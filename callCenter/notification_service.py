from .firebase_service import firebase_service
from typing import Dict, Any
import asyncio
import logging
from sqlalchemy.orm import Session
from database import get_db
from models import Tablette

logger = logging.getLogger(__name__)

class NotificationService:
    """Service pour gérer les notifications aux tablettes des restaurants."""
    
    def __init__(self):
        self.firebase = firebase_service
        logger.info("Service de notification initialisé")
    
    async def notifier_nouvelle_commande(self, agence_id: int, commande_data: Dict[str, Any]) -> bool:
        """
        Envoie une notification pour une nouvelle commande.
        
        Args:
            agence_id: ID de l'agence destinataire
            commande_data: Données de la commande
        
        Returns:
            bool: True si la notification a été envoyée avec succès
        """
        try:
            # Construire le topic spécifique à l'agence
            topic = f"agence_{agence_id}"
            
            # Construire le titre et le corps de la notification
            client_nom = f"{commande_data['client']['prenom']} {commande_data['client']['nom']}"
            montant = commande_data['montant_total']
            
            title = "Nouvelle commande"
            body = f"Commande #{commande_data['id']} - {client_nom} - {montant} GNF"
            
            # Données additionnelles pour la notification
            data = {
                "commande_id": str(commande_data['id']),
                "type": "nouvelle_commande",
                "agence_id": str(agence_id)
            }
            
            # Envoyer la notification au topic de l'agence
            result = self.firebase.send_notification_to_topic(topic, title, body, data)
            
            # Logger le résultat
            if result["success"]:
                logger.info(f"Notification envoyée avec succès au topic {topic}: {result}")
                return True
            else:
                logger.error(f"Échec de l'envoi de notification au topic {topic}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification: {str(e)}")
            return False
    
    async def notifier_mise_a_jour_statut(self, agence_id: int, commande_id: int, statut: str) -> bool:
        """
        Envoie une notification pour une mise à jour de statut de commande.
        
        Args:
            agence_id: ID de l'agence concernée
            commande_id: ID de la commande
            statut: Nouveau statut de la commande
        
        Returns:
            bool: True si la notification a été envoyée avec succès
        """
        try:
            # Construire le topic spécifique à l'agence
            topic = f"agence_{agence_id}"
            
            # Construire le titre et le corps de la notification
            title = "Mise à jour de commande"
            body = f"La commande #{commande_id} est maintenant: {statut}"
            
            # Données additionnelles pour la notification
            data = {
                "commande_id": str(commande_id),
                "type": "mise_a_jour_statut",
                "agence_id": str(agence_id),
                "statut": statut
            }
            
            # Envoyer la notification au topic de l'agence
            result = self.firebase.send_notification_to_topic(topic, title, body, data)
            
            # Logger le résultat
            if result["success"]:
                logger.info(f"Notification de statut envoyée avec succès: {result}")
                return True
            else:
                logger.error(f"Échec de l'envoi de notification de statut: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification de statut: {str(e)}")
            return False

    async def enregistrer_token(self, numero_serie: str, token: str) -> bool:
        """
        Enregistre un token FCM pour une tablette.
        
        Args:
            numero_serie: Numéro de série de la tablette
            token: Token FCM à enregistrer
            
        Returns:
            bool: True si le token a été enregistré avec succès
        """
        try:
            # Obtenir une session de base de données
            db = next(get_db())
            
            # Récupérer la tablette correspondante
            tablette = db.query(Tablette).filter(Tablette.numero_serie == numero_serie).first()
            
            if not tablette:
                logger.error(f"Tablette avec numéro de série {numero_serie} non trouvée")
                return False
                
            # Construire le topic spécifique à l'agence
            topic = f"agence_{tablette.agence_id}"
            
            # Abonner le token au topic de l'agence
            result = self.firebase.subscribe_to_topic([token], topic)
            
            if result["success"]:
                logger.info(f"Token {token} enregistré et abonné au topic {topic}")
                return True
            else:
                logger.error(f"Échec de l'abonnement du token {token} au topic {topic}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du token: {str(e)}")
            return False
    
    async def desinscrire_token(self, numero_serie: str, token: str) -> bool:
        """
        Désinscrit un token FCM.
        
        Args:
            numero_serie: Numéro de série de la tablette
            token: Token FCM à désinscrire
            
        Returns:
            bool: True si le token a été désinscrit avec succès
        """
        try:
            # Obtenir une session de base de données
            db = next(get_db())
            
            # Récupérer la tablette correspondante
            tablette = db.query(Tablette).filter(Tablette.numero_serie == numero_serie).first()
            
            if not tablette:
                logger.error(f"Tablette avec numéro de série {numero_serie} non trouvée")
                return False
                
            # Construire le topic spécifique à l'agence
            topic = f"agence_{tablette.agence_id}"
            
            # Désabonner le token du topic de l'agence
            result = self.firebase.unsubscribe_from_topic([token], topic)
            
            if result["success"]:
                logger.info(f"Token {token} désinscrit du topic {topic}")
                return True
            else:
                logger.error(f"Échec de la désinscription du token {token} du topic {topic}: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la désinscription du token: {str(e)}")
            return False