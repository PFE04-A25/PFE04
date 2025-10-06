# db/models/base_model.py
from datetime import datetime
from typing import Dict, Any, Optional
from pymongo import MongoClient

class BaseModel:
    collection_name: str = None
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('_id', None)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB"""
        data = self.__dict__.copy()
        if data.get('id'):
            data['_id'] = data.pop('id')
        return data
