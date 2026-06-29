"""
故事织机 - 数据存储与关系图谱
支持网状关系：角色-地点-物品-事件-势力-设定
"""
import json
import os
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

STORAGE_DIR = "/root/AstrBot/data/story_loom"
os.makedirs(STORAGE_DIR, exist_ok=True)

@dataclass
class Node:
    id: str
    type: str  # character, location, item, faction, event, setting, inspiration
    name: str
    data: dict
    created_at: str
    updated_at: str

@dataclass
class Edge:
    id: str
    source: str
    target: str
    type: str  # 关系类型
    weight: float = 1.0
    data: dict = None

class StoryLoomStorage:
    def __init__(self):
        self.nodes_file = os.path.join(STORAGE_DIR, "nodes.json")
        self.edges_file = os.path.join(STORAGE_DIR, "edges.json")
        self._load()

    def _load(self):
        if os.path.exists(self.nodes_file):
            with open(self.nodes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.nodes = {nid: Node(**n) for nid, n in data.items()}
        else:
            self.nodes = {}
        if os.path.exists(self.edges_file):
            with open(self.edges_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.edges = {eid: Edge(**e) for eid, e in data.items()}
        else:
            self.edges = {}
        self._save()

    def _save(self):
        with open(self.nodes_file, 'w', encoding='utf-8') as f:
            json.dump({nid: asdict(n) for nid, n in self.nodes.items()}, f, ensure_ascii=False, indent=2)
        with open(self.edges_file, 'w', encoding='utf-8') as f:
            json.dump({eid: asdict(e) for eid, e in self.edges.items()}, f, ensure_ascii=False, indent=2)

    # ===== 节点 CRUD =====
    def _list_all(self, node_type: str) -> dict:
        return {nid: n.data for nid, n in self.nodes.items() if n.type == node_type}

    def _get_one(self, node_type: str, node_id: str) -> Optional[dict]:
        n = self.nodes.get(node_id)
        if n and n.type == node_type:
            return n.data
        return None

    def save_node(self, node_type: str, data: dict, node_id: str = None) -> str:
        now = datetime.now().isoformat()
        if node_id and node_id in self.nodes:
            # 更新
            n = self.nodes[node_id]
            n.data.update(data)
            n.updated_at = now
        else:
            # 新增
            node_id = node_id or str(uuid.uuid4())[:8]
            self.nodes[node_id] = Node(
                id=node_id,
                type=node_type,
                name=data.get('name') or data.get('title') or '未命名',
                data=data,
                created_at=now,
                updated_at=now
            )
        self._save()
        return node_id

    def delete_node(self, node_id: str) -> bool:
        if node_id not in self.nodes:
            return False
        del self.nodes[node_id]
        # 删除相关边
        self.edges = {eid: e for eid, e in self.edges.items() if e.source != node_id and e.target != node_id}
        self._save()
        return True

    # ===== 边（关系）操作 =====
    def add_edge(self, source: str, target: str, edge_type: str, weight: float = 1.0, data: dict = None) -> str:
        """添加两个节点之间的关系"""
        if source not in self.nodes or target not in self.nodes:
            return ""
        edge_id = f"{source}-{target}-{edge_type}"
        self.edges[edge_id] = Edge(
            id=edge_id,
            source=source,
            target=target,
            type=edge_type,
            weight=weight,
            data=data or {}
        )
        self._save()
        return edge_id

    def remove_edge(self, edge_id: str) -> bool:
        if edge_id not in self.edges:
            return False
        del self.edges[edge_id]
        self._save()
        return True

    def get_edges(self, node_id: str = None) -> dict:
        """获取节点相关的边"""
        if node_id:
            return {eid: asdict(e) for eid, e in self.edges.items() if e.source == node_id or e.target == node_id}
        return {eid: asdict(e) for eid, e in self.edges.items()}

    def get_graph(self, node_types: list[str] = None) -> dict:
        """获取完整图谱数据"""
        nodes = []
        edges = []
        for nid, n in self.nodes.items():
            if node_types and n.type not in node_types:
                continue
            nodes.append({
                "id": nid,
                "label": n.name,
                "type": n.type,
                "data": n.data
            })
        for eid, e in self.edges.items():
            if e.source in self.nodes and e.target in self.nodes:
                edges.append({
                    "id": eid,
                    "from": e.source,
                    "to": e.target,
                    "label": e.type,
                    "value": e.weight,
                    "data": e.data or {}
                })
        return {"nodes": nodes, "edges": edges}

    # ===== 快捷方法 =====
    def save_character(self, data: dict, char_id: str = None) -> str:
        return self.save_node("character", data, char_id)

    def delete_character(self, char_id: str) -> bool:
        return self.delete_node(char_id)

    def save_location(self, data: dict, loc_id: str = None) -> str:
        return self.save_node("location", data, loc_id)

    def delete_location(self, loc_id: str) -> bool:
        return self.delete_node(loc_id)

    def save_item(self, data: dict, item_id: str = None) -> str:
        return self.save_node("item", data, item_id)

    def delete_item(self, item_id: str) -> bool:
        return self.delete_node(item_id)

    def save_faction(self, data: dict, faction_id: str = None) -> str:
        return self.save_node("faction", data, faction_id)

    def delete_faction(self, faction_id: str) -> bool:
        return self.delete_node(faction_id)

    def save_timeline_event(self, data: dict, event_id: str = None) -> str:
        return self.save_node("event", data, event_id)

    def delete_timeline_event(self, event_id: str) -> bool:
        return self.delete_node(event_id)

    def save_setting(self, data: dict, setting_id: str = None) -> str:
        return self.save_node("setting", data, setting_id)

    def delete_setting(self, setting_id: str) -> bool:
        return self.delete_node(setting_id)

    def save_inspiration(self, data: dict, insp_id: str = None) -> str:
        return self.save_node("inspiration", data, insp_id)

    def delete_inspiration(self, insp_id: str) -> bool:
        return self.delete_node(insp_id)

    # ===== 列表方法（兼容旧版） =====
    def list_characters(self) -> dict:
        return self._list_all("character")

    def list_locations(self) -> dict:
        return self._list_all("location")

    def list_items(self) -> dict:
        return self._list_all("item")

    def list_factions(self) -> dict:
        return self._list_all("faction")

    def list_timeline(self) -> dict:
        return self._list_all("event")

    def list_settings(self) -> dict:
        return self._list_all("setting")

    def list_inspirations(self) -> dict:
        return self._list_all("inspiration")

    # ===== 搜索 =====
    def search(self, keyword: str) -> dict:
        results = defaultdict(dict)
        kw = keyword.lower()
        for nid, n in self.nodes.items():
            # 搜索名称和描述
            name = n.name.lower()
            data_str = json.dumps(n.data, ensure_ascii=False).lower()
            if kw in name or kw in data_str:
                results[n.type + "s"][nid] = n.data
        return dict(results)
