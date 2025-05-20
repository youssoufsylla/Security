from pydantic import BaseModel
from datetime import datetime


# Schéma pour la réponse de l'utilisateur
class UserResponse(BaseModel):
    id: int
    agence_id: int
    nom: str
    prenom: str
    email: str
    telephone: str
    role: str
    derniere_connexion: datetime
    derniere_deconnexion: datetime

    class Config:
        from_attributes = True  # Anciennement `orm_mode = True` dans Pydantic v1
        
# Schéma pour les données du token
class TokenData(BaseModel):
    user_id: str
    role: str

