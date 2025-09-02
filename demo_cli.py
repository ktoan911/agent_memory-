"""
Demo CLI cho Memory Chatbot
"""
import os
from chatbot import MemoryChatbot

def print_banner():
    """In banner chào mừng"""
    print("=" * 60)
    print("🤖 MEMORY CHATBOT DEMO - CLI VERSION")
    print("Chatbot thông minh với bộ nhớ lâu dài")
    print("Sử dụng Google Gemini làm core")
    print("=" * 60)

def setup_api_key():
    """Thiết lập API key"""
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n⚠️  Chưa có Google API Key trong environment")
        api_key = input("Nhập Google API Key: ").strip()
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            print("✅ Đã thiết lập API key")
        else:
            print("❌ Không thể tiếp tục mà không có API key")
            print("Lấy API key tại: https://makersuite.google.com/app/apikey")
            return False
    else:
        print("✅ Đã có Google API Key")
    return True

def get_user_info():
    """Lấy thông tin người dùng"""
    print("\n📝 Thông tin người dùng:")
    user_id = input("User ID (mặc định: demo_user): ").strip() or "demo_user"
    session_id = input("Session ID (mặc định: default): ").strip() or "default"
    return user_id, session_id

def show_menu():
    """Hiển thị menu"""
    print("\n" + "─" * 50)
    print("MENU:")
    print("1. Chat với bot")
    print("2. Xem thông tin memory")
    print("3. Tìm kiếm trong memory")
    print("4. Xóa memory session")
    print("5. Xóa tất cả memory")
    print("6. Thoát")
    print("─" * 50)

def chat_mode(chatbot):
    """Chế độ chat"""
    print("\n💬 CHẾ độ CHAT")
    print("Gõ 'exit' để quay lại menu chính")
    print("─" * 30)
    
    while True:
        try:
            user_input = input("\n👤 Bạn: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'back']:
                break
            
            if not user_input:
                continue
            
            print("🤖 Bot: ", end="")
            response = chatbot.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\nQuay lại menu chính...")
            break
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")

def show_memory_info(chatbot):
    """Hiển thị thông tin memory"""
    try:
        print("\n📊 THÔNG TIN MEMORY")
        print("─" * 30)
        
        memory_info = chatbot.get_memory_summary()
        
        print(f"User ID: {memory_info['user_id']}")
        print(f"Session ID: {memory_info['session_id']}")
        print(f"Tổng số tin nhắn: {memory_info['total_messages']}")
        print(f"Tổng số entities: {memory_info['total_entities']}")
        print(f"Tổng số vector memories: {memory_info['total_vector_memories']}")
        
        if memory_info['entities']:
            print("\n📋 THÔNG TIN CÁ NHÂN:")
            for entity, facts in memory_info['entities'].items():
                print(f"  {entity}: {', '.join(facts)}")
        
        if memory_info['conversation_summary']:
            print("\n💭 TÓM TẮT CUỘC TRÒ CHUYỆN:")
            print(memory_info['conversation_summary'][:500] + "..." if len(memory_info['conversation_summary']) > 500 else memory_info['conversation_summary'])
        
    except Exception as e:
        print(f"❌ Lỗi khi lấy thông tin memory: {e}")

def search_memory(chatbot):
    """Tìm kiếm trong memory"""
    try:
        query = input("\n🔍 Nhập từ khóa tìm kiếm: ").strip()
        if not query:
            return
        
        print("Đang tìm kiếm...")
        results = chatbot.search_memory(query)
        
        print("\n📋 KẾT QUẢ TÌM KIẾM:")
        print("─" * 30)
        print(results)
        
    except Exception as e:
        print(f"❌ Lỗi khi tìm kiếm: {e}")

def clear_session_memory(chatbot):
    """Xóa memory session"""
    confirm = input("\n⚠️  Bạn có chắc muốn xóa memory session? (y/N): ").strip().lower()
    if confirm == 'y':
        try:
            chatbot.clear_session()
            print("✅ Đã xóa memory session")
        except Exception as e:
            print(f"❌ Lỗi khi xóa memory: {e}")

def clear_all_memory(chatbot):
    """Xóa tất cả memory"""
    confirm = input("\n⚠️  Bạn có chắc muốn xóa TẤT CẢ memory? (y/N): ").strip().lower()
    if confirm == 'y':
        try:
            chatbot.clear_all_memory()
            print("✅ Đã xóa tất cả memory")
        except Exception as e:
            print(f"❌ Lỗi khi xóa memory: {e}")

def main():
    """Hàm main"""
    print_banner()
    
    # Thiết lập API key
    if not setup_api_key():
        return
    
    # Lấy thông tin người dùng
    user_id, session_id = get_user_info()
    
    # Khởi tạo chatbot
    try:
        print(f"\n🚀 Đang khởi tạo chatbot cho user '{user_id}', session '{session_id}'...")
        chatbot = MemoryChatbot(user_id, session_id)
        print("✅ Khởi tạo thành công!")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo chatbot: {e}")
        return
    
    # Menu chính
    while True:
        try:
            show_menu()
            choice = input("Chọn (1-6): ").strip()
            
            if choice == '1':
                chat_mode(chatbot)
            elif choice == '2':
                show_memory_info(chatbot)
            elif choice == '3':
                search_memory(chatbot)
            elif choice == '4':
                clear_session_memory(chatbot)
            elif choice == '5':
                clear_all_memory(chatbot)
            elif choice == '6':
                print("\n👋 Tạm biệt!")
                break
            else:
                print("❌ Lựa chọn không hợp lệ")
                
        except KeyboardInterrupt:
            print("\n\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()