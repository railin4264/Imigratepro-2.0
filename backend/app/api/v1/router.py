from fastapi import APIRouter

from app.api.v1.endpoints import cases, clients, documents, forms, notifications, public_forms, services, users

api_router = APIRouter()
api_router.include_router(clients.router)
api_router.include_router(cases.router)
api_router.include_router(forms.router)
api_router.include_router(users.router)
api_router.include_router(public_forms.router)
api_router.include_router(services.router)
api_router.include_router(documents.router)
api_router.include_router(notifications.router)
