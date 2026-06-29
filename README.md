# 🧵 故事织机 - AstrBot 世界观管理与灵感收集插件

## 概述

故事织机是一款面向小说创作者的世界观管理与灵感收集工具。它帮助你将零散的灵感碎片编织成结构完整、逻辑自洽的故事世界。

### 核心功能

| 功能 | 说明 |
|------|------|
| 🎭 **角色管理** | 管理角色姓名、别称、性格、外貌、背景、能力、关系网 |
| 📍 **地点管理** | 管理故事中的城市、建筑、秘境等地点设定 |
| ⚔️ **物品管理** | 管理武器、法宝、道具等物品的属性和归属 |
| 🏰 **势力管理** | 管理组织、门派、国家等势力的成员和目标 |
| 📅 **时间线** | 按时间顺序管理故事中的关键事件 |
| 📖 **设定条目** | 自由格式记录魔法体系、等级制度等世界观设定 |
| 💡 **灵感收集** | 随时记录创作灵感，打标签分类，关联世界观设定 |
| 🔍 **全局搜索** | 跨所有分类搜索关键词 |

## 安装

将 `astrbot_plugin_story_loom` 目录放入 AstrBot 的 `data/plugins/` 目录下，重启 AstrBot 即可自动加载。

## 使用方法

### 方式一：QQ 命令

| 命令 | 说明 |
|------|------|
| `/织机` | 打开 WebUI 管理界面 |
| `/灵感 内容` | 快速记录灵感 |
| `/角色 名称` | 快速创建角色 |
| `/设定 标题` | 快速创建设定条目 |
| `/搜索 关键词` | 搜索所有内容 |

### 方式二：WebUI 管理界面

访问 `http://服务器IP:8765` 打开 WebUI。

WebUI 提供完整的可视化管理界面：
- 左侧导航栏切换不同分类
- 卡片式列表展示所有条目
- 点击卡片编辑详情
- 新增/编辑/删除操作
- 全局搜索

### 方式三：LLM 自动调用

插件注册了以下 LLM 工具，AI 在对话中会自动调用：

| 工具 | 触发场景 |
|------|---------|
| `add_inspiration` | 用户说"我突然想到一个点子"时自动记录 |
| `query_setting` | 用户问"主角是谁""XX是什么"时自动查询 |
| `create_character` | 用户说"帮我创建一个角色"时自动创建 |
| `create_setting` | 用户说"添加一个设定"时自动创建 |

## 数据存储

所有数据存储在 `data/plugin_data/astrbot_plugin_story_loom/story_loom_data.json` 文件中。

数据格式为 JSON，包含以下顶层键：
- `characters` - 角色字典
- `locations` - 地点字典
- `items` - 物品字典
- `factions` - 势力字典
- `timeline` - 时间线事件字典
- `settings` - 设定条目字典
- `inspirations` - 灵感字典

每个条目包含 `id`、`created_at`、`updated_at` 等通用字段，以及各类型特有的字段。

## 架构说明

```
astrbot_plugin_story_loom/
├── __init__.py          # 空文件，标识为 Python 包
├── metadata.yaml        # 插件元信息
├── main.py              # 插件主入口，命令和 LLM 工具注册
├── models.py            # 数据模型定义（dataclass）
├── storage.py           # JSON 文件存储层（CRUD 操作）
├── webui.py             # HTTP API 和静态文件服务
├── webui/
│   ├── index.html       # WebUI 主页面
│   ├── style.css        # 深色主题样式
│   └── app.js           # 前端交互逻辑
└── README.md            # 本文档
```

### 各模块职责

| 模块 | 职责 | 修改注意事项 |
|------|------|-------------|
| `models.py` | 定义数据结构 | 如需新增字段，同时更新 `PAGES` 配置和 `FIELD_NAMES` |
| `storage.py` | 数据持久化 | 所有 CRUD 操作通过 `_save_raw`/`_load_raw` 读写 JSON |
| `main.py` | AstrBot 集成 | 命令注册、LLM 工具注册、生命周期管理 |
| `webui.py` | HTTP 服务 | API 路由、静态文件服务、CORS |
| `webui/app.js` | 前端逻辑 | `PAGES` 配置决定页面布局，`FIELD_NAMES` 决定字段中文名 |

### 扩展指南

**新增一个数据分类：**
1. `models.py` 中新增 dataclass
2. `storage.py` 中新增 CRUD 方法
3. `webui.py` 的 `_parse_path` 中的允许集合列表添加新分类
4. `webui/app.js` 的 `PAGES` 中添加新页面配置
5. `main.py` 中添加对应的命令和 LLM 工具

## 配置

插件支持在 `data/config/astrbot_plugin_story_loom_config.json` 中配置：

```json
{
  "webui_port": 8765
}
```

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `webui_port` | 8765 | WebUI 服务端口 |

## 依赖

纯 Python 标准库实现，无需额外依赖。

## 版本历史

### v1.0.0
- 初始版本
- 支持角色、地点、物品、势力、时间线、设定、灵感七类数据管理
- 提供 WebUI 管理界面
- 提供 QQ 命令和 LLM 工具接口
- JSON 文件持久化存储
