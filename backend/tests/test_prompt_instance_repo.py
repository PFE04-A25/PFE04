from db.repositories.prompt_instance_repository import PromptInstanceRepository
from db.models.prompt_instance import PromptInstance

def test_prompt_instance_crud():
    repo = PromptInstanceRepository()
    repo.collection.delete_many({})

    instance = PromptInstance(template_id="template123", variables={"x": "1"}, final_prompt="final prompt text")
    created = repo.create(instance)
    assert created.id is not None

    found = repo.find_by_id(created.id)
    assert found.template_id == "template123"

    repo.update(created.id, {"final_prompt": "Updated prompt"})
    updated = repo.find_by_id(created.id)
    assert updated.final_prompt == "Updated prompt"

    deleted = repo.delete(created.id)
    assert deleted is True
    assert repo.find_by_id(created.id) is None
