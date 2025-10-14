from db.repositories.base_repository import BaseRepository
from db.models.test_execution import TestExecution


class TestExecutionRepository(BaseRepository[TestExecution]):
    def __init__(self, mongo_uri: str = None):
        super().__init__(TestExecution, mongo_uri)
