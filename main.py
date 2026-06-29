"""
故事织机插件 - 世界观管理与灵感收集工具
"""
import json
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.api import llm_tool, logger
from astrbot.api.web import request as web_req

from .storage import StoryLoomStorage

PLUGIN_NAME = "story_loom"
API = f"/{PLUGIN_NAME}/api"

# 集合名 -> storage 方法后缀映射
_COLL_MAP = {
    "characters": "character",
    "locations": "location",
    "items": "item",
    "factions": "faction",
    "timeline": "timeline_event",
    "settings": "setting",
    "inspirations": "inspiration",
}

@register("story_loom", "灵笔司书", "故事织机 - 世界观管理与灵感收集工具", "1.0.0")
class StoryLoomPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.storage = StoryLoomStorage()
        self._reg_api()

    def _reg_api(self):
        for coll in _COLL_MAP:
            self.context.register_web_api(f"{API}/{coll}", self._mk_list(coll), ["GET"], f"列表{coll}")
            self.context.register_web_api(f"{API}/{coll}/{{item_id}}", self._mk_get(coll), ["GET"], f"详情{coll}")
        self.context.register_web_api(f"{API}/save", self._save, ["POST"], "新增/更新")
        self.context.register_web_api(f"{API}/delete", self._delete, ["POST"], "删除")
        self.context.register_web_api(f"{API}/search", self._search, ["GET"], "搜索")
        logger.info("故事织机 API 注册完成")

    def _mk_list(self, coll):
        async def h(**kw):
            return {"ok": True, "data": self.storage._list_all(coll)}
        return h

    def _mk_get(self, coll):
        async def h(item_id: str, **kw):
            item = self.storage._get_one(coll, item_id)
            return {"ok": True, "data": item} if item else {"ok": False, "error": "Not found"}
        return h

    async def _save(self, **kw):
        body = await web_req.json()
        coll, iid = body.get("_collection",""), body.get("_id")
        data = {k:v for k,v in body.items() if not k.startswith("_")}
        suffix = _COLL_MAP.get(coll)
        if not suffix:
            return {"ok": False, "error": f"Unknown collection: {coll}"}
        m = getattr(self.storage, f"save_{suffix}")
        nid = m(data, iid)
        return {"ok": True, "id": nid}

    async def _delete(self, **kw):
        body = await web_req.json()
        coll, iid = body.get("_collection",""), body.get("_id","")
        suffix = _COLL_MAP.get(coll)
        if not suffix:
            return {"ok": False, "error": f"Unknown collection: {coll}"}
        m = getattr(self.storage, f"delete_{suffix}")
        return {"ok": True} if m(iid) else {"ok": False, "error": "Not found"}

    async def _search(self, **kw):
        q = web_req.query.get("q", "")
        if not q:
            return {"ok": False, "error": "need q"}
        return {"ok": True, "data": self.storage.search(q)}

    # ===== 命令 =====
    @filter.command("织机")
    async def cmd_loom(self, event: AstrMessageEvent):
        yield event.plain_result(
            "🧵 故事织机已就绪！\n\n"
            "📱 在 AstrBot 前端进入「插件页面」即可看到 WebUI。\n\n"
            "💬 命令：\n"
            "  /灵感 <内容>   - 记录灵感\n"
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
                yield event.plain_result("📭 暂无灵感")
                return
            r = "💡 最近的灵感：\n\n"
            for iid, v in sorted(items.items(), key=lambda x: x[1].get("created_at",""), reverse=True)[:10]:
                r += f"▪ {v.get('title','未命名')} - {(v.get('content','')[:60])}\n"
            yield event.plain_result(r)
        else:
            iid = self.storage.save_inspiration({"title":content[:40],"content":content,"source":"QQ消息"})
            yield event.plain_result(f"💡 灵感已记录！ID: {iid}")

    @filter.command("角色")
    async def cmd_character(self, event: AstrMessageEvent, name: str = None):
        if not name:
            yield event.plain_result(self._fmt("角色", self.storage.list_characters(), ["name","personality"]))
        else:
            yield event.plain_result(f"🎭 角色「{name}」已创建！ID: {self.storage.save_character({'name':name})}")

    @filter.command("设定")
    async def cmd_setting(self, event: AstrMessageEvent, title: str = None):
        if not title:
            yield event.plain_result(self._fmt("设定", self.storage.list_settings(), ["title","category"]))
        else:
            yield event.plain_result(f"📖 设定「{title}」已创建！ID: {self.storage.save_setting({'title':title})}")

    @filter.command("搜索")
    async def cmd_search(self, event: AstrMessageEvent, keyword: str = None):
        if not keyword:
            yield event.plain_result("请提供关键词，如 /搜索 魔法")
            return
        r = self.storage.search(keyword)
        if not r:
            yield event.plain_result(f"🔍 未找到「{keyword}」")
            return
        nm = {"characters":"角色","locations":"地点","items":"物品","factions":"势力","timeline":"事件","settings":"设定","inspirations":"灵感"}
        s = f"🔍 搜索「{keyword}」结果：\n\n"
        for c, items in r.items():
            s += f"📂 {nm.get(c,c)}（{len(items)} 条）：\n"
            for _, v in items.items():
                s += f"  ▪ {v.get('name') or v.get('title') or '未命名'}\n"
            s += "\n"
        yield event.plain_result(s)

    def _fmt(self, title, items, fields):
        if not items:
            return f"📭 {title}列表为空"
        r = f"📋 {title}列表（{len(items)} 条）：\n\n"
        for iid, v in items.items():
            r += f"▪ {v.get(fields[0],'未命名')} (ID: {iid})\n"
            for f in fields[1:]:
                val = v.get(f,"")
                if val:
                    r += f"  {f}: {val[:50]}{'...' if len(val)>50 else ''}\n"
            r += "\n"
        return r.strip()

    # ===== LLM 工具 =====
    @llm_tool("记录灵感")
    def add_inspiration(self, title: str, content: str, tags: str = ""):
        return f"灵感已记录，ID: {self.storage.save_inspiration({'title':title,'content':content,'tags':tags,'source':'LLM'})}"

    @llm_tool("查询设定")
    def query_setting(self, keyword: str):
        r = self.storage.search(keyword)
        return json.dumps(r, ensure_ascii=False, indent=2) if r else f"未找到「{keyword}」"

    @llm_tool("创建角色")
    def create_character(self, name: str, personality: str = "", background: str = ""):
        return f"角色「{name}」已创建，ID: {self.storage.save_character({'name':name,'personality':personality,'background':background})}"

    @llm_tool("创建设定")
    def create_setting(self, title: str, content: str, category: str = ""):
        return f"设定「{title}」已创建，ID: {self.storage.save_setting({'title':title,'content':content,'category':category})}"
