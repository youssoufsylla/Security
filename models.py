from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from database import Base





##===============================================================##
##                       Utilisateurs                            ##
##===============================================================##
class User(Base):
    __tablename__ = "users"
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    agence_id = Column(
        Integer,
        ForeignKey('agences.id'),
        nullable=False
    )
    nom = Column(
        String,
        nullable=False
    )
    prenom = Column(
        String,
        nullable=False
    )
    email = Column(
        String,
        nullable=False
    )
    password = Column(
        String,
        nullable=False
    )
    telephone = Column(
        String,
        nullable=False
    )
    role = Column(
        String,
        nullable=False
    )
    derniere_connexion = Column(
        DateTime,
        nullable=False
    )
    derniere_deconnexion = Column(
        DateTime,
        nullable=False
    )
    # Relation pour les commandes créées par l'utilisateur
    commandes_crees = relationship(
        "Commande",
        foreign_keys="Commande.createur_id",
        backref="createur"  # backref pour accéder à l'utilisateur qui a créé la commande
    )
    # Relation pour les commandes reçues par l'utilisateur
    commandes_recues = relationship(
        "Commande",
        foreign_keys="Commande.recepteur_id",
        backref="recepteur"  # backref pour accéder à l'utilisateur qui a reçu la commande
    )
    session = relationship(
        "UserSession",
        backref = "user"
    )

##===============================================================##
##                         Session                               ##
##===============================================================##
class UserSession(Base):
    __tablename__ = "sessions"

  
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    user_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
    )
    heure_connexion = Column(
        DateTime,
        nullable=False
    )
    heure_deconnexion = Column(
        DateTime,
        nullable=True
    )
    nombre_commande_creer = Column(
        Integer,
        nullable=True
    )
    nombre_commande_traiter = Column(
        Integer,
        nullable=True
    )
    
##===============================================================##
##                           Agence                              ##
##===============================================================##
class Agence(Base):
    __tablename__ = "agences"
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    nom = Column(
        String,
        nullable=False
    )
    adresse = Column(
        String,
        nullable=False
    )
    telephone = Column(
        String,
        nullable=False
    )
    est_active = Column(
        Boolean,
        nullable=False
    )
    user = relationship(
        "User",
        backref = "agence"
    )
    tablette = relationship(
        "Tablette",
        backref = "tablette_agence"
    )
    commande = relationship(
        "Commande",
        backref = "commande_agence"
    )

##===============================================================##
##                            Tablette                           ##
##===============================================================##
class Tablette(Base):
    __tablename__ = "tablettes"
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    numero_serie = Column(
        String,
        nullable=False,
        unique=True
    )
    agence_id = Column(
        Integer,
        ForeignKey('agences.id'),
        nullable=False
    )
    est_active = Column(
        Boolean,
        nullable=False
    )
    derniere_syncro = Column(
        DateTime,
        nullable=False
    )
    firebase_token = Column(
        String,
        nullable=True
    )

##===============================================================##
##                       Clients                                 ##
##===============================================================##
class Client(Base):
    __tablename__ = "clients"
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    nom = Column(
        String,
        nullable=False
    )
    prenom = Column(
        String,
        nullable=False
    )
    telephone = Column(
        String,
        nullable=False,
        unique=True
    )
    adresse = Column(
        String,
        nullable=False,
    )
    date_creation = Column(
        DateTime,
        nullable=False,
    )
    commande = relationship(
        "Commande",
        backref = "client"
    )
##===============================================================##
##                           Commande                            ##
##===============================================================##
class Commande(Base):
    __tablename__ = "commandes"
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    client_id = Column(
        Integer,
        ForeignKey('clients.id'),
        nullable=False
    )
    agence_id = Column(
        Integer,
        ForeignKey('agences.id'),
        nullable=False
    )
    createur_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
    )
    recepteur_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
    )
    date_creation = Column(
        DateTime,
        nullable=False
    )
    date_reception = Column(
        DateTime,
        nullable=True
    )
    status = Column(
        String,
        nullable=False
    )
    montant_total = Column(
        Integer,
        nullable=False
    )
    notes = Column(
        String,
        nullable=False
    )
    lignecommande = relationship(
        "LigneCommande",
        backref = "commande"
    )  
##===============================================================##
##                         Ligne de Commande                     ##
##===============================================================##
class LigneCommande(Base):
    __tablename__ = "ligne_commandes"
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    commande_id = Column(
        Integer,
        ForeignKey('commandes.id'),
        nullable=False
    )
    nom_article = Column(
        String,
        nullable=False
    )
    reference_article = Column(
        String,
        nullable=False
    )
    quantite= Column(
        Integer,
        nullable=False
    )
    prix_unitaire= Column(
        Integer,
        nullable=False
    )
    sous_totaux= Column(
        Integer,
        nullable=False
    )
    

   