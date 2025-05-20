from dotenv import load_dotenv
load_dotenv()  # Charger les variables d'environnement dès le début
import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logger import logger, log_http_request
from callCenter.router import router as router_callCenter
from database import Base, engine
#from dotenv import load_dotenv
from callCenter.notification_service import NotificationService
from callCenter.router import notification_service

notification_service = NotificationService()


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "RFC Call Center API",
    description="""
       API pour la gestion du centre d'appel RFC.
    
       Cette API permet la gestion des commandes, des clients, des utilisateurs et des tablettes.    
    """,
    version = "1.0.0",
    contact={
        "name": "Support RFC",
        "email": "support@rfc.com",
    },
    openapi_tags=[
         {
            "name": "Authentication",
            "description": "Opérations liées à l'authentification des utilisateurs",
        },
        {
            "name": "Commandes",
            "description": "Gestion des commandes (création, mise à jour, récupération)",
        },
        {
            "name": "Clients",
            "description": "Gestion des clients",
        },
        {
            "name": "Utilisateurs",
            "description": "Gestion des utilisateurs",
        },
        {
            "name": "Agences",
            "description": "Gestion des agences",
        },
        {
            "name": "Tablette",
            "description": "Configuration et gestion des tablettes",
        },
    ]
)

# Configuration de la limitation du debit


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Appel des routers
app.include_router(router_callCenter)

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    execution_time = time.time() - start_time
    log_http_request(request, response.status_code, execution_time)
    
    return response

@app.get('/')
def index_root():
    return {"message": "Bienvenue sur l'interface de developpement de RFC Gesion de commande"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', reload=True)
