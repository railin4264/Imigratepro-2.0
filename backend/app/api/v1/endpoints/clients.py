import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def list_clients(db: DbSession, skip: int = 0, limit: int = 100):
    return db.query(Client).order_by(Client.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=ClientRead, status_code=201)
def create_client(payload: ClientCreate, db: DbSession):
    client = Client(**payload.model_dump())
    db.add(client)
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
def update_client(client_id: uuid.UUID, payload: ClientUpdate, db: DbSession):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: uuid.UUID, db: DbSession):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()
