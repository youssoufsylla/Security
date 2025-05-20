import firebase_admin
from firebase_admin import credentials, messaging
import os
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models import Tablette

logger = logging.getLogger(__name__)

class FirebaseNotificationService:
    """Service pour gérer les notifications via Firebase Cloud Messaging."""
    
    _initialized = False
    
    def __init__(self):
        """Initialiser le service Firebase."""
        if not self._initialized:
            self._initialize_firebase()
            FirebaseNotificationService._initialized = True
    
    def _initialize_firebase(self):
        """Initialise la connexion Firebase."""
        try:
            if os.path.exists("firebase-credentials.json"):
                cred = credentials.Certificate("firebase-credentials.json")
            else:
                cred = self._get_credentials_from_env()
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            raise
    
    def _get_credentials_from_env(self):
        """Récupère les credentials Firebase depuis les variables d'environnement."""
        return credentials.Certificate({
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
        })
    
    def _handle_device_token_operation(self, operation: str, token: str, agency_id: int, 
                                     device_id: str, db: Session = None) -> Dict[str, Any]:
        """
        Méthode générique pour gérer l'inscription/désinscription des tokens.
        
        Args:
            operation: 'subscribe' ou 'unsubscribe'
            token: Token FCM de l'appareil
            agency_id: ID de l'agence
            device_id: ID unique de l'appareil
            db: Session de base de données
            
        Returns:
            Résultat de l'opération
        """
        try:
            topic = f"agency_{agency_id}"
            
            # Exécute l'opération appropriée
            if operation == 'subscribe':
                response = messaging.subscribe_to_topic([token], topic)
                log_action = "subscribed to"
            else:
                response = messaging.unsubscribe_from_topic([token], topic)
                log_action = "unsubscribed from"
            
            logger.info(f"Device {device_id} {log_action} agency {agency_id}: {response.success_count} successful")
            
            # Met à jour la base de données si fournie
            if db:
                self._update_device_token_in_db(operation, device_id, token, db)
            
            return {
                "success": True,
                "operation": operation,
                "results": {
                    "success_count": response.success_count,
                    "failure_count": response.failure_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error during device token {operation}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _update_device_token_in_db(self, operation: str, device_id: str, token: str, db: Session):
        """Met à jour le token dans la base de données."""
        tablette = db.query(Tablette).filter(Tablette.numero_serie == device_id).first()
        if tablette:
            if operation == 'subscribe':
                tablette.firebase_token = token
                log_msg = "Updated"
            else:
                tablette.firebase_token = None
                log_msg = "Removed"
            
            db.commit()
            logger.info(f"{log_msg} Firebase token for device {device_id}")
    
    def send_notification_to_agency(
        self, 
        agency_id: int, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, str]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Envoyer une notification à tous les appareils d'une agence spécifique.
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=f"agency_{agency_id}",
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        icon="ic_notification",
                        color="#f5a623",
                        channel_id="rfc_orders",
                        click_action="OPEN_ORDER_ACTIVITY"
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1,
                            content_available=True
                        )
                    )
                )
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent notification to agency {agency_id}: {response}")
            return {"success": True, "message_id": response}
            
        except Exception as e:
            logger.error(f"Error sending notification to agency {agency_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def register_device_token(
        self, 
        token: str, 
        agency_id: int,
        device_id: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """Enregistre un token d'appareil et le souscrit au topic de son agence."""
        return self._handle_device_token_operation('subscribe', token, agency_id, device_id, db)
    
    def unregister_device_token(
        self, 
        token: str, 
        agency_id: int,
        device_id: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """Désinscrit un token d'appareil du topic de son agence."""
        return self._handle_device_token_operation('unsubscribe', token, agency_id, device_id, db)

# Instance singleton du service
firebase_service = FirebaseNotificationService()