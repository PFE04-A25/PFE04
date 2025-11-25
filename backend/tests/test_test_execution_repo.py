from db.repositories.test_execution_repository import TestExecutionRepository
from db.models.test_execution import TestExecution

def test_test_execution_crud():
    repo = TestExecutionRepository()
    repo.collection.delete_many({})

    # CREATE
    exec_data = TestExecution(
        test_generation_id="tg123",
        success_count=5,
        failure_count=2,
        execution_time=2.3,
        coverage=85,
        logs="Run complete"
    )
    created = repo.create(exec_data)
    assert created.id is not None

    # READ
    found = repo.find_by_id(created.id)
    assert found.test_generation_id == "tg123"
    assert found.success_count == 5

    # UPDATE
    repo.update(created.id, {"coverage": 90})
    updated = repo.find_by_id(created.id)
    assert updated.coverage == 90

    # DELETE
    deleted = repo.delete(created.id)
    assert deleted is True
    assert repo.find_by_id(created.id) is None
