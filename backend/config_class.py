from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class EndpointInfo(BaseModel):
    """
    Modèle pour stocker les informations sur un endpoint API.

    Attributs:
        path: Chemin de l'endpoint (ex: "/users/{id}")
        method: Méthode HTTP (GET, POST, etc.)
        parameters: Liste des paramètres avec nom et type
        return_type: Type de retour de l'endpoint
        description: Description de la fonction de l'endpoint
    """

    path: str = Field(description="Chemin de l'endpoint")
    method: str = Field(description="Méthode HTTP (GET, POST, etc.)")
    parameters: List[Dict[str, str]] = Field(
        description="Paramètres de l'endpoint", default_factory=list
    )
    return_type: str = Field(description="Type de retour de l'endpoint")
    description: str = Field(description="Description de l'endpoint")


class ApiAnalysis(BaseModel):
    """
    Modèle pour stocker l'analyse complète d'un contrôleur API.

    Attributs:
        controller_name: Nom du contrôleur analysé
        base_path: Chemin de base pour tous les endpoints
        endpoints: Liste des endpoints détectés
        model_classes: Classes de modèle utilisées dans l'API
        dependencies: Dépendances Java détectées
        authentication_type: Type d'authentification si détecté
    """

    controller_name: str = Field(description="Nom du contrôleur API")
    base_path: str = Field(description="Chemin de base du contrôleur")
    endpoints: List[EndpointInfo] = Field(description="Liste des endpoints détectés")
    model_classes: List[str] = Field(
        description="Classes de modèle utilisées", default_factory=list
    )
    dependencies: List[str] = Field(
        description="Dépendances Java détectées", default_factory=list
    )
    authentication_type: Optional[str] = Field(
        description="Type d'authentification si détecté", default=None
    )
