"""
数据模型定义 - 世界观管理与灵感收集
每个模型对应一个 JSON 字典条目，用 UUID 作为唯一标识
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
import json


def _serialize(obj):
    """将 dataclass 序列化为 JSON 兼容字典"""
    d = asdict(obj)
    # 将 datetime 转为字符串
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


@dataclass
class Character:
    """角色模型"""
    id: str = ""
    name: str = ""
    aliases: str = ""           # 别称，逗号分隔
    age: str = ""               # 年龄（字符串，支持"未知"）
    gender: str = ""            # 性别
    personality: str = ""       # 性格描述
    appearance: str = ""        # 外貌描述
    background: str = ""        # 背景故事
    goal: str = ""              # 目标/动机
    abilities: str = ""         # 能力/特长
    relationships: str = ""     # 关系网，格式：角色ID:关系描述;角色ID:关系描述
    tags: str = ""              # 标签，逗号分隔
    created_at: str = ""        # 创建时间 ISO 字符串
    updated_at: str = ""        # 更新时间 ISO 字符串


@dataclass
class Location:
    """地点模型"""
    id: str = ""
    name: str = ""
    description: str = ""
    type: str = ""              # 类型：城市/建筑/自然/秘境等
    faction: str = ""           # 所属势力
    features: str = ""          # 特色/重要地点
    tags: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Item:
    """物品/道具模型"""
    id: str = ""
    name: str = ""
    description: str = ""
    type: str = ""              # 类型：武器/法宝/书籍/药草等
    holder: str = ""            # 持有者（角色ID）
    location: str = ""          # 所在地（地点ID）
    lore: str = ""              # 背景传说
    tags: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Faction:
    """势力/组织模型"""
    id: str = ""
    name: str = ""
    description: str = ""
    leader: str = ""            # 首领（角色ID）
    members: str = ""           # 成员列表，角色ID逗号分隔
    base: str = ""              # 根据地（地点ID）
    goals: str = ""             # 目标/宗旨
    tags: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class TimelineEvent:
    """事件/时间线模型"""
    id: str = ""
    name: str = ""
    time_point: str = ""        # 时间点，如"创世历103年"
    description: str = ""
    characters: str = ""        # 涉及角色，角色ID逗号分隔
    locations: str = ""         # 涉及地点，地点ID逗号分隔
    items: str = ""             # 涉及物品，物品ID逗号分隔
    importance: str = "普通"    # 重要程度：关键/重要/普通/琐碎
    tags: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class SettingEntry:
    """设定条目模型 - 自由格式的设定说明"""
    id: str = ""
    title: str = ""
    content: str = ""
    category: str = ""          # 分类：魔法体系/等级制度/种族/文化/历史等
    tags: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Inspiration:
    """灵感模型"""
    id: str = ""
    title: str = ""
    content: str = ""
    tags: str = ""              # 标签，逗号分隔
    source: str = ""            # 来源：梦境/阅读/观察/对话/其他
    related_settings: str = ""  # 关联设定ID，逗号分隔
    created_at: str = ""
    updated_at: str = ""


def now_iso() -> str:
    """返回当前时间的 ISO 格式字符串"""
    return datetime.now().isoformat()


def model_to_dict(model) -> dict:
    """将 dataclass 转为字典"""
    return _serialize(model)


def dict_to_model(data: dict, model_class):
    """将字典转为 dataclass"""
    return model_class(**{k: v for k, v in data.items() if k in model_class.__dataclass_fields__})
