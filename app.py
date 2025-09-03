"""
Demo Streamlit App cho Memory Chatbot
"""

import os

import streamlit as st

from chatbot import MemoryChatbot

# Cấu hình trang
st.set_page_config(
    page_title="Memory Chatbot Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.title("Chatbot Demo")

    # Sidebar cấu hình
    with st.sidebar:
        st.header("⚙️ Cấu hình")

        # Kiểm tra API key
        google_api_key = st.text_input(
            "Google API Key",
            type="password",
            help="Nhập Google API Key để sử dụng Gemini",
        )

        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key

        # User ID
        user_id = st.text_input(
            "User ID",
            value="toan",
            help="ID để phân biệt người dùng (dùng để lưu memory riêng biệt)",
        )

        # Session ID
        session_id = st.text_input("Session ID", value="1", help="ID phiên trò chuyện")

        st.divider()

        # Thông tin memory
        # if st.button("📊 Xem thông tin Memory"):
        #     if google_api_key:
        #         try:
        #             chatbot = MemoryChatbot(user_id, session_id)
        #             memory_info = chatbot.get_memory_summary()

        #             st.subheader("Thông tin Memory")
        #             st.json(memory_info)
        #         except Exception as e:
        #             st.error(f"Lỗi: {e}")
        #     else:
        #         st.warning("Vui lòng nhập Google API Key")

        # # Xóa memory
        # if st.button("🗑️ Xóa Memory Session"):
        #     if google_api_key:
        #         try:
        #             chatbot = MemoryChatbot(user_id, session_id)
        #             chatbot.clear_session()
        #             st.success("Đã xóa memory session!")
        #         except Exception as e:
        #             st.error(f"Lỗi: {e}")

        # if st.button("🗑️ Xóa Tất cả Memory"):
        #     if google_api_key:
        #         try:
        #             chatbot = MemoryChatbot(user_id, session_id)
        #             chatbot.clear_all_memory()
        #             st.success("Đã xóa tất cả memory!")
        #         except Exception as e:
        #             st.error(f"Lỗi: {e}")

    # Main chat interface
    if not google_api_key:
        return

    # Khởi tạo chatbot
    try:
        if (
            "chatbot" not in st.session_state
            or st.session_state.get("current_user_id") != user_id
        ):
            st.info("Khởi tạo chatbot...")
            st.session_state.chatbot = MemoryChatbot(user_id, session_id)
            st.session_state.current_user_id = user_id
            st.session_state.messages = []

        chatbot = st.session_state.chatbot

        # Hiển thị lịch sử chat
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Nhập tin nhắn của bạn..."):
            # Hiển thị tin nhắn người dùng
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Tạo phản hồi từ chatbot
            with st.chat_message("assistant"):
                with st.spinner("Đang suy nghĩ..."):
                    try:
                        response = chatbot.chat(prompt)
                        st.markdown(response)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )
                    except Exception as e:
                        error_msg = f"Xin lỗi, đã có lỗi xảy ra: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": error_msg}
                        )

        # Tìm kiếm memory
        # st.divider()
        # st.subheader("🔍 Tìm kiếm Memory")
        # search_query = st.text_input("Tìm kiếm trong bộ nhớ:")
        # if search_query and st.button("Tìm kiếm"):
        #     try:
        #         search_results = chatbot.search_memory(search_query)
        #         st.text_area("Kết quả tìm kiếm:", value=search_results, height=200)
        #     except Exception as e:
        #         st.error(f"Lỗi tìm kiếm: {e}")

    except Exception as e:
        st.error(f"Lỗi khởi tạo chatbot: {e}")
        st.info("Hãy kiểm tra lại API key và thử lại")


if __name__ == "__main__":
    main()
