from fastapi import Depends, HTTPException, File, Form, APIRouter, status, Request,Query
from fastapi.param_functions import Body
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database import *
from typing import List, Optional
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from datetime import datetime
import uuid
from models import *
from utiles import *
from logger import *
from . import schemas
from .firebase_service import firebase_service
  # Import relatif correct

router = APIRouter(
   #prefix="/back_office",
) 


##===============================================================================##
#     Initialiser le service de notification (à ajouter dans votre router.py)    ##
##===============================================================================## 
notification_service = None




##===============================================================================##
##                            AUTHENTIFICATION                                   ##
##===============================================================================##   
##===============================================================##
##           Connecter un Utilisateur et generer un Token        ##
##===============================================================##
@router.post("/login", response_model=schemas.LoginResponse, tags=["Authentication"])
def login(user_access: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Vérification que l'identifiant et le mot de passe sont fournis
   if not user_access.username or not user_access.password:
      raise HTTPException(
         status_code=status.HTTP_400_BAD_REQUEST,
         detail="L'identifiant et le mot de passe sont requis"
      )

    # Récupération de l'utilisateur depuis la base de données
   user = db.query(User).filter(User.email == user_access.username).first()
   if not user:
      raise HTTPException(
         status_code=status.HTTP_401_UNAUTHORIZED,
         detail="Les accès fournis sont incorrects"
      )
    
    # Vérification du mot de passe
   if not verify_password(user_access.password, user.password):
      raise HTTPException(
         status_code=status.HTTP_401_UNAUTHORIZED,
         detail="Le mot de passe fourni n'est pas le bon"
      )

   # Création du token JWT avec l'ID et le rôle de l'utilisateur
   access_token = create_access_token(data={"user_id": user.id, "role": user.role})

   # Retourne la réponse avec le token, le type de token, l'ID de l'utilisateur et son rôle
   return schemas.LoginResponse(
      access_token=access_token,
      token_type="bearer",
      user_id=user.id,
      role=user.role
   )  

##===============================================================##
##         Récupérer les informations de l'utilisateur actuel    ##
##===============================================================##
@router.get("/current_user", response_model=schemas.UserResponse, tags=["Authentication"])
def read_users_me(
   current_user: schemas.UserResponse = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """
   Endpoint pour récupérer les informations de l'utilisateur actuel.
   """
   # Récupérer l'utilisateur actuel depuis la base de données
   user = db.query(User).filter(User.id == current_user.id).first()

   if user is None:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="Aucun utilisateur ne correspond à vos paramètres de recherche"
   )

   # Retourner les informations de l'utilisateur (sans le mot de passe)
   return schemas.UserResponse(
      id=user.id,
      agence_id=user.agence_id,
      nom=user.nom,
      prenom=user.prenom,
      email=user.email,
      telephone=user.telephone,
      role=user.role,
      derniere_connexion=user.derniere_connexion,
      derniere_deconnexion=user.derniere_deconnexion
   )

##===============================================================##
##         Récupérer des utilisateurs                            ##
##===============================================================##
@router.get("/utilisateurs", response_model=List[schemas.UserResponse], tags=["Utilisateurs"])
def get_utilisateurs(
   db: Session = Depends(get_db),
):
    """
    Endpoint pour récupérer la liste de tous les utilisateurs.
    """
    
    utilisateurs = db.query(User).all()
    
    return utilisateurs

##===============================================================##
##         Récupérer des utilisateurs                            ##
##===============================================================##
@router.post("/utilisateurs", response_model=schemas.UserResponse, tags=["Utilisateurs"])
def create_utilisateur(
    user_data: schemas.UserCreate,
    current_user: UserResponse = Depends(role_required(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Endpoint pour créer un nouvel utilisateur.
    """
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Hasher le mot de passe
    hashed_password = hash_password(user_data.password)
    
    # Créer le nouvel utilisateur
    new_user = User(
        agence_id=user_data.agence_id,
        nom=user_data.nom,
        prenom=user_data.prenom,
        email=user_data.email,
        password=hashed_password,
        telephone=user_data.telephone,
        role=user_data.role,
        derniere_connexion=datetime.utcnow(),
        derniere_deconnexion=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


##===============================================================##
##                       Créer une agence                        ##
##===============================================================##
@router.post("/agence", response_model=schemas.AgenceResponse, tags=["Agences"])
def create_agence(
   agence: schemas.AgenceCreate,
   db: Session = Depends(get_db)
):
   """
   Endpoint pour créer une nouvelle agence.
   """
   # Créer une nouvelle instance d'Agence
   db_agence = Agence(
      nom=agence.nom,
      adresse=agence.adresse,
      telephone=agence.telephone,
      est_active=agence.est_active
   )

   # Ajouter l'agence à la base de données
   db.add(db_agence)
   db.commit()
   db.refresh(db_agence)

   # Retourner l'agence créée
   return db_agence

##===============================================================##
##                   Récupérer la liste des agences              ##
##===============================================================##
@router.get("/agences", response_model=List[schemas.AgenceResponse], tags=["Agences"])
def get_agences(
    db: Session = Depends(get_db)
):
   """
   Endpoint pour récupérer la liste de toutes les agences.
   """
   # Récupérer toutes les agences depuis la base de données
   agences = db.query(Agence).all()

   # Si aucune agence n'est trouvée, retourner une erreur 404
   if not agences:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="Aucune agence trouvée"
   )

   # Retourner la liste des agences
   return agences

##===============================================================##
##                       Créer un client                         ##
##===============================================================##
@router.post("/client", response_model=schemas.ClientResponse, tags=["Clients"])
def create_client(
   client: schemas.ClientCreate,
   db: Session = Depends(get_db)
):
   """
   Endpoint pour créer un nouveau client.
   """
   # Vérifier si un client avec le même téléphone existe déjà
   existing_client = db.query(Client).filter(Client.telephone == client.telephone).first()
   if existing_client:
      raise HTTPException(
         status_code=status.HTTP_400_BAD_REQUEST,
         detail="Un client avec ce numéro de téléphone existe déjà"
      )

   # Créer une nouvelle instance de Client
   db_client = Client(
      nom=client.nom,
      prenom=client.prenom,
      telephone=client.telephone,
      adresse=client.adresse,
      date_creation=datetime.utcnow()  # Ajouter la date de création
   )

   # Ajouter le client à la base de données
   db.add(db_client)
   db.commit()
   db.refresh(db_client)

   # Retourner le client créé
   return db_client

##===============================================================##
##                   Récupérer un client par téléphone          ##
##===============================================================##
@router.get("/clients/{telephone}", response_model=schemas.ClientResponse, tags=["Clients"])
def get_client_by_phone(telephone: str, db: Session = Depends(get_db)):
   """
   Endpoint pour récupérer un client via son numéro de téléphone.
   """
   client = db.query(Client).filter(Client.telephone == telephone).first()
   if not client:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="Client non trouvé"
      )

   return client

##===============================================================##
##                      Soumettre une commande                   ##
##===============================================================##
""" @router.post("/commande", response_model=schemas.CommandeResponse, tags=["Commandes"])
async def submit_order(order: schemas.CommandeCreate, db: Session = Depends(get_db)):

   
   # Vérifier si le client existe
   client = db.query(Client).filter(Client.id == order.client_id).first()
   if not client:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="Client non trouvé"
      )

   # Création de la commande
   new_order = Commande(
      client_id=order.client_id,
      agence_id=order.agence_id,
      createur_id=order.createur_id,
      recepteur_id=order.recepteur_id,
      date_creation=datetime.utcnow(),
      date_reception=None,
      status="En attente",
      montant_total=0,  # Sera calculé après
      notes=order.notes
   )

   db.add(new_order)
   db.commit()
   db.refresh(new_order)

   total_montant = 0

   # Création des lignes de commande
   for item in order.lignes_commandes:
      new_line = LigneCommande(
         commande_id=new_order.id,
         nom_article=item.nom_article,
         reference_article=item.reference_article,
         quantite=item.quantite,
         prix_unitaire=item.prix_unitaire,
         sous_totaux=item.quantite * item.prix_unitaire
      )
      db.add(new_line)
      total_montant += new_line.sous_totaux

   # Mise à jour du montant total de la commande
   new_order.montant_total = total_montant
   db.commit()
   db.refresh(new_order)


   # Préparer les données de la commande pour la notification
   client_info = {
      "id": client.id,
      "nom": client.nom,
      "prenom": client.prenom,
      "telephone": client.telephone,
      "adresse": client.adresse
   }
   
   
   commande_data = {
         "id": new_order.id,
         "client": client_info,
         "montant_total": new_order.montant_total,
         "status": new_order.status,
         "date_creation": new_order.date_creation.isoformat(),
         "notes": new_order.notes
   }
   
   # Envoyer la notification
   if notification_service:
      await notification_service.notifier_nouvelle_commande(order.agence_id, commande_data)
   
   return new_order
 """
##===============================================================##
##                      Soumettre une commande                   ##
##===============================================================##
@router.post("/commande", response_model=schemas.CommandeResponse, tags=["Commandes"])
def submit_order(order: schemas.CommandeCreate, db: Session = Depends(get_db)):
   """
    Endpoint pour soumettre une nouvelle commande.
   """
   # Logique existante...
    
   # Création de la commande
   new_order = Commande(
      client_id=order.client_id,
      agence_id=order.agence_id,
      createur_id=order.createur_id,
      recepteur_id=order.recepteur_id,
      date_creation=datetime.utcnow(),
      date_reception=None,
      status="envoyée",  # Changement à 'envoyée' pour correspondre au flux de statut de l'app mobile
      montant_total=0,  # Sera calculé après
      notes=order.notes
   )

   db.add(new_order)
   db.commit()
   db.refresh(new_order)

   total_montant = 0

   # Création des lignes de commande...
    
   # Mise à jour du montant total de la commande
   new_order.montant_total = total_montant
   db.commit()
   db.refresh(new_order)
    
   # Récupérer les informations du client
   client = db.query(Client).filter(Client.id == order.client_id).first()
    
   # Envoyer une notification aux tablettes de l'agence
   try:
      # Données supplémentaires à inclure dans la notification
      notification_data = {
         "commande_id": str(new_order.id),
         "client_nom": f"{client.nom} {client.prenom}",
         "client_telephone": client.telephone,
         "montant_total": str(total_montant),
         "type": "nouvelle_commande"
      }
        
      firebase_service.send_notification_to_agency(
         agency_id=order.agence_id,
         title="Nouvelle commande !",
         body=f"Commande #{new_order.id} pour {client.nom} {client.prenom}",
         data=notification_data,
         db=db
      )
   except Exception as e:
      # Log l'erreur mais continue le processus
      logger.error(f"Erreur lors de l'envoi de la notification: {str(e)}")

   return new_order


##===============================================================##
##             Mettre à jour une commande                        ##
##===============================================================##
@router.put("/commandes/{commande_id}", response_model=schemas.CommandeResponse, tags=["Commandes"])
def mettre_a_jour_commande(
   commande_id: int,
   commande_update: schemas.CommandeUpdate,
   current_user: UserResponse = Depends(role_required(["agent_restaurant"])),
   db: Session = Depends(get_db)
):
   """
   Endpoint pour mettre à jour une commande existante.
   """
   # Récupérer la commande depuis la base de données
   commande = db.query(Commande).filter(Commande.id == commande_id).first()
   if not commande:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="Commande non trouvée"
      )

   # Mettre à jour les champs fournis
   if commande_update.status is not None:
      commande.status = commande_update.status
   if commande_update.notes is not None:
      commande.notes = commande_update.notes
 
   commande.recepteur_id = current_user.id
   # Ajoutez d'autres champs si nécessaire

   # Enregistrer les modifications dans la base de données
   db.commit()
   db.refresh(commande)

   # Retourner la commande mise à jour
   return commande

##===============================================================##
##        Récupérer les détails d'une commande spécifique.       ##
##===============================================================##
@router.get("/commandes/{commande_id}", response_model=schemas.CommandeDetailResponse, tags=["Commandes"])
def get_commande_details(
   commande_id: int,
   db: Session = Depends(get_db),
   current_user: UserResponse = Depends(get_current_user)
):
   """
   Endpoint pour récupérer les détails d'une commande spécifique.
   """
   # Récupérer la commande
   commande = db.query(Commande).filter(Commande.id == commande_id).first()
    
   if not commande:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="Commande non trouvée"
      )
    
   # Récupérer les informations du client
   client = db.query(Client).filter(Client.id == commande.client_id).first()
    
   # Récupérer les informations du récepteur
   recepteur = db.query(User).filter(User.id == commande.recepteur_id).first()
    
   # Récupérer les lignes de commande
   lignes = db.query(LigneCommande).filter(LigneCommande.commande_id == commande.id).all()
    
   # Construire l'objet de réponse
   commande_detail = {
      "id": commande.id,
      "client_id": commande.client_id,
      "client_nom": f"{client.prenom} {client.nom}" if client else "Client inconnu",
      "client_telephone": client.telephone if client else "",
      "client_adresse": client.adresse if client else "",
      "agence_id": commande.agence_id,
      "createur_id": commande.createur_id,
      "recepteur_id": commande.recepteur_id,
      "recepteur_nom": f"{recepteur.prenom} {recepteur.nom}" if recepteur else None,
      "date_creation": commande.date_creation,
      "date_reception": commande.date_reception,
      "statut": commande.status,
      "montant_total": commande.montant_total,
      "notes": commande.notes,
      "lignes_commande": [
         {
            "id": ligne.id,
            "nom_article": ligne.nom_article,
            "reference_article": ligne.reference_article,
            "quantite": ligne.quantite,
            "prix_unitaire": ligne.prix_unitaire,
            "sous_total": ligne.sous_totaux
         } for ligne in lignes
      ]
   }
    
   return commande_detail
##===============================================================##
##        Récupérer les commandes d'une agence spécifique        ##
##===============================================================##
@router.get("/commandes/agence/{agence_id}", response_model=List[schemas.CommandeDetailResponse], tags=["Commandes"])
def get_commandes_agence(
    agence_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint pour récupérer toutes les commandes d'une agence avec leurs détails.
    """
    commandes = db.query(Commande).filter(Commande.agence_id == agence_id).all()
    
    if not commandes:
        return []
    
    result = []
    for commande in commandes:
        # Récupérer les informations du client
        client = db.query(Client).filter(Client.id == commande.client_id).first()
        
        # Récupérer les lignes de commande
        lignes = db.query(LigneCommande).filter(LigneCommande.commande_id == commande.id).all()
        
        # Construire l'objet de réponse
        commande_detail = {
            "id": commande.id,
            "client_id": commande.client_id,
            "client_nom": f"{client.prenom} {client.nom}" if client else "Client inconnu",
            "client_telephone": client.telephone if client else "",
            "client_adresse": client.adresse if client else "",
            "agence_id": commande.agence_id,
            "createur_id": commande.createur_id,
            "recepteur_id": commande.recepteur_id,
            "date_creation": commande.date_creation,
            "date_reception": commande.date_reception,
            "statut": commande.status,
            "montant_total": commande.montant_total,
            "notes": commande.notes,
            "lignes_commande": [
                {
                    "id": ligne.id,
                    "nom_article": ligne.nom_article,
                    "reference_article": ligne.reference_article,
                    "quantite": ligne.quantite,
                    "prix_unitaire": ligne.prix_unitaire,
                    "sous_total": ligne.sous_totaux
                } for ligne in lignes
            ]
        }
        result.append(commande_detail)
    
    return result
##===============================================================##
##         commandes créées par un utilisateur spécifique      ##
##===============================================================##
@router.get("/utilisateurs/{user_id}/commandes", response_model=List[schemas.CommandeDetailResponse], tags=["Commandes"])
def get_commandes_utilisateur(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Endpoint pour récupérer toutes les commandes créées par un utilisateur spécifique.
    """
    # Vérifier si l'utilisateur existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Récupérer les commandes créées par cet utilisateur
    commandes = db.query(Commande).filter(Commande.createur_id == user_id).all()
    
    if not commandes:
        return []
    
    result = []
    for commande in commandes:
        # Récupérer les informations du client
        client = db.query(Client).filter(Client.id == commande.client_id).first()
        
        # Récupérer les informations du récepteur (utilisateur qui a reçu la commande)
        recepteur = db.query(User).filter(User.id == commande.recepteur_id).first()
        
        # Récupérer les lignes de commande
        lignes = db.query(LigneCommande).filter(LigneCommande.commande_id == commande.id).all()
        
        # Construire l'objet de réponse
        commande_detail = {
            "id": commande.id,
            "client_id": commande.client_id,
            "client_nom": f"{client.prenom} {client.nom}" if client else "Client inconnu",
            "client_telephone": client.telephone if client else "",
            "client_adresse": client.adresse if client else "",
            "agence_id": commande.agence_id,
            "createur_id": commande.createur_id,
            "recepteur_id": commande.recepteur_id,
            "recepteur_nom": f"{recepteur.prenom} {recepteur.nom}" if recepteur else None,
            "date_creation": commande.date_creation,
            "date_reception": commande.date_reception,
            "statut": commande.status,
            "montant_total": commande.montant_total,
            "notes": commande.notes,
            "lignes_commande": [
                {
                    "id": ligne.id,
                    "nom_article": ligne.nom_article,
                    "reference_article": ligne.reference_article,
                    "quantite": ligne.quantite,
                    "prix_unitaire": ligne.prix_unitaire,
                    "sous_total": ligne.sous_totaux
                } for ligne in lignes
            ]
        }
        result.append(commande_detail)
    
    return result

##===============================================================##
##           Update pour le status de la commande                ##
##===============================================================##
@router.patch("/commandes/{commande_id}/update_status", tags=["Commandes"])
async def update_order_status(
   commande_id: int, 
   status: str = Query(..., description="Nouveau statut de la commande"), 
   current_user: UserResponse = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   """
   Endpoint pour mettre à jour le statut d'une commande.
   """
   # Récupérer la commande
   commande = db.query(Commande).filter(Commande.id == commande_id).first()
   
   if not commande:
      raise HTTPException(status_code=404, detail="Commande non trouvée")
   
   # Mettre à jour le statut
   commande.status = status
   
   # Si la commande vient d'être reçue, mettre à jour la date de réception
   if status == "reçue" and not commande.date_reception:
      commande.date_reception = datetime.utcnow()
   
   # Enregistrer les modifications
   db.commit()
   db.refresh(commande)
   
   # Envoyer la notification
   if notification_service:
      success = await notification_service.notifier_mise_a_jour_statut(
          commande.agence_id, 
          commande.id, 
          status
      )
      if not success:
          logger.warning(f"Échec de l'envoi de la notification pour la commande {commande_id}")
   
   return {"success": True, "message": f"Statut mis à jour: {status}", "commande_id": commande_id}


##===============================================================##
##             Creation et mise jour du tablette                 ##
##===============================================================##
@router.post("/tablette/configurer",tags=["Tablette"])
def configurer_tablette(
   config: schemas.TabletteConfig, 
   current_user: UserResponse = Depends(role_required("admin")),
   db: Session = Depends(get_db)
):
   # Vérifier si l'agence existe
   agence = db.query(Agence).filter(Agence.id == config.agence_id).first()
   if not agence:
      raise HTTPException(status_code=404, detail="Agence non trouvée")
    
   # Vérifier si le numéro de série est unique
   tablette_existante = db.query(Tablette).filter(Tablette.numero_serie == config.numero_serie).first()
    
   if tablette_existante:
      # Mettre à jour la tablette existante
      tablette_existante.agence_id = config.agence_id
      tablette_existante.est_active = True
      tablette_existante.derniere_syncro = datetime.now()
   else:
      # Créer une nouvelle entrée de tablette
      nouvelle_tablette = Tablette(
         numero_serie=config.numero_serie,
         agence_id=config.agence_id,
         est_active=True,
         derniere_syncro=datetime.now()
      )
      db.add(nouvelle_tablette)
      db.commit()
    
   return {"success": True, "message": "Tablette configurée avec succès"}


##===============================================================##
##             Vérification du statut de la tablette             ##
##===============================================================##
@router.get("/tablettes/verifier/{numero_serie}", tags=["Tablette"])
def verifier_tablette(
   numero_serie: str,
   db: Session = Depends(get_db)
):
   """ 
   Endpoint pour vérifier le statut d'une tablette par son numéro de série.
   """
   
   tablette = db.query(Tablette).filter(Tablette.numero_serie == numero_serie).first()
   
   if not tablette:
      raise HTTPException(status_code=404, detail="Tablette non trouvée")
   
   # Mettre à jour la date de synchronisation
   tablette.derniere_syncro = datetime.utcnow()
   db.commit()
   
   return {
       "est_active": tablette.est_active,
       "agence_id": tablette.agence_id,
       "derniere_syncro": tablette.derniere_syncro
   }
   
   
##===============================================================##
##             Récupération de la liste des tablettes            ##
##===============================================================##
@router.get("/tablettes", response_model=List[schemas.TabletteResponse], tags=["Tablette"])
def get_tablettes(
    db : Session = Depends(get_db),
) :
   
    """
    Endpoint pour récupérer la liste de toutes les tablettes.
    """
    tablettes = db.query(Tablette).all()
    
    return tablettes
 
##===============================================================##
##            Endpoint pour desactiver une tablette              ##
##===============================================================##
@router.post("/tablettes/desactiver", tags=["Tablette"])
def desactiver_tablette(
    config: schemas.TabletteConfig,
    current_user: UserResponse = Depends(role_required(["admin"])),
    db: Session = Depends(get_db)
):
   """
   Endpoint pour désactiver une tablette.
   """
   tablette = db.query(Tablette).filter(Tablette.numero_serie == config.numero_serie).first()
    
   if not tablette:
      raise HTTPException(status_code=404, detail="Tablette non trouvée")
    
   tablette.est_active = False
   db.commit()
    
   return {"success": True, "message": "Tablette désactivée avec succès"}

##===============================================================##
##                  Creation de la session                       ##
##===============================================================##
@router.post("/sessions/start", tags=["Session"])
def start_session(
   user_id: int,
   current_user: UserResponse = Depends(get_current_user), 
   db: Session = Depends(get_db)  # Gardez ce nom pour la session de DB
):
   user = db.query(User).filter(User.id == user_id).first()
   if not user:
      raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
   new_session = UserSession(  # Utilisez le nouveau nom
      user_id=user_id,
      heure_connexion=datetime.now(),
      heure_deconnexion=datetime.now(),
      nombre_commande_creer=0 if user.role == "agent_call_center" else 0,
      nombre_commande_traiter=0 if user.role == "agent_restaurant" else 0
   )
    
   db.add(new_session)
   db.commit()
   db.refresh(new_session)
    
   return {"message": "Session démarrée", "session_id": new_session.id}
##===============================================================##
##            Mise à jour de l'heure de deconnexion              ##
##===============================================================##
@router.post("/sessions/end/{session_id}", tags=["Session"])
def end_session(
   session_id: int,
   current_user: UserResponse = Depends(get_current_user),
   db: Session = Depends(get_db)
):
   # Récupérer la session
   session = db.query(UserSession).filter(UserSession.id == session_id).first()
   if not session:
      raise HTTPException(status_code=404, detail="Session non trouvée")
    
   user = db.query(User).filter(User.id == session.user_id).first()

   if user.id != current_user.id:
      raise HTTPException(status_code=400, detail="Vous n'êtes pas autorisé à deconnecter cette session ") 
   
   # Mettre à jour l'heure de déconnexion
   session.heure_deconnexion = datetime.now()
   db.commit()
    
   return {"message": "Session terminée"}

##===============================================================##
##            Compteur de commandes créées mis à jour            ##
##===============================================================##
@router.post("/sessions/update_commandes_crees/{session_id}", tags=["Session"])
def update_commandes_crees(
   session_id: int,
   current_user: UserResponse = Depends(get_current_user), 
   db: Session = Depends(get_db)
):

   session = db.query(UserSession).filter(UserSession.id == session_id).first()

   if not session:
      raise HTTPException(status_code=404, detail="Session non trouvée")
    
   user = db.query(User).filter(User.id == session.user_id).first()
   if user.role != "agent_call_center":
      raise HTTPException(status_code=400, detail="Seuls les agents call center peuvent créer des commandes")
    
   session.nombre_commande_creer += 1
   db.commit()
    
   return {"message": "Compteur de commandes créées mis à jour"}

##===============================================================##
##            Compteur de commandes créées mis à jour            ##
##===============================================================##
@router.post("/sessions/update_commandes_traitees/{session_id}", tags=["Session"])
def update_commandes_traitees(
   session_id: int,
   current_user: UserResponse = Depends(get_current_user), 
   db: Session = Depends(get_db)
):

   session = db.query(UserSession).filter(UserSession.id == session_id).first()

   if not session:
      raise HTTPException(status_code=404, detail="Session non trouvée")
    
   user = db.query(User).filter(User.id == session.user_id).first()

   if user.role != "agent_restaurant":
      raise HTTPException(status_code=400, detail="Seuls les agents restaurant peuvent traiter des commandes")
    
   session.nombre_commande_traiter += 1
   db.commit()
    
   return {"message": "Compteur de commandes traitées mis à jour"}
 
##===============================================================##
##            Enregistrer un token FCM pour une tablette         ##
##===============================================================##
@router.post("/tablette/{numero_serie}/register_token", tags=["Tablette"])
async def register_token(
   numero_serie: str,
   token_data: dict,
   db: Session = Depends(get_db)
):
   """
   Endpoint pour enregistrer un token FCM pour une tablette.
   """
   # Vérifier si la tablette existe
   tablette = db.query(Tablette).filter(Tablette.numero_serie == numero_serie).first()
   if not tablette:
      raise HTTPException(status_code=404, detail="Tablette non trouvée")
    
   # Vérifier si la tablette est active
   if not tablette.est_active:
      raise HTTPException(status_code=400, detail="Cette tablette n'est pas active")
    
   # Enregistrer le token
   token = token_data.get("token")
   if not token:
      raise HTTPException(status_code=400, detail="Token manquant")
    
   # Enregistrer le token avec le service de notification
   if notification_service:
      success = await notification_service.enregistrer_token(numero_serie, token)
      if success:
         return {"success": True, "message": "Token enregistré avec succès"}
      else:
         raise HTTPException(status_code=500, detail="Échec de l'enregistrement du token")
   else:
      raise HTTPException(status_code=503, detail="Service de notification non disponible")

##===============================================================##
##            Désinscrire un token FCM                           ##
##===============================================================##
@router.post("/tablette/{numero_serie}/unregister_token", tags=["Tablette"])
async def unregister_token(
   numero_serie: str,
   token_data: dict,
   db: Session = Depends(get_db)
):
   """
   Endpoint pour désinscrire un token FCM.
   """
   # Vérifier si la tablette existe
   tablette = db.query(Tablette).filter(Tablette.numero_serie == numero_serie).first()
   if not tablette:
      raise HTTPException(status_code=404, detail="Tablette non trouvée")
    
   # Désinscrire le token
   token = token_data.get("token")
   if not token:
      raise HTTPException(status_code=400, detail="Token manquant")
    
   # Désinscrire le token avec le service de notification
   if notification_service:
      success = await notification_service.desinscrire_token(numero_serie, token)
      if success:
         return {"success": True, "message": "Token désinscrit avec succès"}
      else:
         raise HTTPException(status_code=500, detail="Échec de la désinscription du token")
   else:
      raise HTTPException(status_code=503, detail="Service de notification non disponible")
