"""
Memory Manager để quản lý và kết hợp tất cả các loại memory
"""
from typing import Dict, List, Any, Optional
from langchain.memory import ConversationBufferMemory, ConversationEntityMemory
from langchain.schema import BaseMemory
from langchain.schema.messages import BaseMessage

from .json_entity_store import JSONEntityStore
from .json_chat_history import JSONChatMessageHistory
from .vector_memory import VectorStoreMemory


class MemoryManager:
    """
    Quản lý tất cả các loại memory cho một user
    Kết hợp Entity Memory, Chat History và Vector Memory
    """
    
    def __init__(self, user_id: str, session_id: str = "default"):
        """
        Khởi tạo MemoryManager
        
        Args:
            user_id: ID của người dùng
            session_id: ID của phiên trò chuyện
        """
        self.user_id = user_id
        self.session_id = session_id
        
        # Khởi tạo các loại memory
        self._initialize_memories()
    
    def _initialize_memories(self) -> None:
        """Khởi tạo tất cả các loại memory"""
        # 1. Entity Store để lưu thông tin về người dùng
        self.entity_store = JSONEntityStore(self.user_id)
        
        # 2. Chat Message History để lưu lịch sử trò chuyện
        self.chat_history = JSONChatMessageHistory(self.user_id, self.session_id)
        
        # 3. Conversation Buffer Memory với chat history
        self.conversation_memory = ConversationBufferMemory(
            chat_memory=self.chat_history,
            memory_key="chat_history",
            return_messages=True
        )
        
        # 4. Entity Memory để theo dõi thông tin thực thể
        self.entity_memory = ConversationEntityMemory(
            entity_store=self.entity_store,
            memory_key="entities",
            return_messages=True
        )
        
        # 5. Vector Store Memory để semantic search
        self.vector_memory = VectorStoreMemory(self.user_id)
    
    def add_user_message(self, message: str) -> None:
        """
        Thêm message từ người dùng
        
        Args:
            message: Nội dung message
        """
        # Thêm vào chat history
        self.chat_history.add_user_message(message)
        
        # Thêm vào vector memory
        self.vector_memory.add_memory(
            content=f"Người dùng nói: {message}",
            memory_type="user_message"
        )
    
    def add_ai_message(self, message: str) -> None:
        """
        Thêm message từ AI
        
        Args:
            message: Nội dung message
        """
        # Thêm vào chat history
        self.chat_history.add_ai_message(message)
        
        # Thêm vào vector memory
        self.vector_memory.add_memory(
            content=f"AI trả lời: {message}",
            memory_type="ai_message"
        )
    
    def add_entity_fact(self, entity: str, fact: str) -> None:
        """
        Thêm thông tin về một thực thể
        
        Args:
            entity: Tên thực thể
            fact: Thông tin về thực thể
        """
        self.entity_store.add_fact(entity, fact)
        
        # Cũng lưu vào vector memory
        self.vector_memory.add_memory(
            content=f"Thông tin về {entity}: {fact}",
            memory_type="entity_fact",
            additional_metadata={"entity": entity}
        )
    
    def get_conversation_context(self, limit: int = 10) -> List[BaseMessage]:
        """
        Lấy ngữ cảnh cuộc trò chuyện gần đây
        
        Args:
            limit: Số lượng messages tối đa
            
        Returns:
            Danh sách messages gần đây
        """
        return self.chat_history.get_recent_messages(limit)
    
    def get_entity_info(self, entity: str) -> List[str]:
        """
        Lấy thông tin về một thực thể
        
        Args:
            entity: Tên thực thể
            
        Returns:
            Danh sách thông tin về thực thể
        """
        return self.entity_store.get_entity_facts(entity)
    
    def get_all_entities(self) -> Dict[str, List[str]]:
        """
        Lấy tất cả thông tin thực thể
        
        Returns:
            Dictionary chứa tất cả thực thể và thông tin
        """
        return self.entity_store.get_all_entities()
    
    def search_relevant_memories(self, query: str, limit: int = 5) -> str:
        """
        Tìm kiếm memories liên quan đến query
        
        Args:
            query: Câu hỏi hoặc chủ đề
            limit: Số lượng kết quả tối đa
            
        Returns:
            Chuỗi tóm tắt các memories liên quan
        """
        return self.vector_memory.get_memory_summary(query)
    
    def get_memory_variables_for_chain(self) -> Dict[str, Any]:
        """
        Lấy tất cả memory variables để sử dụng trong LangChain
        
        Returns:
            Dictionary chứa tất cả memory variables
        """
        memory_vars = {}
        
        # Chat history
        chat_memory = self.conversation_memory.load_memory_variables({})
        memory_vars.update(chat_memory)
        
        # Entity memory
        entity_memory = self.entity_memory.load_memory_variables({})
        memory_vars.update(entity_memory)
        
        return memory_vars
    
    def save_conversation_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Lưu context của cuộc trò chuyện
        
        Args:
            inputs: Input variables
            outputs: Output variables
        """
        # Lưu vào conversation memory
        self.conversation_memory.save_context(inputs, outputs)
        
        # Lưu vào entity memory (sẽ tự động extract entities)
        self.entity_memory.save_context(inputs, outputs)
        
        # Lưu vào vector memory
        self.vector_memory.save_context(inputs, outputs)
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Tạo tóm tắt tổng quan về memory
        
        Returns:
            Dictionary chứa thông tin tóm tắt
        """
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "total_messages": self.chat_history.get_messages_count(),
            "total_entities": len(self.entity_store.get_all_entities()),
            "total_vector_memories": self.vector_memory.get_memories_count(),
            "conversation_summary": self.chat_history.get_conversation_summary(),
            "entities": self.entity_store.get_all_entities()
        }
    
    def clear_session_memory(self) -> None:
        """Xóa memory của session hiện tại (giữ lại entities và vector memories)"""
        self.chat_history.clear()
    
    def clear_all_memory(self) -> None:
        """Xóa tất cả memory của user"""
        self.chat_history.clear()
        self.entity_store.clear()
        self.vector_memory.clear_memories()
    
    def search_chat_history(self, query: str, limit: int = 5) -> List[BaseMessage]:
        """
        Tìm kiếm trong lịch sử chat
        
        Args:
            query: Từ khóa tìm kiếm
            limit: Số lượng kết quả tối đa
            
        Returns:
            Danh sách messages chứa từ khóa
        """
        return self.chat_history.search_messages(query, limit)
    
    def get_comprehensive_context(self, current_input: str, context_limit: int = 5) -> Dict[str, Any]:
        """
        Lấy ngữ cảnh toàn diện cho câu hỏi hiện tại
        
        Args:
            current_input: Câu hỏi/input hiện tại
            context_limit: Giới hạn số lượng context items
            
        Returns:
            Dictionary chứa tất cả ngữ cảnh liên quan
        """
        context = {
            # Lịch sử trò chuyện gần đây
            "recent_conversation": [
                {"role": "human" if isinstance(msg, type(self.chat_history.messages[0])) and "Human" in str(type(msg)) else "ai",
                 "content": msg.content}
                for msg in self.get_conversation_context(context_limit)
            ],
            
            # Thông tin thực thể liên quan
            "relevant_entities": self.get_all_entities(),
            
            # Memories liên quan từ vector search
            "relevant_memories": self.search_relevant_memories(current_input, context_limit),
            
            # Tóm tắt memory tổng quan
            "memory_summary": self.get_memory_summary()
        }
        
        return context