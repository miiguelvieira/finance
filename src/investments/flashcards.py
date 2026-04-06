"""Flashcards educativos sobre investimentos (BR 2026)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Flashcard:
    id: int
    topic: str
    question: str
    answer: str
    tags: list[str]


FLASHCARDS: list[Flashcard] = [
    Flashcard(
        id=1,
        topic="Renda Fixa — IR 2026",
        question="Qual a alíquota de IR sobre CDB e Tesouro Direto após a reforma 2026?",
        answer=(
            "17,5% sobre o ganho bruto (após dedução do IOF, se aplicável). "
            "A reforma 2026 unificou as alíquotas, eliminando a tabela regressiva anterior."
        ),
        tags=["renda_fixa", "ir", "reforma_2026"],
    ),
    Flashcard(
        id=2,
        topic="IOF em Investimentos",
        question="Quando incide IOF em renda fixa e como ele é calculado?",
        answer=(
            "O IOF incide quando o resgate ocorre em menos de 30 dias após a aplicação. "
            "A alíquota é regressiva: 96% no 1º dia até 0% no 30º dia, calculada sobre o ganho bruto."
        ),
        tags=["renda_fixa", "iof"],
    ),
    Flashcard(
        id=3,
        topic="LCI/LCA pós-reforma",
        question="LCI e LCA continuam isentos de IR após a reforma tributária de 2026?",
        answer=(
            "Não. As novas emissões após a reforma pagam 5% de IR sobre o ganho. "
            "Papéis emitidos antes da reforma mantêm a isenção até o vencimento."
        ),
        tags=["lci_lca", "ir", "reforma_2026"],
    ),
    Flashcard(
        id=4,
        topic="Ações — Isenção Trimestral",
        question="Quando as vendas de ações são isentas de IR?",
        answer=(
            "Quando o total de vendas no trimestre não supera R$60.000. "
            "Operações de day trade nunca são isentas — pagam 20% independente do volume."
        ),
        tags=["acoes", "ir", "isencao"],
    ),
    Flashcard(
        id=5,
        topic="FII — Tributação",
        question="Como são tributados os FII em 2026?",
        answer=(
            "Dividendos pagam 5% de IR na fonte. "
            "Ganho de capital na venda das cotas paga 17,5%. "
            "Prejuízos de capital podem ser compensados com ganhos futuros por até 5 anos."
        ),
        tags=["fii", "ir", "dividendos"],
    ),
    Flashcard(
        id=6,
        topic="Carryforward de Prejuízo",
        question="Por quanto tempo posso compensar prejuízo de ações/FII com lucros futuros?",
        answer=(
            "Até 5 anos a partir da data do prejuízo. "
            "A compensação só é válida dentro da mesma categoria (ações com ações, FII com FII). "
            "Day trade só compensa day trade."
        ),
        tags=["acoes", "fii", "carryforward"],
    ),
    Flashcard(
        id=7,
        topic="Crypto — Tributação",
        question="Quando criptoativos são isentos de IR?",
        answer=(
            "Quando as vendas mensais somam até R$35.000. "
            "Acima disso, paga 17,5% sobre o ganho. "
            "Prejuízos podem ser compensados em meses futuros por até 5 anos."
        ),
        tags=["crypto", "ir", "isencao"],
    ),
    Flashcard(
        id=8,
        topic="Diversificação de Carteira",
        question="Qual a lógica tributária para escolher entre CDB, LCI/LCA e Tesouro em 2026?",
        answer=(
            "Com a reforma, LCI/LCA passou a 5% de IR (antes isento). "
            "CDB e Tesouro ficaram em 17,5%. "
            "Para prazos curtos (<30 dias) prefira evitar renda fixa por conta do IOF. "
            "Para liquidez diária, Tesouro Selic ou CDB com liquidez diária pós 30 dias."
        ),
        tags=["estrategia", "renda_fixa", "lci_lca", "reforma_2026"],
    ),
]


def get_all() -> list[Flashcard]:
    return FLASHCARDS


def get_by_tag(tag: str) -> list[Flashcard]:
    return [c for c in FLASHCARDS if tag in c.tags]


def get_by_id(flashcard_id: int) -> Flashcard | None:
    return next((c for c in FLASHCARDS if c.id == flashcard_id), None)
