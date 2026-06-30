# 故事织机 — AI 开发维护指南

> 本文档供 AI 快速理解插件架构和修改要点。人类也可阅读。

## 1. 文件结构

```
astrbot_plugin_story_loom/
├── __init__.py          # 空文件
├── metadata.yaml        # 插件元信息（注册名/版本/描述）
├── main.py              # 插件入口：命令注册、API路由、LLM工具
├── storage.py            # 数据持久化层（nodes.json + edges.json）
├── models.py            # （无用，已废弃）
├── requirements.txt     # （无用，无外部依赖）
├── README.md            # （已过时，非权威）
├── DEV_GUIDE.md         # ← 本文档
└── pages/loom/
    ├── index.html       # Plugin Page 入口（AstrBot 自动注入 asset_token）
    ├── style.css        # 深色主题样式
    ├── app.js           # 全部前端逻辑（单文件）
    └── vis-network.min.js  # vis.js 关系图谱库
```

## 2. 架构总览

```
QQ 命令 ──→ main.py ──→ storage.py ──→ nodes.json / edges.json
LLM 工具 ──→              （AstrBot 数据目录）
                              ↑
WebUI ←── main.py (REST API) ─┘
（Plugin Page 内嵌 iframe）
```

**关键认知**：没有独立的 `webui.py`。HTTP API 路由 **全部注册在 `main.py` 的 `_register_api()`** 中，用 `self.context.register_web_api()` 挂载到 AstrBot 内部 web 框架。

## 3. 数据模型（统一 Node/Edge）

### 存储文件
| 文件 | 内容 |
|------|------|
| `/root/AstrBot/data/story_loom/nodes.json` | 所有实体，一个 JSON 对象，key=8位uuid |
| `/root/AstrBot/data/story_loom/edges.json` | 节点间关系（暂未自动生成） |

### Node 结构
```json
{
  "id": "a1b2c3d4",
  "type": "character",     // character/location/item/faction/event/setting/inspiration
  "name": "张三",
  "data": {                // 自由字典，字段因 type 而异
    "name": "张三",
    "personality": "冷漠",
    "tags": "主角,剑客"
  },
  "created_at": "2026-06-30T08:00:00",
  "updated_at": "2026-06-30T08:30:00"
}
```

**注意**：`data` 字典内字段完全由前端表单决定（见 `app.js` 的 `FIELDS` 配置），后端不做校验。`name` 字段同时作为 Node 的 `name` 属性（展示用）和 `data.name`（可编辑）。

### 集合命名约定（极易出错！）

| 前端 `collection` | 后端 type | 存储方法后缀 | 注意 |
|---|---|---|---|
| `characters` | `character` | `save_character` | 前端复数，后端单数 |
| `locations` | `location` | `save_location` | |
| `items` | `item` | `save_item` | |
| `factions` | `faction` | `save_faction` | |
| `timeline` | `event` | `save_timeline_event` | ⚠ 前端 `timeline`，后端 type 是 `event` |
| `settings` | `setting` | `save_setting` | |
| `inspirations` | `inspiration` | `save_inspiration` | |

映射关系定义在 `main.py` 的 `_COLL_MAP` 字典中。

## 4. API 路由一览

基础路径：`/api/plugin/story_loom/api`（⚠ 容易写错成 `/api/plug/...`）

| 方法 | 路径 | 说明 | 返回格式 |
|------|------|------|----------|
| GET | `/{collection}` | 列出某类型所有元素 | `{ok, data: {id: item}}` |
| GET | `/{collection}/{id}` | 获取单个元素详情 | `{ok, data: item}` 或 `{ok:false, error}` |
| POST | `/save` | 新增/更新 | body: `{_collection, _id?, ...fields}` → `{ok, id}` |
| POST | `/delete` | 删除 | body: `{_collection, _id}` → `{ok}` |
| GET | `/graph` | 获取完整图谱 | `{ok, data: {nodes, edges}}` |
| GET | `/search?q=keyword` | 全局搜索 | `{ok, data: {collection: {id: item}}}` |

**save/delete 的 body 约定**：`_collection` 和 `_id` 是元字段前缀 `_`，其余键值直接作为 data 字段。

## 5. 前端 app.js 核心结构

### 页面状态
- `currentPage` — 当前页面标识 (`dashboard` | `graph` | `characters` | ...)
- `editingItem` — 当前编辑上下文 `{collection, id?, type}`
- `network` — vis.js Network 实例

