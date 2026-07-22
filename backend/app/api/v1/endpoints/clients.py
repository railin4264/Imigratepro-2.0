import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession, RequireOwnerOrAdmin
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def list_clients(db: DbSession, skip: int = 0, limit: int = 100):
    return db.query(Client).order_by(Client.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=ClientRead, status_code=201)
def create_client(payload: ClientCreate, db: DbSession, requester: CurrentUser):
    client = Client(**payload.model_dump())
    db.add(client)
    db.flush()
    log_action(db, requester, "client.created", "client", client.id,
               {"name": f"{client.first_name} {client.last_name}"})
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: uuid.UUID, db: DbSession):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(client_id: uuid.UUID, payload: ClientUpdate, db: DbSession, requester: CurrentUser):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    log_action(db, requester, "client.updated", "client", client.id,
               {"name": f"{client.first_name} {client.last_name}"})
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: uuid.UUID, db: DbSession, requester: RequireOwnerOrAdmin):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    log_action(
        db, requester, "client.deleted", "client", client.id, {"name": f"{client.first_name} {client.last_name}"}
    )
    db.delete(client)
    db.commit()
