"""
Chatbot chính sử dụng Gemini với memory tích hợp
"""

from typing import Any, Dict

from langchain.schema import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config import GOOGLE_API_KEY, MODEL_NAME, TEMPERATURE
from memory.memory_manager import MemoryManager


class MemoryChatbot:
    def __init__(self, user_id: str, session_id: str = "default"):
        """
        Khởi tạo chatbot

        Args:
            user_id: ID của người dùng
            session_id: ID của phiên trò chuyện
        """
        self.user_id = user_id
        self.session_id = session_id

        # Khởi tạo Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            google_api_key=GOOGLE_API_KEY,
            temperature=TEMPERATURE,
            convert_system_message_to_human=True,
        )

        # Khởi tạo Memory Manager
        self.memory_manager = MemoryManager(user_id, self.llm, session_id)

        # System prompt cho chatbot
        self.system_prompt = """Bạn là một AI assistant thông minh và thân thiện. 
        Bạn có khả năng nhớ thông tin về người dùng qua nhiều cuộc trò chuyện.
        
        Hãy sử dụng thông tin từ bộ nhớ để cung cấp câu trả lời cá nhân hóa và phù hợp.
        Nếu bạn học được thông tin mới về người dùng, hãy ghi nhớ nó.
        
        Luôn trả lời một cách tự nhiên, thân thiện và hữu ích."""

    def _build_context_prompt(self, user_input: str) -> str:
        context = self.memory_manager.get_comprehensive_context(user_input)

        # Xây dựng prompt
        prompt_parts = [self.system_prompt]

        # Thêm thông tin về entities (thông tin cá nhân)
        if context["relevant_entities"]:
            prompt_parts.append("\n=== THÔNG TIN ĐÃ BIẾT VỀ NGƯỜI DÙNG ===")
            for entity, facts in context["relevant_entities"].items():
                if facts:
                    prompt_parts.append(f"{entity}: {', '.join(facts)}")

        # Thêm memories liên quan
        if (
            context["relevant_memories"]
            and context["relevant_memories"]
            != "Không tìm thấy thông tin liên quan trong bộ nhớ."
        ):
            prompt_parts.append(
                "\n=== THÔNG TIN LIÊN QUAN TỪ CÁC CUỘC TRÒ CHUYỆN TRƯỚC ==="
            )
            prompt_parts.append(context["relevant_memories"])

        # Thêm lịch sử trò chuyện gần đây
        if context["recent_conversation"]:
            prompt_parts.append("\n=== LỊCH SỬ TRÒ CHUYỆN GẦN ĐÂY ===")
            for msg in context["recent_conversation"][
                -5:
            ]:  # Chỉ lấy 5 tin nhắn gần nhất
                role = "Người dùng" if msg["role"] == "human" else "AI"
                prompt_parts.append(f"{role}: {msg['content']}")

        # Thêm câu hỏi hiện tại
        prompt_parts.append(f"\n=== CÂU HỎI HIỆN TẠI ===\nNgười dùng: {user_input}")
        prompt_parts.append("\nHãy trả lời một cách tự nhiên và hữu ích:")

        return "\n".join(prompt_parts)

    def _extract_and_save_entities(self, user_input: str) -> None:
        personal_keywords = {
            "tên": ["tên tôi là", "tôi tên", "mình tên", "tôi là"],
            "tuổi": ["tôi", "tuổi", "năm nay", "sinh năm"],
            "nghề nghiệp": ["tôi làm", "nghề", "công việc", "làm việc tại"],
            "sở thích": ["thích", "yêu thích", "sở thích", "hobby", "yêu"],
            "địa chỉ": ["tôi ở", "sống ở", "địa chỉ", "quê ở"],
            "gia đình": ["vợ", "chồng", "con", "bố mẹ", "anh chị em"],
        }

        # Kiểm tra và trích xuất thông tin từ user input
        user_lower = user_input.lower()
        for entity_type, keywords in personal_keywords.items():
            for keyword in keywords:
                if keyword in user_lower:
                    # Lưu thông tin vào entity store
                    self.memory_manager.add_entity_fact(entity_type, user_input)
                    break
    
    def chat(self, user_input: str) -> str:
        try:
            # Lưu tin nhắn của người dùng
            self.memory_manager.add_user_message(user_input)

            # Xây dựng prompt với context
            full_prompt = self._build_context_prompt(user_input)

            # Gọi Gemini để tạo phản hồi
            response = self.llm.invoke([HumanMessage(content=full_prompt)])
            ai_response = response.content

            # Lưu phản hồi của AI
            self.memory_manager.add_ai_message(ai_response)

            # Trích xuất và lưu thông tin thực thể
            self._extract_and_save_entities(user_input, ai_response)

            # Lưu context cho các memory khác
            self.memory_manager.save_conversation_context(
                {"input": user_input}, {"output": ai_response}
            )

            return ai_response

        except Exception as e:
            error_msg = f"Xin lỗi, đã có lỗi xảy ra: {str(e)}"
            print(f"Lỗi trong chatbot: {e}")
            return error_msg

    def get_memory_summary(self) -> Dict[str, Any]:
        return self.memory_manager.get_memory_summary()

    def search_memory(self, query: str) -> str:
        return self.memory_manager.search_relevant_memories(query)

    def clear_session(self) -> None:
        self.memory_manager.clear_session_memory()

    def clear_all_memory(self) -> None:
        self.memory_manager.clear_all_memory()

    def get_conversation_history(self, limit: int = 10) -> list:
        messages = self.memory_manager.get_conversation_context(limit)
        history = []

        for msg in messages:
            if hasattr(msg, "__class__"):
                if "Human" in str(type(msg)):
                    history.append({"role": "user", "content": msg.content})
                elif "AI" in str(type(msg)):
                    history.append({"role": "assistant", "content": msg.content})

        return history
