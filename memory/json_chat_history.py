"""
JSON-based Chat Message History để lưu trữ lịch sử trò chuyện
"""
import json
from pathlib import Path
from typing import List
from langchain.schema import BaseChatMessageHistory
from langchain.schema.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from config import CHAT_HISTORY_DIR


class JSONChatMessageHistory(BaseChatMessageHistory):
    """
    Chat Message History sử dụng file JSON để lưu trữ
    Mỗi user_id sẽ có một file JSON riêng chứa lịch sử trò chuyện
    """
    
    def __init__(self, user_id: str, session_id: str = "default"):
        """
        Khởi tạo JSONChatMessageHistory
        
        Args:
            user_id: ID của người dùng
            session_id: ID của phiên trò chuyện (mặc định là "default")
        """
        self.user_id = user_id
        self.session_id = session_id
        self.file_path = CHAT_HISTORY_DIR / f"{user_id}_{session_id}_history.json"
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Đảm bảo file JSON tồn tại"""
        if not self.file_path.exists():
            self.file_path.write_text(json.dumps([]))
    
    def _message_to_dict(self, message: BaseMessage) -> dict:
        """Chuyển đổi BaseMessage thành dictionary"""
        return {
            "type": message.__class__.__name__,
            "content": message.content,
            "additional_kwargs": getattr(message, "additional_kwargs", {}),
        }
    
    def _dict_to_message(self, message_dict: dict) -> BaseMessage:
        """Chuyển đổi dictionary thành BaseMessage"""
        message_type = message_dict["type"]
        content = message_dict["content"]
        additional_kwargs = message_dict.get("additional_kwargs", {})
        
        if message_type == "HumanMessage":
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
        elif message_type == "AIMessage":
            return AIMessage(content=content, additional_kwargs=additional_kwargs)
        elif message_type == "SystemMessage":
            return SystemMessage(content=content, additional_kwargs=additional_kwargs)
        else:
            # Fallback cho các loại message khác
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
    
    def _load_messages(self) -> List[dict]:
        """Tải messages từ file JSON"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_messages(self, messages: List[dict]) -> None:
        """Lưu messages vào file JSON"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Lấy tất cả messages"""
        message_dicts = self._load_messages()
        return [self._dict_to_message(msg_dict) for msg_dict in message_dicts]
    
    def add_message(self, message: BaseMessage) -> None:
        """
        Thêm một message mới
        
        Args:
            message: Message cần thêm
        """
        messages = self._load_messages()
        messages.append(self._message_to_dict(message))
        self._save_messages(messages)
    
    def add_user_message(self, message: str) -> None:
        """
        Thêm message từ người dùng
        
        Args:
            message: Nội dung message
        """
        self.add_message(HumanMessage(content=message))
    
    def add_ai_message(self, message: str) -> None:
        """
        Thêm message từ AI
        
        Args:
            message: Nội dung message
        """
        self.add_message(AIMessage(content=message))
    
    def clear(self) -> None:
        """Xóa tất cả messages"""
        self._save_messages([])
    
    def get_messages_count(self) -> int:
        """Lấy số lượng messages"""
        return len(self._load_messages())
    
    def get_recent_messages(self, limit: int = 10) -> List[BaseMessage]:
        """
        Lấy các messages gần đây nhất
        
        Args:
            limit: Số lượng messages tối đa
            
        Returns:
            Danh sách các messages gần đây
        """
        all_messages = self.messages
        return all_messages[-limit:] if len(all_messages) > limit else all_messages
    
    def get_conversation_summary(self) -> str:
        """
        Tạo tóm tắt cuộc trò chuyện
        
        Returns:
            Chuỗi tóm tắt cuộc trò chuyện
        """
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
        """
        Tìm kiếm messages theo nội dung
        
        Args:
            query: Từ khóa tìm kiếm
            limit: Số lượng kết quả tối đa
            
        Returns:
            Danh sách messages chứa từ khóa
        """
        messages = self.messages
        matching_messages = []
        
        for message in messages:
            if query.lower() in message.content.lower():
                matching_messages.append(message)
                if len(matching_messages) >= limit:
                    break
        
        return matching_messages