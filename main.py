"""
故事织机插件 - 世界观管理与关系图谱
AstrBot 插件，通过 Plugin Page 提供 WebUI，网状关系展示
"""
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.api import llm_tool, logger
from astrbot.api.web import request as web_req

from .storage import StoryLoomStorage

PLUGIN_NAME = "story_loom"
API_PREFIX = f"/{PLUGIN_NAME}/api"

# 集合名 -> storage 方法后缀映射
_COLL_MAP = {
    "characters": "character",
    "locations": "location",
    "items": "item",
    "factions": "faction",
    "timeline": "event",
    "settings": "setting",
    "inspirations": "inspiration",
}

@register("story_loom", "灵笔司书", "故事织机 - 世界观管理与关系图谱", "1.1.0")
class StoryLoomPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.storage = StoryLoomStorage()
        self._register_api()

    def _register_api(self):
        """注册 REST API"""
        for coll in _COLL_MAP:
            # GET 列表 + 单个
            self.context.register_web_api(f"{API_PREFIX}/{coll}", self._mk_list(coll), ["GET"], f"列表{coll}")
            self.context.register_web_api(f"{API_PREFIX}/{coll}/{{item_id}}", self._mk_get(coll), ["GET"], f"详情{coll}")

        # POST 统一入口：增/删/改
        self.context.register_web_api(f"{API_PREFIX}/save", self._handle_save, ["POST"], "新增/更新元素")
        self.context.register_web_api(f"{API_PREFIX}/delete", self._handle_delete, ["POST"], "删除元素")
        self.context.register_web_api(f"{API_PREFIX}/graph", self._handle_graph, ["GET"], "获取完整关系图谱")
        self.context.register_web_api(f"{API_PREFIX}/search", self._handle_search, ["GET"], "搜索元素")

        logger.info("故事织机 API 注册完成")

    def _mk_list(self, coll: str):
        async def handler(**kw):
            return {"ok": True, "data": self.storage._list_all(_COLL_MAP[coll])}
        return handler

    def _mk_get(self, coll: str):
        async def handler(item_id: str, **kw):
            item = self.storage._get_one(_COLL_MAP[coll], item_id)
            if item:
                return {"ok": True, "data": item}
            return {"ok": False, "error": "Not found"}
        return handler

    async def _handle_save(self, **kw):
        body = await web_req.json()
        coll = body.get("_collection", "")
        iid = body.get("_id")
        data = {k: v for k, v in body.items() if not k.startswith("_")}
        suffix = _COLL_MAP.get(coll)
        if not suffix:
            return {"ok": False, "error": f"Unknown collection: {coll}"}
        save_method = getattr(self.storage, f"save_{suffix}")
        new_id = save_method(data, iid)
        return {"ok": True, "id": new_id}

    async def _handle_delete(self, **kw):
        body = await web_req.json()
        coll = body.get("_collection", "")
        iid = body.get("_id", "")
        suffix = _COLL_MAP.get(coll)
        if not suffix:
            return {"ok": False, "error": f"Unknown collection: {coll}"}
        delete_method = getattr(self.storage, f"delete_{suffix}")
        success = delete_method(iid)
        return {"ok": True} if success else {"ok": False, "error": "Not found"}

    async def _handle_graph(self, **kw):
        """获取完整关系图谱数据"""
        return {"ok": True, "data": self.storage.get_graph()}

    async def _handle_search(self, **kw):
        q = web_req.query.get("q", "")
        if not q:
            return {"ok": False, "error": "Missing search query q"}
        return {"ok": True, "data": self.storage.search(q)}

    # ===== QQ 命令 =====
    @filter.command("织机")
    async def cmd_loom(self, event: AstrMessageEvent):
        yield event.plain_result(
            "🧵 故事织机已就绪！\n\n"
            "📱 在 AstrBot 前端进入「插件页面」即可打开 WebUI，支持：\n"
            "  • 🕸️ 关系图谱可视化展示\n"
            "  • 🎭 角色/地点/物品/势力/事件/设定/灵感全管理\n"
            "  • LLM 工具自动记录灵感\n\n"
            "💬 命令：\n"
            "  /灵感 <内容>   - 快速记录灵感\n"
            "  /角色 <名称>   - 创建角色\n"
            "  /设定 <标题>   - 创建设定\n"
            "  /搜索 <关键词>  - 搜索\n"
            "  /世界观        - 概况"
        )

    @filter.command("世界观")
    async def cmd_world(self, event: AstrMessageEvent):
        yield event.plain_result(
            f"🌍 世界观概况\n\n"
            f"🎭 角色：{len(self.storage.list_characters())} 人\n"
            f"📍 地点：{len(self.storage.list_locations())} 处\n"
            f"⚔️ 物品：{len(self.storage.list_items())} 件\n"
            f"🏰 势力：{len(self.storage.list_factions())} 个\n"
            f"📅 事件：{len(self.storage.list_timeline())} 个\n"
            f"📖 设定：{len(self.storage.list_settings())} 条\n"
            f"💡 灵感：{len(self.storage.list_inspirations())} 条"
        )

    @filter.command("灵感")
    async def cmd_inspiration(self, event: AstrMessageEvent, content: str = None):
        if not content:
            items = self.storage.list_inspirations()
            if not items:
                yield event.plain_result("📭 暂无灵感。发送 /灵感 你的灵感内容 来记录")
                return
            result = "💡 最近的灵感：\n\n"
            sorted_items = sorted(items.items(), key=lambda x: x[1].get("created_at",""), reverse=True)
            for iid, insp in sorted_items[:10]:
                title = insp.get("title","未命名")
                preview = insp.get("content","")[:60]
                result += f"▪ {title}{' - ' + preview if preview else ''}\n"
            yield event.plain_result(result)
        else:
            iid = self.storage.save_inspiration({"title": content[:40], "content": content, "source": "QQ消息"})
            yield event.plain_result(f"💡 灵感已记录！ID: {iid}")

    @filter.command("角色")
    async def cmd_character(self, event: AstrMessageEvent, name: str = None):
        if not name:
            yield event.plain_result(self._format_list("角色", self.storage.list_characters(), ["name", "personality"]))
        else:
            cid = self.storage.save_character({"name": name})
            yield event.plain_result(f"🎭 角色「{name}」已创建！ID: {cid}")

    @filter.command("设定")
    async def cmd_setting(self, event: AstrMessageEvent, title: str = None):
        if not title:
            yield event.plain_result(self._format_list("设定", self.storage.list_settings(), ["title", "category"]))
        else:
            sid = self.storage.save_setting({"title": title})
            yield event.plain_result(f"📖 设定「{title}」已创建！ID: {sid}")

    @filter.command("搜索")
    async def cmd_search(self, event: AstrMessageEvent, keyword: str = None):
        if not keyword:
            yield event.plain_result("请提供搜索关键词，例如：/搜索 魔法")
            return
        results = self.storage.search(keyword)
        if not results:
            yield event.plain_result(f"🔍 未找到包含「{keyword}」的内容")
            return
        name_map = {
            "characters": "🎭 角色", "locations": "📍 地点", "items": "⚔️ 物品",
            "factions": "🏰 势力", "timeline": "📅 事件", "settings": "📖 设定", "inspirations": "💡 灵感"
        }
        result = f"🔍 搜索「{keyword}」结果：\n\n"
        for coll, items in results.items():
            display_name = name_map.get(coll, coll)
            result += f"{display_name}（{len(items)} 条）：\n"
            for iid, item in items.items():
                title = item.get("name") or item.get("title") or "未命名"
                result += f"  ▪ {title}\n"
            result += "\n"
        yield event.plain_result(result)

    def _format_list(self, title: str, items: dict, fields: list) -> str:
        if not items:
            return f"📭 {title}列表为空"
        result = f"📋 {title}列表（共 {len(items)} 条）：\n\n"
        for iid, item in items.items():
            name = item.get(fields[0], "未命名")
            result += f"▪ {name} (ID: {iid})\n"
            for field in fields[1:]:
                val = item.get(field, "")
                if val:
                    result += f"  {field}: {val[:50]}{'...' if len(val) > 50 else ''}\n"
            result += "\n"
        return result.strip()

    # ===== LLM 工具 =====
    @llm_tool("记录灵感到故事织机")
    def add_inspiration(self, title: str, content: str, tags: str = ""):
        """记录一个创作灵感或点子"""
        iid = self.storage.save_inspiration({"title": title, "content": content, "tags": tags, "source": "LLM对话"})
        return f"灵感已记录，ID: {iid}"

    @llm_tool("查询世界观设定")
    def query_setting(self, keyword: str):
        """查询世界观中的角色/地点/物品等设定"""
        results = self.storage.search(keyword)
        return results if results else f"未找到与「{keyword}」相关的设定"

    @llm_tool("创建角色")
    def create_character(self, name: str, personality: str = "", background: str = ""):
        """在世界观中创建一个新角色"""
        cid = self.storage.save_character({"name": name, "personality": personality, "background": background})
        return f"角色「{name}」已创建，ID: {cid}"

    @llm_tool("创建设定条目")
    def create_setting(self, title: str, content: str, category: str = ""):
        """创建一个世界观设定条目，如魔法体系、等级制度等"""
        sid = self.storage.save_setting({"title": title, "content": content, "category": category})
        return f"设定「{title}」已创建，ID: {sid}"
