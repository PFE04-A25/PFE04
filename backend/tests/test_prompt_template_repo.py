from db.repositories.prompt_template_repository import PromptTemplateRepository
from db.models.prompt_template import PromptTemplate

def test_prompt_template_crud():
    repo = PromptTemplateRepository()
    repo.collection.delete_many({})

    template = PromptTemplate(name="Unit Test Template", description="Desc", template_text="Given code, generate tests")
    created = repo.create(template)
    assert created.id is not None

    found = repo.find_by_id(created.id)
    assert found.name == "Unit Test Template"

    repo.update(created.id, {"description": "Updated Desc"})
    updated = repo.find_by_id(created.id)
    assert updated.description == "Updated Desc"

    deleted = repo.delete(created.id)
    assert deleted is True
    assert repo.find_by_id(created.id) is None
