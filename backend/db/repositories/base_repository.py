import os
from typing import List, Dict, Any, Optional, TypeVar, Generic, Type
from pymongo import MongoClient
from bson import ObjectId
import datetime

from db.models.base_model import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    def __init__(
        self,
        model_class: Type[T],
        mongo_uri: str = None,
    ):
        self.model_class = model_class
        mongo_uri = mongo_uri or os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
        self.client = MongoClient(mongo_uri)
        self.db = self.client.test_generator
        self.collection = self.db[model_class.collection_name]

    def create(self, model: T) -> T:
        """Create a new document"""
        result = self.collection.insert_one(model.to_dict())
        model.id = result.inserted_id
        return model

    def find_by_id(self, id: str) -> Optional[T]:
        """Find document by ID"""
        data = self.collection.find_one({"_id": ObjectId(id)})
        if data:
            return self.model_class(**data)
        return None

    def find_all(self, filter_dict: Dict = None) -> List[T]:
        """Find all documents matching filter"""
        filter_dict = filter_dict or {}
        cursor = self.collection.find(filter_dict)
        return [self.model_class(**doc) for doc in cursor]

    def update(self, id: str, update_dict: Dict) -> Optional[T]:
        """Update document by ID"""
        update_dict["updated_at"] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_dict}
        )
        if result.modified_count:
            return self.find_by_id(id)
        return None

    def delete(self, id: str) -> bool:
        """Delete document by ID"""
        result = self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
