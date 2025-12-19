from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.domain.models.imagem_confirmacao import ImagemConfirmacao
from src.utils.imagens_utils.imagens_utils import gerar_thumbnail_webp

router = APIRouter()

@router.get("/imagens/{imagem_id}/thumb")
def get_imagem_thumb(imagem_id: int, db: Session = Depends(get_db)):
    img = (
        db.query(ImagemConfirmacao.imagem)
        .filter(ImagemConfirmacao.id == imagem_id)
        .scalar()
    )

    if not img:
        raise HTTPException(404, "Imagem não encontrada")

    return {
        "imagem": gerar_thumbnail_webp(img)
    }
