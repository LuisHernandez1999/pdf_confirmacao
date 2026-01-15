import logging
from datetime import date, datetime
from typing import Sequence, List
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from src.domain.models.relatorio_confirmacao import RelatorioConfirmacao
from src.domain.models.confirmacao_servico import ConfirmacaoServico

logger = logging.getLogger("relatorio_mapper")

#### validar confirmacao(move pra camada utils)
def _is_confirmacao_valida(c: ConfirmacaoServico) -> bool:
    campos_faltando = [
        campo
        for campo, valor in (
            ("tag_doc", c.tag_doc),
            ("nome_vistoriador", c.nome_vistoriador),
            ("tipo_servico", c.tipo_servico),
            ("data_servico", c.data_servico),
        )
        if not valor
    ]

    if campos_faltando:
        logger.info(
            "Confirmação ignorada (campos faltando: %s) - tag_doc=%s",
            ", ".join(campos_faltando),
            getattr(c, "tag_doc", "desconhecida"),
        )
        return False

    return True


def mapear_confirmacoes_validas(
    confirmacoes: Sequence[ConfirmacaoServico],
) -> list[dict]:
    confirmacoes_validas = [
        c for c in confirmacoes if _is_confirmacao_valida(c)
    ]

    if not confirmacoes_validas:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nenhuma confirmação com dados completos foi encontrada. "
                "Verifique tag_doc, nome_vistoriador, tipo_servico e data_servico."
            ),
        )

    logger.info(
        "Filtragem de confirmações: %d válidas de %d totais",
        len(confirmacoes_validas),
        len(confirmacoes),
    )

    BASE_URL = "/static/imagens/"
    lista_mapeada: list[dict] = []

    for c in confirmacoes_validas:
        imagens = [
            {
                "id": img.id,
                "url": f"{BASE_URL}{img.imagem}",
            }
            for img in (c.imagens or [])
        ]

        lista_mapeada.append(
            {
                "id": c.id,
                "tag_doc": c.tag_doc,
                "tipo_servico": c.tipo_servico,
                "data_servico": c.data_servico.isoformat()
                if c.data_servico
                else None,
                "imagens": imagens,
            }
        )

    return lista_mapeada


def calcular_total_imagens(confirmacoes: Sequence[dict]) -> int:
    total = sum(len(c.get("imagens", [])) for c in confirmacoes)
    logger.debug("Total de imagens calculado: %d", total)
    return total


def gerar_observacao_relatorio(
    total_confirmacoes: int,
    total_imagens: int,
    data_inicial: date | None = None,
    data_final: date | None = None,
) -> str:
    partes = [
        f"RELATÓRIO COMPLETO - {total_confirmacoes} confirmações, {total_imagens} imagens"
    ]

    if data_inicial or data_final:
        if data_inicial and data_final:
            periodo = (
                f"Período: {data_inicial:%d/%m/%Y} a {data_final:%d/%m/%Y}"
            )
        elif data_inicial:
            periodo = f"A partir de: {data_inicial:%d/%m/%Y}"
        else:
            periodo = f"Até: {data_final:%d/%m/%Y}"

        partes.append(periodo)

    partes.append(datetime.now().strftime("%d/%m/%Y %H:%M"))

    return " - ".join(partes)


def mapear_dados_relatorio(
    relatorio: RelatorioConfirmacao,
    data_inicial: date | None = None,
    data_final: date | None = None,
) -> dict:
    return {
        "id": relatorio.id,
        "total_confirmacoes": relatorio.total_confirmacoes,
        "total_imagens": relatorio.total_imagens,
        "data_geracao": relatorio.data_geracao.isoformat(),
        "data_inicial": data_inicial.isoformat() if data_inicial else None,
        "data_final": data_final.isoformat() if data_final else None,
        "observacao": relatorio.observacao,
    }


def criar_relatorio_confirmacao(
    db: Session,
    primeira_tag: str,
    observacao: str,
) -> RelatorioConfirmacao:
    relatorio = RelatorioConfirmacao(
        confirmacao_tag=primeira_tag,
        observacao=observacao,
    )

    db.add(relatorio)
    db.commit()
    db.refresh(relatorio)

    logger.info(
        "Relatório criado com sucesso - ID: %d | Primeira tag: %s",
        relatorio.id,
        primeira_tag,
    )

    return relatorio

##### service toda agora realmente retira a deletada do backmarch 
def filtrar_imagens_excluidas(
    confirmacoes: Sequence[ConfirmacaoServico],
    ids_excluir: List[int],
) -> List[ConfirmacaoServico]:
    if not ids_excluir:
        return list(confirmacoes)

    ids_set = set(ids_excluir)
    resultado: List[ConfirmacaoServico] = []
    total_removidas = 0

    campos_para_copiar = [
        "id",
        "tag_doc",
        "nome_vistoriador",
        "tipo_servico",
        "data_servico",
        "observacao",
        "status",
        "created_at",
        "updated_at",
    ]

    for conf in confirmacoes:
        if not conf.imagens:
            resultado.append(conf)
            continue

        imagens_mantidas = []
        houve_remocao = False

        for img in conf.imagens:
            if img.id in ids_set:
                houve_remocao = True
                total_removidas += 1
                logger.info(
                    "Imagem ID %d excluída do relatório (tag_doc: %s)",
                    img.id,
                    conf.tag_doc or "sem_tag",
                )
            else:
                imagens_mantidas.append(img)

        if not houve_remocao:
            resultado.append(conf)
            continue

        nova_conf = ConfirmacaoServico()#### agora cria apenas um objeto 

        for campo in campos_para_copiar:
            if hasattr(conf, campo):
                setattr(nova_conf, campo, getattr(conf, campo))

        nova_conf.imagens = imagens_mantidas 
        resultado.append(nova_conf)

    logger.info("Total de imagens excluídas do PDF: %d", total_removidas)
    return resultado



def get_imagens_modal(db: Session) -> list[dict]:
    confirmacoes = (
        db.query(ConfirmacaoServico)
        .options(joinedload(ConfirmacaoServico.imagens))
        .order_by(ConfirmacaoServico.data_servico.desc())
        .all()
    )

    imagens_lista: list[dict] = []

    for conf in confirmacoes:
        for img in conf.imagens or []:
            imagens_lista.append(
                {
                    "imagem_id": img.id,
                }
            )

    return imagens_lista