### 页面渲染链路
```
DOMContentLoaded
  → 绑定侧边栏 click 事件
  → navigateTo('dashboard')
      → renderDashboard()      # 遍历所有 type，调 apiGet 拿计数
      → renderGraph()          # loadVisNetwork() 动态加载 vis.js
      → renderListPage()       # 通用列表页，卡片展示
          → openEditor()       # 弹窗编辑
              → renderForm()   # 根据 FIELDS[type] 动态生成表单
              → saveModal()    # apiPost /save
```

### 关键函数清单
| 函数 | 触发 | 作用 |
|------|------|------|
| `navigateTo(page)` | 侧边栏点击 | 路由到对应页面 |
| `renderDashboard(c)` | 总览 | 统计卡片 + 最近灵感 |
| `renderListPage(c, coll)` | 各分类 | 卡片列表 |
| `openEditor(coll, id?)` | 点击卡片/新增按钮 | 打开发送弹窗 |
| `renderForm(type, item)` | 编辑器打开时 | 动态生成表单 HTML |
| `saveModal()` | 保存按钮 | 收集表单值 → POST /save |
| `doGlobalSearch()` | 搜索框 | GET /search |
| `renderGraph(c)` | 图谱页 | 动态加载 vis.js，渲染关系网 |

### API 调用约定
```javascript
const API_BASE = "/api/plugin/story_loom/api";

// GET 请求：url 自动拼接 asset_token 参数
apiGet(url) → fetch(url + sep + "asset_token=" + token, {credentials:"include"})

// POST 请求：JSON body，同样拼接 token
apiPost(url, data) → fetch(url + sep + "asset_token=" + token, {method:'POST', body:JSON, credentials:"include"})
```

⚠ **两个 fetch 都带 `credentials: "include"`** — 这是必须的，否则 iframe 请求不带登录 cookie 会 401。

## 6. 常见问题排查

### 页面白屏/点击无反应
1. `node -c pages/loom/app.js` 检查 JS 语法
2. 查看浏览器控制台报错

### 保存失败/API 404
1. 检查 `API_BASE` 拼写（是否少了 `in`，即 `plug` vs `plugin`）
2. 检查 `_COLL_MAP` 映射是否正确
3. 检查存储目录 `/root/AstrBot/data/story_loom/` 是否存在
4. 检查 fetch 是否有 `credentials: "include"`

### 图谱不显示
- `vis-network.min.js` 是否存在于 `pages/loom/` 目录
- 浏览器是否加载了该 JS（检查 Network 面板）

### 数据位置
- 存储：`/root/AstrBot/data/story_loom/nodes.json` + `edges.json`
- 插件自己：`/root/AstrBot/data/plugins/astrbot_plugin_story_loom/`

## 7. 修改指南

### 新增一个数据分类（如“组织”）
1. `storage.py`：添加 `save_organization()` / `delete_organization()` / `list_organizations()`（都是 `save_node("organization", ...)` 的封装）
2. `main.py`：在 `_COLL_MAP` 添加 `"organizations": "organization"`
3. `app.js`：
   - `TYPES` 添加 `organization: {label:'组织', icon:'🏢', color:'#xxx'}`
   - `FIELDS` 添加 `organization: ['name','description','...']`
   - `index.html` 侧边栏添加对应 `<li class="nav-item" data-page="organizations">`

### 新增字段
1. `app.js` 的 `FIELDS[type]` 数组追加字段名
2. `app.js` 的 `LABELS` 追加中文标签
3. 如果字段是下拉选择，在 `TYPES_SELECT` 添加选项数组

### 新增 LLM 工具
在 `main.py` 的 `StoryLoomPlugin` 类中添加 `@llm_tool` 装饰的方法即可，AstrBot 会自动注册。

### 新增 QQ 命令
在 `main.py` 中添加 `@filter.command("命令名")` 装饰的方法。

## 8. Git 操作备忘

```bash
# 路径
cd /root/AstrBot/data/plugins/astrbot_plugin_story_loom

# 提交
git add -A
git commit -m "描述"
git push

# 用户侧拉取
cd /root/AstrBot/data/plugins/astrbot_plugin_story_loom
git pull
# 然后在 AstrBot 面板重载插件
```

## 9. 依赖

- **Python**：纯标准库，无外部依赖
- **前端**：vis-network（CDN 回退到本地 `vis-network.min.js`）
