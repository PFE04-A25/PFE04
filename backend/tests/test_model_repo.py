from db.repositories.model_repository import ModelRepository
from db.models.model_info import ModelInfo

def test_model_crud():
    repo = ModelRepository()
    repo.collection.delete_many({})

    model_data = ModelInfo(name="MyModel", description="Test model")
    created_model = repo.create(model_data)
    assert created_model.id is not None

    found = repo.find_by_id(created_model.id)
    assert found.name == "MyModel"

    repo.update(created_model.id, {"name": "Updated"})
    updated = repo.find_by_id(created_model.id)
    assert updated.name == "Updated"

    deleted = repo.delete(created_model.id)
    assert deleted is True

    assert repo.find_by_id(created_model.id) is None
