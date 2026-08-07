import os
import json
import re
from typing import List, Dict, Any, Optional

class MongoTemplate:
    """
    A custom Python abstraction layer matching the MongoTemplate design pattern.
    Handles connections and queries to MongoDB collections, with a fully
    transparent JSON database fallback.
    """
    def __init__(self, db_client=None, db_name: str = None, fallback_json_path: str = None):
        self.db = db_client[db_name] if db_client is not None else None
        self.fallback_json_path = fallback_json_path
        self.mongo_available = self.db is not None

    def _read_fallback(self, collection_name: str) -> List[Dict[str, Any]]:
        if not self.fallback_json_path or not os.path.exists(self.fallback_json_path):
            return []
        try:
            with open(self.fallback_json_path, "r") as f:
                data = json.load(f)
                return data.get(collection_name, [])
        except Exception:
            return []

    def _write_fallback(self, collection_name: str, data_list: List[Dict[str, Any]]):
        if not self.fallback_json_path:
            return
        try:
            data = {}
            if os.path.exists(self.fallback_json_path):
                with open(self.fallback_json_path, "r") as f:
                    data = json.load(f)
            data[collection_name] = data_list
            with open(self.fallback_json_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def find(self, collection_name: str, query: dict = None, projection: dict = None) -> List[Dict[str, Any]]:
        query = query or {}
        projection = projection or {"_id": 0}
        
        if self.mongo_available:
            return list(self.db[collection_name].find(query, projection))
        else:
            items = self._read_fallback(collection_name)
            filtered = []
            for item in items:
                match = True
                for k, v in query.items():
                    if isinstance(v, dict):
                        if "$regex" in v:
                            pattern = v["$regex"]
                            flags = re.IGNORECASE if v.get("$options") == "i" else 0
                            if not re.search(pattern, str(item.get(k, "")), flags):
                                match = False
                                break
                        else:
                            match = False
                            break
                    elif item.get(k) != v:
                        match = False
                        break
                if match:
                    cleaned = item.copy()
                    cleaned.pop("_id", None)
                    filtered.append(cleaned)
            return filtered

    def find_one(self, collection_name: str, query: dict, projection: dict = None) -> Optional[Dict[str, Any]]:
        res = self.find(collection_name, query, projection)
        return res[0] if res else None

    def save(self, collection_name: str, query_filter: dict, document: dict, upsert: bool = True):
        cleaned = document.copy()
        cleaned.pop("_id", None)
        
        if self.mongo_available:
            return self.db[collection_name].replace_one(query_filter, cleaned, upsert=upsert)
        else:
            items = self._read_fallback(collection_name)
            idx = -1
            for i, item in enumerate(items):
                match = True
                for k, v in query_filter.items():
                    if item.get(k) != v:
                        match = False
                        break
                if match:
                    idx = i
                    break
            
            if idx != -1:
                items[idx] = cleaned
            elif upsert:
                items.append(cleaned)
            
            self._write_fallback(collection_name, items)

    def insert_many(self, collection_name: str, documents: List[dict]):
        cleaned = []
        for doc in documents:
            c = doc.copy()
            c.pop("_id", None)
            cleaned.append(c)
            
        if self.mongo_available:
            if cleaned:
                return self.db[collection_name].insert_many(cleaned)
        else:
            items = self._read_fallback(collection_name)
            items.extend(cleaned)
            self._write_fallback(collection_name, items)

    def delete_many(self, collection_name: str, query: dict = None):
        query = query or {}
        if self.mongo_available:
            return self.db[collection_name].delete_many(query)
        else:
            items = self._read_fallback(collection_name)
            filtered = [item for item in items if not all(item.get(k) == v for k, v in query.items())]
            self._write_fallback(collection_name, filtered)

    def count(self, collection_name: str, query: dict = None) -> int:
        query = query or {}
        if self.mongo_available:
            return self.db[collection_name].count_documents(query)
        else:
            return len(self.find(collection_name, query))
