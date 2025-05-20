import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Créer le dossier des logs s'il n'existe pas
os.makedirs("logs", exist_ok=True)

# Configuration de base du logger
logger = logging.getLogger("rfc_callcenter_api")
logger.setLevel(logging.INFO)

# Format du log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Handler pour la console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Handler pour les fichiers
file_handler = RotatingFileHandler(
    filename=f"logs/api_{datetime.now().strftime('%Y-%m-%d')}.log",
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Fonction pour créer des logs HTTP
def log_http_request(request, response_status, execution_time=None):
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host,
        "status_code": response_status,
        "execution_time": f"{execution_time:.2f}s" if execution_time else None
    }
    
    if 200 <= response_status < 400:
        logger.info(f"HTTP {log_data['method']} {log_data['url']} - {log_data['status_code']} - {log_data['execution_time']}")
    else:
        logger.error(f"HTTP {log_data['method']} {log_data['url']} - {log_data['status_code']} - {log_data['execution_time']}")