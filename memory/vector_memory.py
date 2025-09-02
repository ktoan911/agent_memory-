"""
Vector Store Memory để lưu trữ và truy xuất thông tin dựa trên semantic search
"""
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from langchain.schema import BaseMemory
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from config import VECTOR_STORE_DIR, MAX_RETRIEVED_MEMORIES, GOOGLE_API_KEY


class VectorStoreMemory(BaseMemory):
    """
    Memory sử dụng FAISS vector store để lưu trữ và truy xuất thông tin
    dựa trên semantic similarity
    """
    
    def __init__(self, user_id: str):
        """
        Khởi tạo VectorStoreMemory
        
        Args:
            user_id: ID của người dùng
        """
        self.user_id = user_id
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
        self.vector_store_path = VECTOR_STORE_DIR / f"{user_id}_vectorstore"
        self.metadata_path = VECTOR_STORE_DIR / f"{user_id}_metadata.json"
        
        # Khởi tạo hoặc tải vector store
        self._initialize_vector_store()
    
    def _initialize_vector_store(self) -> None:
        """Khởi tạo hoặc tải vector store từ file"""
        try:
            if self.vector_store_path.exists():
                # Tải vector store hiện có
                self.vector_store = FAISS.load_local(
                    str(self.vector_store_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                # Tạo vector store mới với document dummy
                dummy_doc = Document(
                    page_content="Khởi tạo vector store",
                    metadata={"user_id": self.user_id, "type": "init"}
                )
                self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)
                self._save_vector_store()
        except Exception as e:
            print(f"Lỗi khi khởi tạo vector store: {e}")
            # Tạo vector store mới nếu có lỗi
            dummy_doc = Document(
                page_content="Khởi tạo vector store",
                metadata={"user_id": self.user_id, "type": "init"}
            )
            self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)
            self._save_vector_store()
    
    def _save_vector_store(self) -> None:
        """Lưu vector store vào file"""
        try:
            self.vector_store.save_local(str(self.vector_store_path))
        except Exception as e:
            print(f"Lỗi khi lưu vector store: {e}")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Tải metadata từ file"""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}
        return {}
    
    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Lưu metadata vào file"""
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def add_memory(self, content: str, memory_type: str = "conversation", 
                   additional_metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Thêm một memory mới vào vector store
        
        Args:
            content: Nội dung memory
            memory_type: Loại memory (conversation, fact, decision, etc.)
            additional_metadata: Metadata bổ sung
        """
        metadata = {
            "user_id": self.user_id,
            "type": memory_type,
            "timestamp": str(np.datetime64('now'))
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        document = Document(page_content=content, metadata=metadata)
        
        try:
            # Thêm document vào vector store
            self.vector_store.add_documents([document])
            self._save_vector_store()
            
            # Cập nhật metadata tracking
            all_metadata = self._load_metadata()
            memory_id = f"{self.user_id}_{len(all_metadata)}"
            all_metadata[memory_id] = metadata
            self._save_metadata(all_metadata)
            
        except Exception as e:
            print(f"Lỗi khi thêm memory: {e}")
    
    def retrieve_memories(self, query: str, k: int = MAX_RETRIEVED_MEMORIES) -> List[Document]:
        """
        Truy xuất memories liên quan dựa trên query
        
        Args:
            query: Câu hỏi hoặc nội dung cần tìm
            k: Số lượng memories tối đa cần truy xuất
            
        Returns:
            Danh sách các documents liên quan
        """
        try:
            # Tìm kiếm similarity
            docs = self.vector_store.similarity_search(query, k=k)
            
            # Lọc bỏ document dummy init
            filtered_docs = [doc for doc in docs if doc.metadata.get("type") != "init"]
            
            return filtered_docs
        except Exception as e:
            print(f"Lỗi khi truy xuất memories: {e}")
            return []
    
    def retrieve_memories_with_scores(self, query: str, k: int = MAX_RETRIEVED_MEMORIES) -> List[tuple]:
        """
        Truy xuất memories với điểm số similarity
        
        Args:
            query: Câu hỏi hoặc nội dung cần tìm
            k: Số lượng memories tối đa cần truy xuất
            
        Returns:
            Danh sách tuple (document, score)
        """
        try:
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Lọc bỏ document dummy init
            filtered_docs = [(doc, score) for doc, score in docs_with_scores 
                           if doc.metadata.get("type") != "init"]
            
            return filtered_docs
        except Exception as e:
            print(f"Lỗi khi truy xuất memories với scores: {e}")
            return []
    
    def get_memory_summary(self, query: str) -> str:
        """
        Tạo tóm tắt memories liên quan đến query
        
        Args:
            query: Câu hỏi hoặc chủ đề
            
        Returns:
            Chuỗi tóm tắt các memories liên quan
        """
        memories = self.retrieve_memories(query)
        
        if not memories:
            return "Không tìm thấy thông tin liên quan trong bộ nhớ."
        
        summary_parts = []
        for i, memory in enumerate(memories, 1):
            memory_type = memory.metadata.get("type", "unknown")
            timestamp = memory.metadata.get("timestamp", "unknown")
            content_preview = memory.page_content[:200] + "..." if len(memory.page_content) > 200 else memory.page_content
            
            summary_parts.append(f"{i}. [{memory_type}] {content_preview}")
        
        return "\n".join(summary_parts)
    
    def clear_memories(self) -> None:
        """Xóa tất cả memories"""
        try:
            # Tạo lại vector store với document dummy
            dummy_doc = Document(
                page_content="Khởi tạo vector store",
                metadata={"user_id": self.user_id, "type": "init"}
            )
            self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)
            self._save_vector_store()
            
            # Xóa metadata
            self._save_metadata({})
            
        except Exception as e:
            print(f"Lỗi khi xóa memories: {e}")
    
    def get_memories_count(self) -> int:
        """Lấy số lượng memories (không tính document init)"""
        try:
            # Đếm documents trong vector store
            all_docs = self.vector_store.similarity_search("", k=1000)  # Lấy tất cả
            return len([doc for doc in all_docs if doc.metadata.get("type") != "init"])
        except:
            return 0
    
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
                additional_metadata={
                    "user_input": user_input,
                    "ai_output": ai_output
                }
            )