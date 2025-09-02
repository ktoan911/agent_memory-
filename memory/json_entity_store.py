"""
JSON-based Entity Store để lưu trữ thông tin thực thể của người dùng
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from langchain.schema import BaseEntityStore
from config import ENTITIES_DIR


class JSONEntityStore(BaseEntityStore):
    """
    Entity Store sử dụng file JSON để lưu trữ thông tin thực thể
    Mỗi user_id sẽ có một file JSON riêng
    """
    
    def __init__(self, user_id: str):
        """
        Khởi tạo JSONEntityStore cho một user cụ thể
        
        Args:
            user_id: ID của người dùng
        """
        self.user_id = user_id
        self.file_path = ENTITIES_DIR / f"{user_id}_entities.json"
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Đảm bảo file JSON tồn tại"""
        if not self.file_path.exists():
            self.file_path.write_text(json.dumps({}))
    
    def _load_entities(self) -> Dict[str, List[str]]:
        """Tải entities từ file JSON"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_entities(self, entities: Dict[str, List[str]]) -> None:
        """Lưu entities vào file JSON"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)
    
    def get(self, entity_key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Lấy thông tin của một entity
        
        Args:
            entity_key: Khóa của entity
            default: Giá trị mặc định nếu không tìm thấy
            
        Returns:
            Thông tin của entity hoặc default
        """
        entities = self._load_entities()
        facts = entities.get(entity_key, [])
        return facts[-1] if facts else default
    
    def set(self, entity_key: str, entity_value: str) -> None:
        """
        Đặt thông tin cho một entity
        
        Args:
            entity_key: Khóa của entity
            entity_value: Giá trị của entity
        """
        entities = self._load_entities()
        if entity_key not in entities:
            entities[entity_key] = []
        
        # Tránh lưu trùng lặp
        if entity_value not in entities[entity_key]:
            entities[entity_key].append(entity_value)
        
        self._save_entities(entities)
    
    def delete(self, entity_key: str) -> None:
        """
        Xóa một entity
        
        Args:
            entity_key: Khóa của entity cần xóa
        """
        entities = self._load_entities()
        if entity_key in entities:
            del entities[entity_key]
            self._save_entities(entities)
    
    def exists(self, entity_key: str) -> bool:
        """
        Kiểm tra xem entity có tồn tại không
        
        Args:
            entity_key: Khóa của entity
            
        Returns:
            True nếu entity tồn tại
        """
        entities = self._load_entities()
        return entity_key in entities and len(entities[entity_key]) > 0
    
    def clear(self) -> None:
        """Xóa tất cả entities"""
        self._save_entities({})
    
    def get_all_entities(self) -> Dict[str, List[str]]:
        """
        Lấy tất cả entities
        
        Returns:
            Dictionary chứa tất cả entities
        """
        return self._load_entities()
    
    def get_entity_facts(self, entity_key: str) -> List[str]:
        """
        Lấy tất cả facts của một entity
        
        Args:
            entity_key: Khóa của entity
            
        Returns:
            Danh sách các facts
        """
        entities = self._load_entities()
        return entities.get(entity_key, [])
    
    def add_fact(self, entity_key: str, fact: str) -> None:
        """
        Thêm một fact mới cho entity
        
        Args:
            entity_key: Khóa của entity
            fact: Fact mới cần thêm
        """
        entities = self._load_entities()
        if entity_key not in entities:
            entities[entity_key] = []
        
        # Tránh lưu trùng lặp
        if fact not in entities[entity_key]:
            entities[entity_key].append(fact)
        
        self._save_entities(entities)
    
    def remove_fact(self, entity_key: str, fact: str) -> None:
        """
        Xóa một fact khỏi entity
        
        Args:
            entity_key: Khóa của entity
            fact: Fact cần xóa
        """
        entities = self._load_entities()
        if entity_key in entities and fact in entities[entity_key]:
            entities[entity_key].remove(fact)
            if not entities[entity_key]:  # Xóa entity nếu không còn fact nào
                del entities[entity_key]
            self._save_entities(entities)