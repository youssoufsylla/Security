from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from datetime import datetime
from typing import List, Optional



##===============================================================##
##         Schema pour la création des utilisateur               ##
##===============================================================##
# Schéma pour la création d'un utilisateur
class UserCreate(BaseModel):
    agence_id: int
    nom: str = Field(..., min_length=2, max_length=50)
    prenom: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    telephone: str = Field(..., min_length=8, max_length=15)
    role: str = Field(..., pattern='^(admin|agent_centre_appel|agent_agence)$')
    
    @field_validator('password')
    def password_complexe(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une lettre majuscule')
        if not re.search(r'[a-z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une lettre minuscule')
        if not re.search(r'[0-9]', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        return v
        
    @field_validator('telephone')
    def telephone_valide(cls, v):
        if not re.match(r'^\+?[0-9]+$', v):
            raise ValueError('Le numéro de téléphone doit contenir uniquement des chiffres, avec éventuellement un + au début')
        return v

##===============================================================##
##                    Authentificaiton                           ##
##===============================================================##
# Schéma pour la demande de connexion
class LoginRequest(BaseModel):
    email: str
    password: str

# Schéma pour la réponse de connexion
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: str

# Schéma pour les données du token
class TokenData(BaseModel):
    user_id: str
    role: str

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

##===============================================================##
##                 Schema pour les Agences                       ##
##===============================================================##
class AgenceCreate(BaseModel):
    nom: str
    adresse: str
    telephone: str
    est_active: bool

class AgenceResponse(BaseModel):
    id: int
    nom: str
    adresse: str
    telephone: str
    est_active: bool

    class Config:
        from_attributes = True 
##===============================================================##
##                 Schema pour les Clients                       ##
##===============================================================##
class ClientCreate(BaseModel):
    nom: str
    prenom: str
    telephone: str
    adresse: str

class ClientResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    telephone: str
    adresse: str
    date_creation: datetime

    class Config:
        from_attributes = True  
##===============================================================##
##                 Schema pour les Commande                      ##
##===============================================================##
# Schéma pour une ligne de commande
class LigneCommandeCreate(BaseModel):
    nom_article: str
    reference_article: str
    quantite: int
    prix_unitaire: int

# Schéma pour la soumission d'une commande
class CommandeCreate(BaseModel):
    client_id: int
    agence_id: int
    createur_id: int
    recepteur_id: int
    notes: str
    lignes_commandes: List[LigneCommandeCreate]
    
    model_config = {
        "json_schema_extra" : {
            "example": {
                "client_id": 1,
                "agence_id": 2,
                "createur_id": 3,
                "recepteur_id": 4,
                "notes": "Livraison prioritaire",
                "lignes_commandes": [
                    {
                        "nom_article": "Poulet Frit",
                        "reference_article": "PF-001",
                        "quantite": 2,
                        "prix_unitaire": 5000
                    },
                    {
                        "nom_article": "Frites",
                        "reference_article": "FRI-001",
                        "quantite": 1,
                        "prix_unitaire": 2000
                    }
                ]
            }
        }
    } # type: ignore
# Schéma pour les détails de la commande
class LigneCommandeDetail(BaseModel):
    id: int
    nom_article: str
    reference_article: str
    quantite: int
    prix_unitaire: int
    sous_total: int

class CommandeDetailResponse(BaseModel):
    id: int
    client_id: int
    client_nom: str
    client_telephone: str
    client_adresse: str
    agence_id: int
    createur_id: int
    recepteur_id: int
    date_creation: datetime
    date_reception: Optional[datetime]
    statut: str
    montant_total: int
    notes: str
    lignes_commande: List[LigneCommandeDetail]
    
    class Config:
        from_attributes = True
# Schéma pour la réponse de la commande
class CommandeResponse(BaseModel):
    id: int
    client_id: int
    agence_id: int
    createur_id: int
    recepteur_id: int
    date_creation: datetime
    status: str
    montant_total: int
    notes: str

    class Config:
        from_attributes = True

class CommandeUpdate(BaseModel):
    recepteur_id: int
    status: Optional[str] = None
    notes: Optional[str] = None
##===============================================================##
##                 Schema pour les tablette                      ##
##===============================================================##
class TabletteConfig(BaseModel):
    agence_id: int
    numero_serie: str


# Schéma pour la tablette
class TabletteResponse(BaseModel):
    id: int
    numero_serie: str
    agence_id: int
    est_active: bool
    derniere_syncro: datetime

    class Config:
        from_attributes = True

# Schéma pour la mise à jour du statut
class StatutUpdate(BaseModel):
    statut: str

##===============================================================##
##                 Schema pour les tablette                      ##
##===============================================================##
class SessionBase(BaseModel):
    user_id: int
    heure_connexion: datetime
    heure_deconnexion: Optional[datetime] = None
    nombre_commande_creer: Optional[int] = None
    nombre_commande_traiter: Optional[int] = None

    class Config:
        orm_mode = True

##===============================================================##
##                 Schema pour Firebase Token                    ##
##===============================================================##
class FirebaseTokenRegister(BaseModel):
    token: str


