from db.repositories.test_generation_repository import TestGenerationRepository
from db.models.test_generation import TestGeneration

def test_test_generation_crud():
    repo = TestGenerationRepository()
    repo.collection.delete_many({})

    # CREATE
    gen = TestGeneration(
        model_id="m123",
        prompt_instance_id="pi123",
        code_snippet_id="cs123",
        generated_test="def test_example(): assert True",
        token_usage={"input": 10, "output": 20},
        generation_time=1.5,
    )
    created = repo.create(gen)
    assert created.id is not None

    # READ
    found = repo.find_by_id(created.id)
    assert found.model_id == "m123"

    # UPDATE
    repo.update(created.id, {"generated_test": "def test_updated(): assert False"})
    updated = repo.find_by_id(created.id)
    assert "updated" in updated.generated_test

    # DELETE
    deleted = repo.delete(created.id)
    assert deleted is True
    assert repo.find_by_id(created.id) is None
