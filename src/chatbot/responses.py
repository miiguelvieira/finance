"""Templates de resposta do chatbot financeiro."""

from __future__ import annotations

HELP_TEXT = (
    "Posso ajudar com:\n"
    "- Saldo e extrato das suas contas\n"
    "- Resumo de gastos por categoria\n"
    "- Historico de transacoes\n"
    "- Resumo da sua carteira de investimentos\n"
    "- Suas metas financeiras\n"
    "- Projecao de saldo futuro\n"
    "- Informacoes sobre impostos BR 2026"
)

UNKNOWN_TEXT = (
    "Nao entendi sua pergunta. "
    "Tente perguntar sobre saldo, gastos, transacoes, investimentos ou metas. "
    "Digite 'ajuda' para ver o que posso fazer."
)


def fmt_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_saldo(accounts: list[dict]) -> str:
    if not accounts:
        return "Nenhuma conta encontrada."
    lines = ["Saldo das suas contas:"]
    total = 0.0
    for acc in accounts:
        bal = acc["balance"]
        lines.append(f"  {acc['name']} ({acc['bank_name']}): {fmt_brl(bal)}")
        total += bal
    lines.append(f"\nPatrimonio total: {fmt_brl(total)}")
    return "\n".join(lines)


def build_gastos(summary: dict) -> str:
    lines = [f"Gastos de {summary.get('month', '?')}/{summary.get('year', '?')}:"]
    lines.append(f"  Receitas: {fmt_brl(summary.get('income', 0))}")
    lines.append(f"  Despesas: {fmt_brl(abs(summary.get('expenses', 0)))}")
    lines.append(f"  Saldo do mes: {fmt_brl(summary.get('net', 0))}")

    by_cat = summary.get("by_category", {})
    despesas = {k: v for k, v in by_cat.items() if v < 0}
    if despesas:
        lines.append("\nPor categoria:")
        for cat, val in sorted(despesas.items(), key=lambda x: x[1]):
            lines.append(f"  {cat}: {fmt_brl(val)}")
    return "\n".join(lines)


def build_transacoes(transactions: list[dict]) -> str:
    if not transactions:
        return "Nenhuma transacao encontrada."
    lines = [f"Ultimas {len(transactions)} transacoes:"]
    for tx in transactions:
        sinal = "+" if tx["amount"] > 0 else ""
        lines.append(
            f"  {tx['transaction_date']} | {tx['description'][:30]} | "
            f"{sinal}{fmt_brl(tx['amount'])} [{tx['category']}]"
        )
    return "\n".join(lines)


def build_investimentos(portfolio: dict) -> str:
    if portfolio.get("count", 0) == 0:
        return "Nenhum investimento cadastrado."
    lines = [
        "Carteira de Investimentos:",
        f"  Aplicado:    {fmt_brl(portfolio['total_principal'])}",
        f"  Valor atual: {fmt_brl(portfolio['total_current'])}",
        f"  Ganho:       {fmt_brl(portfolio['total_gain'])} ({portfolio['gain_pct']:.2f}%)",
        "\nAlocacao:",
    ]
    for tipo, data in portfolio.get("by_type", {}).items():
        lines.append(f"  {tipo}: {fmt_brl(data['current'])} ({data['allocation_pct']:.1f}%)")
    return "\n".join(lines)


def build_metas(goals: list[dict]) -> str:
    if not goals:
        return "Nenhuma meta cadastrada."
    lines = ["Suas metas:"]
    for g in goals:
        pct = (g["current_amount"] / g["target_amount"] * 100) if g["target_amount"] > 0 else 0
        status = "ATINGIDA" if g["is_achieved"] else f"{pct:.0f}%"
        lines.append(
            f"  {g['name']}: {fmt_brl(g['current_amount'])} / "
            f"{fmt_brl(g['target_amount'])} [{status}]"
        )
    return "\n".join(lines)


def build_projecao(projected_balance: float, trend: str, days: int) -> str:
    trend_map = {"growing": "crescendo", "declining": "caindo", "stable": "estavel"}
    return (
        f"Projecao para {days} dias:\n"
        f"  Saldo projetado: {fmt_brl(projected_balance)}\n"
        f"  Tendencia: {trend_map.get(trend, trend)}"
    )


def build_impostos() -> str:
    return (
        "Impostos sobre investimentos BR 2026:\n"
        "  Renda Fixa (CDB/Tesouro): 17,5% + IOF se < 30 dias\n"
        "  LCI/LCA (novas emissoes): 5%\n"
        "  Acoes: 17,5% | Day trade: 20% | Isento se vendas <= R$60k/trimestre\n"
        "  FII: 5% dividendos + 17,5% ganho de capital\n"
        "  Crypto: 17,5% | Isento se vendas <= R$35k/mes\n"
        "  Carryforward de prejuizo: ate 5 anos"
    )
