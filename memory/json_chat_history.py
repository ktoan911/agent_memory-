"""
JSON-based Chat Message History để lưu trữ lịch sử trò chuyện
"""

import json
import time
from typing import List

from langchain.schema import BaseChatMessageHistory
from langchain.schema.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from pymongo import MongoClient

from config import CHAT_COL_HISTORY, CHAT_DBNAME, MONGODB_URI


class JSONChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, user_id: str, session_id: str = "default"):
        """
        Khởi tạo JSONChatMessageHistory

        Args:
            user_id: ID của người dùng
            session_id: ID của phiên trò chuyện (mặc định là "default")
        """
        self.user_id = user_id
        self.session_id = session_id
        self.client = MongoClient(MONGODB_URI)
        self.col = self.client[CHAT_DBNAME][CHAT_COL_HISTORY]

    def _message_to_dict(self, message: BaseMessage) -> dict:
        return {
            "type": message.__class__.__name__,
            "content": message.content,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": time.time(),
        }

    def delete(self):
        return None

    def exists(self):
        return False

    def get(self):
        return []

    def set(self, messages):
        return None

    def _dict_to_message(self, message_dict: dict) -> BaseMessage:
        """Chuyển đổi dictionary thành BaseMessage"""
        message_type = message_dict["type"]
        content = message_dict["content"]

        if message_type == "HumanMessage":
            return HumanMessage(content=content)
        elif message_type == "AIMessage":
            return AIMessage(content=content)
        elif message_type == "SystemMessage":
            return SystemMessage(content=content)
        else:
            return HumanMessage(content=content)

    def _load_messages(self) -> List[dict]:
        try:
            message_dicts = list(
                self.col.find({"user_id": self.user_id, "session_id": self.session_id})
            )
            if not message_dicts:
                return []
            return message_dicts
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @property
    def messages(self) -> List[BaseMessage]:
        """Lấy tất cả messages"""
        message_dicts = self._load_messages()
        return [self._dict_to_message(msg_dict) for msg_dict in message_dicts]

    def add_message(self, message: BaseMessage) -> None:
        self.col.insert_one(self._message_to_dict(message))

    def add_user_message(self, message: str) -> None:
        self.add_message(HumanMessage(content=message))

    def add_ai_message(self, message: str) -> None:
        self.add_message(AIMessage(content=message))

    def clear(self) -> None:
        self.col.delete_many({"user_id": self.user_id, "session_id": self.session_id})

    def get_recent_messages(self, limit: int = 10) -> List[BaseMessage]:
        return self.messages[-limit:] if len(self.messages) > limit else self.messages

    def get_conversation_summary(self) -> str:
        messages = self.messages
        if not messages:
            return "Chưa có cuộc trò chuyện nào."

        summary_parts = []
        for message in messages[-10:]:  # Chỉ lấy 10 message gần nhất
            if isinstance(message, HumanMessage):
                summary_parts.append(f"Người dùng: {message.content[:100]}...")
            elif isinstance(message, AIMessage):
                summary_parts.append(f"AI: {message.content[:100]}...")

        return "\n".join(summary_parts)

    def search_messages(self, query: str, limit: int = 5) -> List[BaseMessage]:
        messages = self.messages
        matching_messages = []

        for message in messages:
            if query.lower() in message.content.lower():
                matching_messages.append(message)
                if len(matching_messages) >= limit:
                    break

        return matching_messages
