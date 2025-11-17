# domain/service/service_gerar_relatorio.py

import logging
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder  # ← ESSA É A CHAVE
from sqlalchemy.orm import Session, joinedload
from domain.models.relatorio_confirmacao import RelatorioConfirmacao
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao

logger = logging.getLogger("relatorio_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def gerar_relatorio(
    db: Session,
    confirmacao_tag: str,
    imagem_antes_id: int,
    imagem_depois_id: int,
    obs_antes: str | None = None,
    obs_depois: str | None = None,
    observacao: str | None = None,
) -> dict:

    logger.info("="*80)
    logger.info("INICIANDO GERAÇÃO DE RELATÓRIO")
    logger.info(f"confirmacao_tag: {confirmacao_tag}")
    logger.info("="*80)

    # 1. Busca confirmação
    confirmacao = db.query(ConfirmacaoServico).filter(
        ConfirmacaoServico.tag_doc == confirmacao_tag
    ).first()
    if not confirmacao:
        raise HTTPException(status_code=404, detail="Confirmação não encontrada.")
    logger.info(f"Confirmação encontrada: id={confirmacao.id}")

    # 2. Valida imagens
    img_antes = db.query(ImagemConfirmacao).filter(
        ImagemConfirmacao.id == imagem_antes_id,
        ImagemConfirmacao.confirmacao_id == confirmacao.id
    ).first()
    img_depois = db.query(ImagemConfirmacao).filter(
        ImagemConfirmacao.id == imagem_depois_id,
        ImagemConfirmacao.confirmacao_id == confirmacao.id
    ).first()

    if not img_antes or not img_depois:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")
    if imagem_antes_id == imagem_depois_id:
        raise HTTPException(status_code=400, detail="Imagens devem ser diferentes.")

    # 3. Cria relatório
    relatorio = RelatorioConfirmacao(
        confirmacao_tag=confirmacao_tag,
        obs_antes=obs_antes,
        obs_depois=obs_depois,
        observacao=observacao,
    )
    db.add(relatorio)
    db.commit()
    logger.info(f"Relatório criado: id={relatorio.id}")

    # 4. RECARREGA COM RELACIONAMENTOS
    relatorio_carregado = (
        db.query(RelatorioConfirmacao)
        .options(
            joinedload(RelatorioConfirmacao.confirmacao),
            joinedload(RelatorioConfirmacao.imagens)
        )
        .filter(RelatorioConfirmacao.id == relatorio.id)
        .first()
    )

    if not relatorio_carregado:
        raise HTTPException(status_code=500, detail="Erro ao recarregar relatório.")

    # 5. Monta objeto bruto (com Decimal, date, etc)
    objeto_bruto = {
        "id": relatorio_carregado.id,
        "confirmacao_tag": relatorio_carregado.confirmacao_tag,
        "obs_antes": relatorio_carregado.obs_antes,
        "obs_depois": relatorio_carregado.obs_depois,
        "observacao": relatorio_carregado.observacao,
        "data_geracao": relatorio_carregado.data_geracao,
        "confirmacao": {
            "id": relatorio_carregado.confirmacao.id,
            "tag_doc": relatorio_carregado.confirmacao.tag_doc,
            "nome_vistoriador": relatorio_carregado.confirmacao.nome_vistoriador,
            "data_servico": relatorio_carregado.confirmacao.data_servico,
            "tipo_servico": relatorio_carregado.confirmacao.tipo_servico,
            "latitude": relatorio_carregado.confirmacao.latitude,
            "longitude": relatorio_carregado.confirmacao.longitude,
        },
        "imagens": [
            {"id": img.id, "url": img.imagem}
            for img in relatorio_carregado.imagens
        ],
        "imagens_utilizadas": {
            "antes": {"id": img_antes.id, "url": img_antes.imagem},
            "depois": {"id": img_depois.id, "url": img_depois.imagem}
        }
    }

    # 6. USA jsonable_encoder → CONVERTE Decimal, date, datetime AUTOMATICAMENTE
    resposta = jsonable_encoder(objeto_bruto)

    logger.info("RELATÓRIO GERADO E SERIALIZADO COM jsonable_encoder!")
    logger.info("="*80)
    return resposta