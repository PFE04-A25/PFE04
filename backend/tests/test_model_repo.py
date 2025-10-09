import pytest
from bson import ObjectId
from db.repositories.model_repository import ModelRepository

def test_model_crud():
    repo = ModelRepository()
    # Clean collection
    repo.collection.delete_many({})

    # Insert
    model_data = {"name": "MyModel", "description": "Test model"}
    inserted_id = repo.insert_one(model_data)
    assert inserted_id is not None

    # Find
    found = repo.find_by_id(inserted_id)
    assert found["name"] == "MyModel"

    # Update
    repo.update({"_id": inserted_id}, {"$set": {"name": "Updated"}})
    updated = repo.find_by_id(inserted_id)
    assert updated["name"] == "Updated"

    # Delete
    deleted_count = repo.delete({"_id": inserted_id})
    assert deleted_count == 1

    # Confirm deletion
    assert repo.find_by_id(inserted_id) is None
