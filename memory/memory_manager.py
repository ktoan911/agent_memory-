"""
Memory Manager để quản lý và kết hợp tất cả các loại memory
"""

from typing import Any, Dict, List

from langchain.memory import ConversationBufferMemory, ConversationEntityMemory
from langchain.schema.messages import BaseMessage

from .json_chat_history import JSONChatMessageHistory
from .json_entity_store import JSONEntityStore
from .vector_memory import VectorStoreMemory


class MemoryManager:
    """
    Quản lý tất cả các loại memory cho một user
    Kết hợp Entity Memory, Chat History và Vector Memory
    """

    def __init__(self, user_id: str, llm, session_id: str = "default"):
        self.user_id = user_id
        self.session_id = session_id
        self.llm = llm

        self._initialize_memories()

    def _initialize_memories(self) -> None:
        """Khởi tạo tất cả các loại memory"""
        # 1. Entity Store để lưu thông tin về người dùng

        self.entity_store = JSONEntityStore(self.user_id)

        self.chat_history = JSONChatMessageHistory(self.user_id, self.session_id)
        self.conversation_memory = ConversationBufferMemory(
            chat_memory=self.chat_history,
            memory_key="chat_history",
            return_messages=True,
        )

        self.entity_memory = ConversationEntityMemory(
            entity_store=self.entity_store,
            llm=self.llm,
            memory_key="entities",
            return_messages=True,
        )

        self.vector_memory = VectorStoreMemory(self.user_id)

    def initialize_entity_memory_with_llm(self, llm):
        self.entity_memory = ConversationEntityMemory(
            entity_store=self.entity_store,
            llm=llm,
            memory_key="entities",
            return_messages=True,
        )

    def add_user_message(self, message: str) -> None:
        self.chat_history.add_user_message(message)
        self.vector_memory.add_memory(
            content=f"Người dùng nói: {message}", memory_type="user_message"
        )

    def add_ai_message(self, message: str) -> None:
        self.chat_history.add_ai_message(message)

        self.vector_memory.add_memory(
            content=f"AI trả lời: {message}", memory_type="ai_message"
        )

    def add_entity_fact(self, entity: str, fact: str) -> None:
        self.entity_store.add_fact(entity, fact)

        self.vector_memory.add_memory(
            content=f"Thông tin về {entity}: {fact}",
            memory_type="entity_fact",
            additional_metadata={"entity": entity},
        )

    def get_conversation_context(self, limit: int = 10) -> List[BaseMessage]:
        return self.chat_history.get_recent_messages(limit)

    def get_entity_info(self, entity: str) -> List[str]:
        return self.entity_store.get_entity_facts(entity)

    def get_all_entities(self) -> Dict[str, List[str]]:
        return self.entity_store.get_all_entities()

    def search_relevant_memories(self, query: str, limit: int = 5) -> str:
        return self.vector_memory.get_memory_summary(query)

    def get_memory_variables_for_chain(self) -> Dict[str, Any]:
        memory_vars = {}

        chat_memory = self.conversation_memory.load_memory_variables({})
        memory_vars.update(chat_memory)

        if self.entity_memory is not None:
            entity_memory = self.entity_memory.load_memory_variables({})
            memory_vars.update(entity_memory)

        return memory_vars

    def save_conversation_context(
        self, inputs: Dict[str, Any], outputs: Dict[str, str]
    ) -> None:
        self.conversation_memory.save_context(inputs, outputs)

        if self.entity_memory is not None:
            self.entity_memory.save_context(inputs, outputs)

        self.vector_memory.save_context(inputs, outputs)

    def get_memory_summary(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "total_entities": len(self.entity_store.get_all_entities()),
            "conversation_summary": self.chat_history.get_conversation_summary(),
            "entities": self.entity_store.get_all_entities(),
        }

    def clear_session_memory(self) -> None:
        self.chat_history.clear()

    def clear_all_memory(self) -> None:
        self.chat_history.clear()
        self.entity_store.clear()
        self.vector_memory.clear_memories()

    def search_chat_history(self, query: str, limit: int = 5) -> List[BaseMessage]:
        return self.chat_history.search_messages(query, limit)

    def get_comprehensive_context(
        self, current_input: str, context_limit: int = 5
    ) -> Dict[str, Any]:
        conversation_messages = self.get_conversation_context(context_limit)

        context = {
            "recent_conversation": [
                {
                    "role": "human" if "Human" in str(type(msg)) else "ai",
                    "content": msg.content,
                }
                for msg in conversation_messages
            ]
            if conversation_messages
            else [],
            "relevant_entities": self.get_all_entities(),
            "relevant_memories": self.search_relevant_memories(
                current_input, context_limit
            ),
            "memory_summary": self.get_memory_summary(),
        }

        return context
