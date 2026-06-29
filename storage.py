"""
存储层 - 使用 JSON 文件存储所有世界观和灵感数据
数据文件位置: data/plugin_data/astrbot_plugin_story_loom/story_loom_data.json
"""
import json
import os
import uuid
from typing import Optional

from .models import (
    Character, Location, Item, Faction, TimelineEvent,
    SettingEntry, Inspiration, now_iso, model_to_dict, dict_to_model
)


class StoryLoomStorage:
    """故事织机数据存储类"""

    def __init__(self, data_dir: str = None):
        """
        初始化存储
        :param data_dir: 数据存储目录，默认 AstrBot 插件数据目录
        """
        if data_dir is None:
            # 默认路径：AstrBot 插件数据目录
            base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "data", "plugin_data", "astrbot_plugin_story_loom")
            data_dir = base
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "story_loom_data.json")
        self._ensure_dir_exists()
        self._init_data_file()

    def _ensure_dir_exists(self):
        """确保数据目录存在"""
        os.makedirs(self.data_dir, exist_ok=True)

    def _init_data_file(self):
        """如果数据文件不存在，创建空数据文件"""
        if not os.path.exists(self.data_file):
            self._save_raw({
                "characters": {},
                "locations": {},
                "items": {},
                "factions": {},
                "timeline": {},
                "settings": {},
                "inspirations": {}
            })

    def _load_raw(self) -> dict:
        """加载原始 JSON 数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_raw(self, data: dict):
        """保存原始 JSON 数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ==================== 通用 CRUD ====================

    def _list_all(self, collection_key: str) -> dict:
        """获取指定集合的所有条目"""
        data = self._load_raw()
        return data.get(collection_key, {})

    def _get_one(self, collection_key: str, item_id: str) -> Optional[dict]:
        """获取指定集合中的单个条目"""
        data = self._load_raw()
        return data.get(collection_key, {}).get(item_id)

    def _save_one(self, collection_key: str, item_id: str, item_dict: dict):
        """保存单个条目到指定集合"""
        data = self._load_raw()
        if collection_key not in data:
            data[collection_key] = {}
        data[collection_key][item_id] = item_dict
        self._save_raw(data)

    def _delete_one(self, collection_key: str, item_id: str) -> bool:
        """从指定集合删除单个条目"""
        data = self._load_raw()
        if collection_key in data and item_id in data[collection_key]:
            del data[collection_key][item_id]
            self._save_raw(data)
            return True
        return False

    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return uuid.uuid4().hex[:12]

    # ==================== 角色管理 ====================

    def list_characters(self) -> dict:
        """获取所有角色"""
        return self._list_all("characters")

    def get_character(self, char_id: str) -> Optional[dict]:
        """获取单个角色"""
        return self._get_one("characters", char_id)

    def save_character(self, data: dict, char_id: str = None) -> str:
        """保存角色，返回 ID"""
        if char_id is None:
            char_id = self._generate_id()
            data["id"] = char_id
            data["created_at"] = now_iso()
        data["updated_at"] = now_iso()
        self._save_one("characters", char_id, data)
        return char_id

    def delete_character(self, char_id: str) -> bool:
        """删除角色"""
        return self._delete_one("characters", char_id)

    # ==================== 地点管理 ====================

    def list_locations(self) -> dict:
        return self._list_all("locations")

    def get_location(self, loc_id: str) -> Optional[dict]:
        return self._get_one("locations", loc_id)

    def save_location(self, data: dict, loc_id: str = None) -> str:
        if loc_id is None:
            loc_id = self._generate_id()
            data["id"] = loc_id
            data["created_at"] = now_iso()
        data["updated_at"] = now_iso()
        self._save_one("locations", loc_id, data)
        return loc_id

    def delete_location(self, loc_id: str) -> bool:
        return self._delete_one("locations", loc_id)

    # ==================== 物品管理 ====================

    def list_items(self) -> dict:
        return self._list_all("items")

    def get_item(self, item_id: str) -> Optional[dict]:
        return self._get_one("items", item_id)

    def save_item(self, data: dict, item_id: str = None) -> str:
        if item_id is None:
            item_id = self._generate_id()
            data["id"] = item_id
            data["created_at"] = now_iso()
        data["updated_at"] = now_iso()
        self._save_one("items", item_id, data)
        return item_id

    def delete_item(self, item_id: str) -> bool:
        return self._delete_one("items", item_id)

    # ==================== 势力管理 ====================

    def list_factions(self) -> dict:
        return self._list_all("factions")

    def get_faction(self, faction_id: str) -> Optional[dict]:
        return self._get_one("factions", faction_id)

    def save_faction(self, data: dict, faction_id: str = None) -> str:
        if faction_id is None:
            faction_id = self._generate_id()
            data["id"] = faction_id
            data["created_at"] = now_iso()
        data["updated_at"] = now_iso()
        self._save_one("factions", faction_id, data)
        return faction_id

    def delete_faction(self, faction_id: str) -> bool:
        return self._delete_one("factions", faction_id)

    # ==================== 时间线管理 ====================

    def list_timeline(self) -> dict:
        return self._list_all("timeline")

    def get_timeline_event(self, event_id: str) -> Optional[dict]:
        return self._get_one("timeline", event_id)

    def save_timeline_event(self, data: dict, event_id: str = None) -> str:
        if event_id is None:
            event_id = self._generate_id()
            data["id"] = event_id
            data["created_at"] = now_iso()
        data["updated_at"] = now_iso()
        self._save_one("timeline", event_id, data)
        return event_id

    def delete_timeline_event(self, event_id: str) -> bool:
        return self._delete_one("timeline", event_id)

    # ==================== 设定管理 ====================

    def list_settings(self) -> dict:
        return self._list_all("settings")

    def get_setting(self, setting_id: str) -> Optional[dict]:
        return self._get_one("settings", setting_id)

    def save_setting(self, data: dict, setting_id: str = None) -> str:
        if setting_id is None:
            setting_id = self._generate_id()
            data["id"] = setting_id
            data["created_at"] = now_iso()
        data["updated_at"] = now_iso()
        self._save_one("settings", setting_id, data)
        return setting_id

    def delete_setting(self, setting_id: str) -> bool:
        return self._delete_one("settings", setting_id)

    # ==================== 灵感管理 ====================

    def list_inspirations(self) -> dict:
        return self._list_all("inspirations")

    def get_inspiration(self, insp_id: str) -> Optional[dict]:
        return self._get_one("inspirations", insp_id)

    def save_inspiration(self, data: dict, insp_id: str = None) -> str:
        if insp_id is None:
            insp_id = self._generate_id()
            data["id"] = insp_id
            data["created_at"] = now_iso()
        data["updated_at"] = now_iso()
        self._save_one("inspirations", insp_id, data)
        return insp_id

    def delete_inspiration(self, insp_id: str) -> bool:
        return self._delete_one("inspirations", insp_id)

    # ==================== 搜索 ====================

    def search(self, keyword: str) -> dict:
        """
        在所有集合中搜索关键词
        返回按集合分组的搜索结果
        """
        keyword = keyword.lower()
        results = {}

        collections = {
            "characters": ["name", "aliases", "personality", "background"],
            "locations": ["name", "description", "type"],
            "items": ["name", "description", "type", "lore"],
            "factions": ["name", "description", "goals"],
            "timeline": ["name", "description", "time_point"],
            "settings": ["title", "content", "category"],
            "inspirations": ["title", "content", "tags"],
        }

        for coll_name, fields in collections.items():
            items = self._list_all(coll_name)
            matched = {}
            for item_id, item in items.items():
                for field in fields:
                    if keyword in str(item.get(field, "")).lower():
                        matched[item_id] = item
                        break
            if matched:
                results[coll_name] = matched

        return results
