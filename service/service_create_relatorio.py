import logging
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from domain.models.relatorio_confirmacao import RelatorioConfirmacao
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao
import json

logger = logging.getLogger("relatorio_service")


def gerar_relatorio(
    db: Session,
    confirmacao_tag: str,
    imagens_antes_ids: list[int],
    imagens_depois_ids: list[int],
) -> dict:

    # Buscar confirmação pelo tag
    confirmacao = db.query(ConfirmacaoServico).filter(
        ConfirmacaoServico.tag_doc == confirmacao_tag
    ).first()

    if not confirmacao:
        raise HTTPException(404, "Confirmação não encontrada.")

    # Buscar TODAS as imagens selecionadas
    todas_ids = imagens_antes_ids + imagens_depois_ids

    imagens = db.query(ImagemConfirmacao).filter(
        ImagemConfirmacao.confirmacao_id == confirmacao.id,
        ImagemConfirmacao.id.in_(todas_ids)
    ).all()

    if len(imagens) != len(todas_ids):
        raise HTTPException(404, "Alguma imagem não pertence à confirmação.")

    # Organizar imagens em dicionário
    img_dict = {img.id: img for img in imagens}
    imagens_antes = [img_dict[i] for i in imagens_antes_ids]
    imagens_depois = [img_dict[i] for i in imagens_depois_ids]

    # Criar relatório (listas convertidas para JSON)
    relatorio = RelatorioConfirmacao(
        confirmacao_tag=confirmacao_tag,
        imagem_antes=[img.imagem for img in imagens_antes],  # lista de URLs
        imagem_depois=[img.imagem for img in imagens_depois],
        latitude_antes=[float(img.latitude) for img in imagens_antes],
        longitude_antes=[float(img.longitude) for img in imagens_antes],
        latitude_depois=[float(img.latitude) for img in imagens_depois],
        longitude_depois=[float(img.longitude) for img in imagens_depois],
    )

    # Salvar no banco
    db.add(relatorio)
    db.commit()
    db.refresh(relatorio)

    logger.info(f"Relatório criado para TAG {confirmacao_tag}")

    # Retornar resultado serializado
    return jsonable_encoder(relatorio)
