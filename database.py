from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os


# URL de connexion à PostgreSQL
# Remplacez les valeurs par vos informations de connexion
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL_RFC_CALL")

# Créer un moteur de connexion
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Créer une session locale pour interagir avec la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Déclarer la base pour les modèles
Base = declarative_base()

# Fonction pour obtenir une session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()