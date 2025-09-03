"""
Cấu hình cho Agent Memory System
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
CHAT_DBNAME = os.getenv("CHAT_DBNAME", "chat_db")
CHAT_COL_ENTITIES = os.getenv("CHAT_COL_ENTITIES", "entities")
CHAT_COL_HISTORY = os.getenv("CHAT_COL_HISTORY", "history")
CHAT_COL_VECTOR = os.getenv("CHAT_COL_VECTOR", "vector")

# Cấu hình Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-pro")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Cấu hình đường dẫn lưu trữ
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
ENTITIES_DIR = Path(os.getenv("ENTITIES_DIR", "./data/entities"))
CHAT_HISTORY_DIR = Path(os.getenv("CHAT_HISTORY_DIR", "./data/chat_history"))
VECTOR_STORE_DIR = Path(os.getenv("VECTOR_STORE_DIR", "./data/vector_store"))

# Tạo các thư mục nếu chưa tồn tại
for directory in [DATA_DIR, ENTITIES_DIR, CHAT_HISTORY_DIR, VECTOR_STORE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Cấu hình vector store
VECTOR_DIMENSION = 1536  # OpenAI embedding dimension
MAX_RETRIEVED_MEMORIES = 5  # Số lượng memory tối đa được retrieve

# Cấu hình entity memory
MAX_ENTITY_FACTS = 50  # Số lượng facts tối đa cho mỗi entity
