from db.repositories.base_repository import BaseRepository
from db.models.test_generation import TestGeneration


class TestGenerationRepository(BaseRepository[TestGeneration]):
    """
    Repository pour interagir avec la collection 'test_generations'.
    Cette collection relie un code source, un prompt et un modèle IA à un test généré.
    """

    def __init__(self, mongo_uri: str = None):
        # Initialise la collection 'test_generations'
        super().__init__(TestGeneration, mongo_uri)