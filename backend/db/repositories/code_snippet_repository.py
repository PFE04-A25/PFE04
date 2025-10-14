from db.repositories.base_repository import BaseRepository
from db.models.code_snippet import CodeSnippet


class CodeSnippetRepository(BaseRepository[CodeSnippet]):

    def __init__(self, mongo_uri: str = None):
        # Appelle le constructeur de BaseRepository avec la classe CodeSnippet
        super().__init__(CodeSnippet, mongo_uri)

    def find_by_language(self, language: str):
        return self.find_all({"language": language})

    def find_by_hash(self, code_hash: str):
        """
        Recherche un snippet à partir de son empreinte (hash unique).
        Cela permet d'éviter les doublons dans la base.
        """
        results = self.find_all({"hash": code_hash})
        return results[0] if results else None

    def search_by_keyword(self, keyword: str):
        regex_filter = {"source_code": {"$regex": keyword, "$options": "i"}}
        return self.find_all(regex_filter)
