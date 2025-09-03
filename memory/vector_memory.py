"""
Vector Store Memory để lưu trữ và truy xuất thông tin dựa trên semantic search
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from langchain.docstore.document import Document
from langchain.schema import BaseMemory
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from pydantic import Field
from pymongo import MongoClient

from config import (
    CHAT_COL_VECTOR,
    CHAT_DBNAME,
    GOOGLE_API_KEY,
    MAX_RETRIEVED_MEMORIES,
    MONGODB_URI,
)

from .safe_embeddings import SafeGoogleGenerativeAIEmbeddings


def ensure_event_loop():
    """Đảm bảo có event loop cho các thao tác async"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        # Tạo event loop mới nếu không có hoặc bị đóng
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


class VectorStoreMemory(BaseMemory):
    user_id: str = Field(default="")
    embeddings: Optional[Any] = Field(default=None, exclude=True)
    metadata_path: Optional[Path] = Field(default=None, exclude=True)
    vector_store: Optional[Any] = Field(default=None, exclude=True)

    def __init__(self, user_id: str, **data):
        """
        Khởi tạo VectorStoreMemory

        Args:
            user_id: ID của người dùng
        """
        # Đảm bảo có event loop
        ensure_event_loop()

        super().__init__(user_id=user_id, **data)
        self.embeddings = SafeGoogleGenerativeAIEmbeddings(
            model="models/embedding-001", google_api_key=GOOGLE_API_KEY
        )

        self.client = MongoClient(MONGODB_URI)
        self.col = self.client[CHAT_DBNAME][CHAT_COL_VECTOR]
        self._initialize_vector_store()

    def _check_exist_user(self, user_id: str) -> bool:
        """Kiểm tra xem người dùng đã tồn tại trong cơ sở dữ liệu hay chưa"""
        user = self.col.find_one({"user_id": user_id})
        return user is not None

    def _initialize_vector_store(self) -> None:
        """Khởi tạo hoặc tải vector store từ file"""
        try:
            if self._check_exist_user(self.user_id):
                self.vector_store = MongoDBAtlasVectorSearch(self.col, self.embeddings)
            else:
                dummy_doc = Document(
                    page_content="Khởi tạo vector store",
                    metadata={"user_id": self.user_id, "type": "init"},
                )
                self.vector_store = MongoDBAtlasVectorSearch(
                    self.col, self.embeddings
                ).from_documents([dummy_doc], self.embeddings)
        except Exception as e:
            print(f"Lỗi khi khởi tạo vector store: {e}")
            dummy_doc = Document(
                page_content="Khởi tạo vector store",
                metadata={"user_id": self.user_id, "type": "init"},
            )
            self.vector_store = MongoDBAtlasVectorSearch(
                self.col, self.embeddings
            ).from_documents([dummy_doc], self.embeddings)

    def add_memory(
        self,
        content: str,
        memory_type: str = "conversation",
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        ensure_event_loop()

        metadata = {
            "user_id": self.user_id,
            "type": memory_type,
            "timestamp": str(np.datetime64("now")),
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        document = Document(page_content=content, metadata=metadata)

        try:
            self.vector_store.add_documents([document])
        except Exception as e:
            print(f"Lỗi khi thêm memory: {e}")

    def retrieve_memories(
        self, query: str, k: int = MAX_RETRIEVED_MEMORIES
    ) -> List[Document]:
        ensure_event_loop()

        try:
            # Tìm kiếm similarity
            docs = self.vector_store.similarity_search(query, k=k)

            filtered_docs = [doc for doc in docs if doc.metadata.get("type") != "init"]

            return filtered_docs
        except Exception as e:
            print(f"Lỗi khi truy xuất memories: {e}")
            return []

    def get_memory_summary(self, query: str) -> str:
        memories = self.retrieve_memories(query)

        if not memories:
            return "Không tìm thấy thông tin liên quan trong bộ nhớ."

        summary_parts = []
        for i, memory in enumerate(memories, 1):
            memory_type = memory.metadata.get("type", "unknown")
            content_preview = (
                memory.page_content[:200] + "..."
                if len(memory.page_content) > 200
                else memory.page_content
            )

            summary_parts.append(f"{i}. [{memory_type}] {content_preview}")

        return "\n".join(summary_parts)

    def clear_memories(self) -> None:
        """Xóa tất cả memories"""
        try:
            # Tạo lại vector store với document dummy
            self.col.delete_many({"user_id": self.user_id})
            dummy_doc = Document(
                page_content="Khởi tạo vector store",
                metadata={"user_id": self.user_id, "type": "init"},
            )
            self.vector_store = MongoDBAtlasVectorSearch.from_documents(
                [dummy_doc], self.embeddings
            )

        except Exception as e:
            print(f"Lỗi khi xóa memories: {e}")

    def clear(self) -> None:
        self.clear_memories()

    @property
    def memory_variables(self) -> List[str]:
        """Biến memory được sử dụng bởi memory này"""
        return ["relevant_memories"]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """
        Tải các biến memory dựa trên inputs

        Args:
            inputs: Dictionary chứa input variables

        Returns:
            Dictionary chứa memory variables
        """
        query = inputs.get("input", "")
        if query:
            relevant_memories = self.get_memory_summary(query)
            return {"relevant_memories": relevant_memories}
        return {"relevant_memories": ""}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Lưu context từ inputs và outputs

        Args:
            inputs: Input variables
            outputs: Output variables
        """
        user_input = inputs.get("input", "")
        ai_output = outputs.get("output", "")

        if user_input and ai_output:
            # Lưu cuộc trò chuyện
            conversation = f"Người dùng: {user_input}\nAI: {ai_output}"
            self.add_memory(
                content=conversation,
                memory_type="conversation",
                additional_metadata={"user_input": user_input, "ai_output": ai_output},
            )
