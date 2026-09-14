from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Interest
from app.schemas import InterestOut

router = APIRouter()


@router.get("/interests", response_model=list[InterestOut])
def list_interests(db: Session = Depends(get_db)) -> list[Interest]:
    broad = (
        db.execute(
            select(Interest)
            .where(Interest.parent_id.is_(None))
            .order_by(Interest.sort_order)
        )
        .scalars()
        .all()
    )
    return list(broad)
