import logging
from datetime import date, datetime
from typing import Sequence,List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.domain.models.relatorio_confirmacao import RelatorioConfirmacao
from src.domain.models.confirmacao_servico import ConfirmacaoServico

logger = logging.getLogger("relatorio_mapper")


def _is_confirmacao_valida(c: ConfirmacaoServico) -> bool:
    campos_faltando = [
        campo for campo, valor in [
            ("tag_doc", c.tag_doc),
            ("nome_vistoriador", c.nome_vistoriador),
            ("tipo_servico", c.tipo_servico),
            ("data_servico", c.data_servico),
        ] if not valor
    ]
    
    if campos_faltando:
        logger.info("Confirmação ignorada (campos faltando: %s) - tag_doc=%s", 
                    ", ".join(campos_faltando), getattr(c, "tag_doc", "desconhecida"))
        return False
    return True


def mapear_confirmacoes_validas(confirmacoes: Sequence[ConfirmacaoServico]) -> list[ConfirmacaoServico]:
    confirmacoes_validas = [c for c in confirmacoes if _is_confirmacao_valida(c)]

    if not confirmacoes_validas:
        raise HTTPException(
            status_code=400,
            detail="Nenhuma confirmação com dados completos foi encontrada. "
                   "Verifique tag_doc, nome_vistoriador, tipo_servico e data_servico."
        )

    logger.info(
        "Filtragem de confirmações: %d válidas de %d totais",
        len(confirmacoes_validas), len(confirmacoes)
    )
    return confirmacoes_validas


def calcular_total_imagens(confirmacoes: Sequence[ConfirmacaoServico]) -> int:
    total = sum(len(c.imagens or ()) for c in confirmacoes)
    logger.debug("Total de imagens calculado: %d", total)
    return total


def gerar_observacao_relatorio(
    total_confirmacoes: int,
    total_imagens: int,
    data_inicial: date | None = None,
    data_final: date | None = None,
) -> str:
    partes = [f"RELATÓRIO COMPLETO - {total_confirmacoes} confirmações, {total_imagens} imagens"]

    if data_inicial or data_final:
        if data_inicial and data_final:
            periodo = f"Período: {data_inicial:%d/%m/%Y} a {data_final:%d/%m/%Y}"
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

### criar relatorio
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
    
    logger.info("Relatório criado com sucesso - ID: %d | Primeira tag: %s", relatorio.id, primeira_tag)
    return relatorio
#### excluir imagens("seleciona ela e apaga")
def filtrar_imagens_excluidas(
    confirmacoes: Sequence[ConfirmacaoServico],
    ids_excluir: List[int],
) -> List[ConfirmacaoServico]:
    """
    Remove imagens específicas das confirmações.
    Versão FINAL e à prova de SQLAlchemy (funciona com attached/detached/qualquer estado).
    """
    if not ids_excluir:
        return list(confirmacoes)

    ids_set = set(ids_excluir)
    resultado = []
    total_removidas = 0

    for conf in confirmacoes:
        # === CRIA UMA CÓPIA LIMPA DA CONFIRMAÇÃO SEM NENHUM RASTRO DO SQLALCHEMY ===
        nova_conf = ConfirmacaoServico()

        # Copia todos os campos escalares (strings, datas, números, etc.)
        campos_para_copiar = [
            "id", "tag_doc", "nome_vistoriador", "tipo_servico", "data_servico",
            "observacao", "status", "created_at", "updated_at",
            # adicione aqui qualquer outro campo que sua model tenha
        ]

        for campo in campos_para_copiar:
            if hasattr(conf, campo):
                setattr(nova_conf, campo, getattr(conf, campo))

        # === TRATA AS IMAGENS ===
        if conf.imagens:
            imagens_mantidas = []
            for img in conf.imagens:
                if img.id not in ids_set:
                    imagens_mantidas.append(img)  # mantém o objeto imagem original (é seguro)
                else:
                    total_removidas += 1
                    logger.info("Imagem ID %d excluída do relatório (tag_doc: %s)", img.id, conf.tag_doc or "sem_tag")

            nova_conf.imagens = imagens_mantidas
        else:
            nova_conf.imagens = []

        resultado.append(nova_conf)

    logger.info("Total de imagens excluídas do PDF: %d", total_removidas)
    return resultado