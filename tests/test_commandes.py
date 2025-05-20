# tests/test_commandes.py
import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, get_db, engine
from sqlalchemy.orm import Session
from models import User, Agence, Client, Commande
import json
from datetime import datetime

client = TestClient(app)

# Fonction de configuration pour créer une base de données de test
@pytest.fixture(scope="function")
def test_db():
    # Créer les tables
    Base.metadata.create_all(bind=engine)
    
    # Créer une session
    db = next(get_db())
    
    # Créer des données de test
    agence = Agence(
        nom="Agence Test",
        adresse="123 Test Street",
        telephone="+123456789",
        est_active=True
    )
    db.add(agence)
    db.commit()
    
    user = User(
        agence_id=agence.id,
        nom="Test",
        prenom="User",
        email="test@example.com",
        password="$2b$12$HxIfz7UO.yUJCq4VrQWN8OTfOc6QD1yR9.YcB.hNjVVsmHX.Hd1fC",  # "testpassword"
        telephone="+123456789",
        role="admin",
        derniere_connexion=datetime.utcnow(),
        derniere_deconnexion=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    
    client = Client(
        nom="Client",
        prenom="Test",
        telephone="+987654321",
        adresse="456 Client Avenue",
        date_creation=datetime.utcnow()
    )
    db.add(client)
    db.commit()
    
    yield db
    
    # Nettoyer après les tests
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_commande(test_db):
    # Obtenir l'ID de l'utilisateur, de l'agence et du client créés dans le fixture
    user = test_db.query(User).first()
    agence = test_db.query(Agence).first()
    client_db = test_db.query(Client).first()
    
    # Créer les données de la commande
    commande_data = {
        "client_id": client_db.id,
        "agence_id": agence.id,
        "createur_id": user.id,
        "recepteur_id": user.id,
        "notes": "Commande de test",
        "lignes_commandes": [
            {
                "nom_article": "Article Test",
                "reference_article": "REF123",
                "quantite": 2,
                "prix_unitaire": 1000
            }
        ]
    }
    
    # Envoyer la requête pour créer une commande
    response = client.post(
        "/commande",
        json=commande_data,
        headers={"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}  # Token JWT valide
    )
    
    # Vérifier que la réponse est correcte
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == client_db.id
    assert data["agence_id"] == agence.id
    assert data["montant_total"] == 2000  # 2 * 1000
    
    # Vérifier que la commande a été créée dans la base de données
    commande = test_db.query(Commande).filter(Commande.id == data["id"]).first()
    assert commande is not None
    assert commande.montant_total == 2000