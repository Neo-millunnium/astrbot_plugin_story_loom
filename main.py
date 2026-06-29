"""
故事织机插件主入口
AstrBot 插件 - 世界观管理与灵感收集工具

架构：
1. Plugin Page 机制提供 WebUI 前端（pages/loom/）
2. register_web_api 注册 RESTful API（/story_loom/api/...）
3. AstrBot 命令提供 QQ 交互
4. LLM 工具自动记录灵感和查询设定
5. JSON 文件持久化存储
"""
import json
import os
from typing import Optional

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.api import llm_tool
from astrbot.api import logger

from .storage import StoryLoomStorage

PLUGIN_NAME = "story_loom"


@register("story_loom", "灵笔司书", "故事织机 - 世界观管理与灵感收集工具", "1.0.0")
class StoryLoomPlugin(Star):
    """故事织机插件主类"""

    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.storage = StoryLoomStorage()
        self._register_api()

    def _register_api(self):
        """注册 RESTful API 到 AstrBot 前端"""
        prefix = f"/{PLUGIN_NAME}/api"

        # 每个集合的 CRUD
        collections = [
            ("characters", "角色"),
            ("locations", "地点"),
            ("items", "物品"),
            ("factions", "势力"),
            ("timeline", "事件"),
            ("settings", "设定"),
            ("inspirations", "灵感"),
        ]

        for coll_name, coll_label in collections:
            # GET /api/{collection} - 列表
            self.context.register_web_api(
                f"{prefix}/{coll_name}",
                self._make_list_handler(coll_name),
                ["GET"],
                f"获取{coll_label}列表",
            )
            # GET /api/{collection}/{id} - 单个
            self.context.register_web_api(
                f"{prefix}/{coll_name}/{{item_id}}",
                self._make_get_handler(coll_name),
                ["GET"],
                f"获取单个{coll_label}",
            )
            # POST /api/{collection} - 新增
            self.context.register_web_api(
                f"{prefix}/{coll_name}",
                self._make_create_handler(coll_name),
                ["POST"],
                f"新增{coll_label}",
            )
            # PUT /api/{collection}/{id} - 更新
            self.context.register_web_api(
                f"{prefix}/{coll_name}/{{item_id}}",
                self._make_update_handler(coll_name),
                ["PUT"],
                f"更新{coll_label}",
            )
            # DELETE /api/{collection}/{id} - 删除
            self.context.register_web_api(
                f"{prefix}/{coll_name}/{{item_id}}",
                self._make_delete_handler(coll_name),
                ["DELETE"],
                f"删除{coll_label}",
            )

        # 搜索 API
        self.context.register_web_api(
            f"{prefix}/search",
            self._handle_search,
            ["GET"],
            "搜索所有内容",
        )

        logger.info(f"故事织机 API 已注册，共 {len(collections) * 5 + 1} 个端点")

    # ==================== API 处理器工厂 ====================

    def _make_list_handler(self, collection: str):
        async def handler(request=None, **kwargs):
            items = self.storage._list_all(collection)
            return {"ok": True, "data": items}
        return handler

    def _make_get_handler(self, collection: str):
        async def handler(item_id: str, request=None, **kwargs):
            item = self.storage._get_one(collection, item_id)
            if item:
                return {"ok": True, "data": item}
            return {"ok": False, "error": "Not found"}, 404
        return handler

    def _make_create_handler(self, collection: str):
        async def handler(request=None, **kwargs):
            body = await request.json() if request else {}
            save_method = getattr(self.storage, f"save_{collection.rstrip('s')}")
            new_id = save_method(body)
            return {"ok": True, "id": new_id}
        return handler

    def _make_update_handler(self, collection: str):
        async def handler(item_id: str, request=None, **kwargs):
            body = await request.json() if request else {}
            save_method = getattr(self.storage, f"save_{collection.rstrip('s')}")
            save_method(body, item_id)
            return {"ok": True, "id": item_id}
        return handler

    def _make_delete_handler(self, collection: str):
        async def handler(item_id: str, request=None, **kwargs):
            delete_method = getattr(self.storage, f"delete_{collection.rstrip('s')}")
            success = delete_method(item_id)
            if success:
                return {"ok": True}
            return {"ok": False, "error": "Not found"}, 404
        return handler

    async def _handle_search(self, request=None, **kwargs):
        """搜索处理器"""
        q = request.query_params.get("q", "") if request else ""
        if not q:
            return {"ok": False, "error": "请提供搜索关键词 q"}, 400
        results = self.storage.search(q)
        return {"ok": True, "data": results}

    # ==================== 命令处理 ====================

    @filter.command("织机")
    async def cmd_loom(self, event: AstrMessageEvent):
        """打开故事织机"""
        yield event.plain_result(
            "🧵 故事织机已就绪！\n\n"
            "📱 在 AstrBot 前端中，进入「插件页面」即可看到故事织机。\n\n"
            "💬 也可通过以下命令操作：\n"
            "  /灵感 <内容>   - 快速记录灵感\n"
            "  /角色 <名称>   - 快速创建角色\n"
            "  /设定 <标题>   - 快速创建设定\n"
            "  /搜索 <关键词>  - 搜索所有内容\n"
            "  /世界观        - 查看世界观概况"
        )

    @filter.command("世界观")
    async def cmd_world(self, event: AstrMessageEvent):
        """世界观概况"""
        chars = self.storage.list_characters()
        locs = self.storage.list_locations()
        items = self.storage.list_items()
        factions = self.storage.list_factions()
        timeline = self.storage.list_timeline()
        settings = self.storage.list_settings()
        inss = self.storage.list_inspirations()

        yield event.plain_result(
            f"🌍 世界观概况\n\n"
            f"🎭 角色：{len(chars)} 人\n"
            f"📍 地点：{len(locs)} 处\n"
            f"⚔️ 物品：{len(items)} 件\n"
            f"🏰 势力：{len(factions)} 个\n"
            f"📅 事件：{len(timeline)} 个\n"
            f"📖 设定：{len(settings)} 条\n"
            f"💡 灵感：{len(inss)} 条\n\n"
            f"使用 WebUI 进行完整管理：在 AstrBot 前端进入「插件页面」"
        )

    @filter.command("灵感")
    async def cmd_inspiration(self, event: AstrMessageEvent, content: str = None):
        """记录或查看灵感"""
        if not content:
            inspirations = self.storage.list_inspirations()
            if not inspirations:
                yield event.plain_result("📭 暂无灵感。发送 /灵感 你的灵感内容 来记录")
                return
            result = "💡 最近的灵感：\n\n"
            for iid, insp in sorted(inspirations.items(),
                                    key=lambda x: x[1].get("created_at", ""),
                                    reverse=True)[:10]:
                title = insp.get("title", "未命名")
                preview = insp.get("content", "")[:60]
                result += f"▪ {title}"
                if preview:
                    result += f" - {preview}"
                result += "\n"
            yield event.plain_result(result)
        else:
            insp_id = self.storage.save_inspiration({
                "title": content[:40],
                "content": content,
                "tags": "",
                "source": "QQ消息",
                "related_settings": ""
            })
            yield event.plain_result(f"💡 灵感已记录！ID: {insp_id}")

    @filter.command("角色")
    async def cmd_character(self, event: AstrMessageEvent, name: str = None):
        """角色管理"""
        if not name:
            chars = self.storage.list_characters()
            yield event.plain_result(self._format_list("角色", chars, ["name", "personality", "background"]))
        else:
            char_id = self.storage.save_character({"name": name})
            yield event.plain_result(f"🎭 角色「{name}」已创建！ID: {char_id}")

    @filter.command("设定")
    async def cmd_setting(self, event: AstrMessageEvent, title: str = None):
        """设定管理"""
        if not title:
            settings = self.storage.list_settings()
            yield event.plain_result(self._format_list("设定", settings, ["title", "category", "content"]))
        else:
            setting_id = self.storage.save_setting({"title": title})
            yield event.plain_result(f"📖 设定「{title}」已创建！ID: {setting_id}")

    @filter.command("搜索")
    async def cmd_search(self, event: AstrMessageEvent, keyword: str = None):
        """搜索所有内容"""
        if not keyword:
            yield event.plain_result("请提供搜索关键词，例如：/搜索 魔法")
            return

        results = self.storage.search(keyword)
        if not results:
            yield event.plain_result(f"🔍 未找到包含「{keyword}」的内容")
            return

        result = f"🔍 搜索「{keyword}」结果：\n\n"
        name_map = {
            "characters": "角色", "locations": "地点", "items": "物品",
            "factions": "势力", "timeline": "事件", "settings": "设定", "inspirations": "灵感"
        }
        for coll_name, items in results.items():
            display_name = name_map.get(coll_name, coll_name)
            result += f"📂 {display_name}（{len(items)} 条）：\n"
            for iid, item in items.items():
                title = item.get("name") or item.get("title") or "未命名"
                result += f"  ▪ {title}\n"
            result += "\n"

        yield event.plain_result(result)

    def _format_list(self, title: str, items: dict, fields: list) -> str:
        """格式化列表输出"""
        if not items:
            return f"📭 {title}列表为空"
        result = f"📋 {title}列表（共 {len(items)} 条）：\n\n"
        for item_id, item in items.items():
            name = item.get(fields[0], "未命名")
            result += f"▪ {name} (ID: {item_id})\n"
            for field in fields[1:]:
                val = item.get(field, "")
                if val:
                    if len(val) > 50:
                        val = val[:50] + "..."
                    result += f"  {field}: {val}\n"
            result += "\n"
        return result.strip()

    # ==================== LLM 工具 ====================

    @llm_tool("记录一个灵感到故事织机")
    def add_inspiration(self, title: str, content: str, tags: str = ""):
        """记录一个创作灵感。当用户说'我突然想到一个点子'等时调用"""
        insp_id = self.storage.save_inspiration({
            "title": title,
            "content": content,
            "tags": tags,
            "source": "LLM对话"
        })
        return f"灵感已记录，ID: {insp_id}"

    @llm_tool("查询世界观设定")
    def query_setting(self, keyword: str):
        """查询世界观中的角色、地点、物品等信息。当用户问'主角是谁'等时调用"""
        results = self.storage.search(keyword)
        if not results:
            return f"未找到与「{keyword}」相关的设定"
        return json.dumps(results, ensure_ascii=False, indent=2)

    @llm_tool("创建角色")
    def create_character(self, name: str, personality: str = "", background: str = ""):
        """创建一个新的角色设定"""
        char_id = self.storage.save_character({
            "name": name,
            "personality": personality,
            "background": background
        })
        return f"角色「{name}」已创建，ID: {char_id}"

    @llm_tool("创建设定条目")
    def create_setting(self, title: str, content: str, category: str = ""):
        """创建一个世界观设定条目，如魔法体系、等级制度等"""
        setting_id = self.storage.save_setting({
            "title": title,
            "content": content,
            "category": category
        })
        return f"设定「{title}」已创建，ID: {setting_id}"
