from typing import Dict, List, Optional

from langchain.memory.entity import BaseEntityStore
from pydantic import Field
from pymongo import MongoClient

from config import CHAT_COL_ENTITIES, CHAT_DBNAME, MONGODB_URI


class JSONEntityStore(BaseEntityStore):
    user_id: str = Field(default="")

    def __init__(self, user_id: str):
        # Initialize với user_id và data khác
        super().__init__(user_id=user_id)
        self.client = MongoClient(MONGODB_URI)
        self.col = self.client[CHAT_DBNAME][CHAT_COL_ENTITIES]

    def _get_user_entity(self):
        user_entity = self.col.find_one({"user_id": self.user_id})
        if user_entity is None:
            user_entity = {"user_id": self.user_id}
            self.col.insert_one(user_entity)
        return user_entity
    def clear(self) -> None:
        self.col.delete_one({"user_id": self.user_id})

    def get_all_entities(self) -> Dict[str, List[str]]:
        return self._get_user_entity()

    def get_entity_facts(self, entity_key: str) -> List[str]:
        entities = self._get_user_entity()
        return entities.get(entity_key, [])

    def add_fact(self, entity_key: str, fact: str) -> None:
        entities = self._get_user_entity()
        if entity_key not in entities:
            entities[entity_key] = []

        # Tránh lưu trùng lặp
        if fact not in entities[entity_key]:
            entities[entity_key].append(fact)

        self.col.update_one({"user_id": self.user_id}, {"$set": entities})
