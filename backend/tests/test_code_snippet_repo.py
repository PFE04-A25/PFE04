from db.repositories.code_snippet_repository import CodeSnippetRepository
from db.models.code_snippet import CodeSnippet


def test_code_snippet_crud():
    repo = CodeSnippetRepository()
    repo.collection.delete_many({})

    snippet = CodeSnippet(language="python", source_code="print('Hello')", hash="abc123")
    created_snippet = repo.create(snippet)
    assert created_snippet.id is not None

    found = repo.find_by_id(created_snippet.id)
    assert found.language == "python"
    assert "print" in found.source_code

    repo.update(created_snippet.id, {"source_code": "print('Updated')"})
    updated = repo.find_by_id(created_snippet.id)
    assert "Updated" in updated.source_code

    results = repo.find_by_language("python")
    assert any(s.hash == "abc123" for s in results)

    found_by_hash = repo.find_by_hash("abc123")
    assert found_by_hash is not None
    assert found_by_hash.language == "python"

    search_results = repo.search_by_keyword("updated")
    assert len(search_results) >= 1
    assert "Updated" in search_results[0].source_code

    deleted = repo.delete(created_snippet.id)
    assert deleted is True

    assert repo.find_by_id(created_snippet.id) is None
