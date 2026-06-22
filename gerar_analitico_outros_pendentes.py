"""Analítico completo: TODOS os Outros pendentes (entregues no stage, sem cadastro na orders)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

GERAR_DIR = Path.home() / "Desktop/Área de Trabalho/WorkSpace/Relatórios - Caixa Nova/Indicador de produtividade"
if not GERAR_DIR.exists():
    GERAR_DIR = Path.home() / "Desktop/WorkSpace/Relatórios - Caixa Nova/Indicador de produtividade"
OUT = Path(__file__).resolve().parent
CORTE_ENTREGA = pd.Timestamp("2026-05-27")
EQUIPAMENTO = "Outros"
sys.path.insert(0, str(GERAR_DIR))
import gerar_indicador as gi  # noqa: E402


def fmt_dt(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return pd.Timestamp(value).strftime("%d/%m/%Y %H:%M")


def fmt_date(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return pd.Timestamp(value).strftime("%d/%m/%Y")


def uniq_join(series: pd.Series) -> str:
    vals = sorted({str(v).strip() for v in series if str(v).strip() and str(v).lower() != "nan"})
    return ", ".join(vals)


def resumo_por_pedido(out: pd.DataFrame) -> pd.DataFrame:
    if out.empty:
        return pd.DataFrame()
    return (
        out.groupby("Pedido", as_index=False)
        .agg(
            Qtd_loggers=("Logger", "count"),
            UF=("UF", lambda s: next((x for x in s if str(x).strip()), "")),
            Modal=("Modal", uniq_join),
            Embalagens=("Embalagem", uniq_join),
            Tipos_termicos=("Tipo termico", uniq_join),
            Data_coleta_min=("Data coleta (so data)", "min"),
            Data_coleta_max=("Data coleta (so data)", "max"),
            Data_entrega_min=("Data entrega (so data)", lambda s: min([x for x in s if x], default="")),
            Data_entrega_max=("Data entrega (so data)", lambda s: max([x for x in s if x], default="")),
            Loggers=("Logger", lambda s: ", ".join(sorted(s.astype(str)))),
        )
        .sort_values(["Data_entrega_max", "Pedido"], ascending=[False, True])
    )


def main() -> None:
    print("Carregando AuraVTC...")
    df, _, _, _ = gi.carregar()
    base = df[(df["status"] == "pendente") & (df["equipamento"] == EQUIPAMENTO)].copy()
    base = base.sort_values(["coleta", "pedido", "logger"], ascending=[False, True, True])
    qtd_por_pedido = base.groupby("pedido")["logger"].transform("count")

    out = pd.DataFrame(
        {
            "Pedido": base["pedido"].astype(str),
            "Logger": base["logger"].astype(str),
            "Prefixo logger": base["logger"].astype(str).str[:2].str.upper(),
            "UF": base.get("uf", "").fillna("").astype(str),
            "Modal": base.get("modal", "").fillna("").astype(str),
            "Embalagem": base.get("embalagem", "").fillna("").astype(str),
            "Faixa termica": base.get("faixa_termica", "").fillna("").astype(str),
            "Tipo termico": base.get("tipo_termico", "").fillna("").astype(str),
            "Equipamento": base.get("equipamento", "").fillna("").astype(str),
            "Status stage": base.get("status", "").fillna("").astype(str),
            "Data coleta": base["coleta"].map(fmt_dt),
            "Data entrega": base["entrega"].map(fmt_dt),
            "Data coleta (so data)": base["coleta"].map(fmt_date),
            "Data entrega (so data)": base["entrega"].map(fmt_date),
            "Mes coleta": base.get("mes_coleta", "").fillna("").astype(str),
            "Mes entrega": base.get("mes_entrega", "").fillna("").astype(str),
            f"Qtd {EQUIPAMENTO} pendentes no pedido": qtd_por_pedido.values,
        }
    )

    entrega_dt = pd.to_datetime(base["entrega"], errors="coerce")
    antes = out[entrega_dt < CORTE_ENTREGA].copy()
    apos = out[entrega_dt >= CORTE_ENTREGA].copy()
    sem_entrega = out[entrega_dt.isna()].copy()

    res_pedido = resumo_por_pedido(out)
    res_antes = resumo_por_pedido(antes)
    res_apos = resumo_por_pedido(apos)

    res_uf = (
        out.groupby("UF", as_index=False)
        .agg(Pedidos=("Pedido", "nunique"), Loggers=("Logger", "count"))
        .sort_values("Loggers", ascending=False)
    )
    res_modal = (
        out.groupby("Modal", as_index=False)
        .agg(Pedidos=("Pedido", "nunique"), Loggers=("Logger", "count"))
        .sort_values("Loggers", ascending=False)
    )
    res_mes = (
        out.groupby("Mes entrega", as_index=False)
        .agg(Pedidos=("Pedido", "nunique"), Loggers=("Logger", "count"))
        .sort_values("Mes entrega", ascending=False)
    )
    res_termico = (
        out.groupby("Tipo termico", as_index=False)
        .agg(Pedidos=("Pedido", "nunique"), Loggers=("Logger", "count"))
        .sort_values("Loggers", ascending=False)
    )
    res_prefixo = (
        out.groupby("Prefixo logger", as_index=False)
        .agg(Pedidos=("Pedido", "nunique"), Loggers=("Logger", "count"))
        .sort_values("Loggers", ascending=False)
    )

    xlsx = OUT / "outros_pendentes_analitico.xlsx"
    csv = OUT / "outros_pendentes_analitico.csv"

    resumo_corte = pd.DataFrame(
        [
            {
                "Corte entrega": "Antes de 27/05/2026",
                "Pedidos": antes["Pedido"].nunique(),
                "Loggers": len(antes),
            },
            {
                "Corte entrega": "A partir de 27/05/2026",
                "Pedidos": apos["Pedido"].nunique(),
                "Loggers": len(apos),
            },
            {
                "Corte entrega": "Sem data de entrega",
                "Pedidos": sem_entrega["Pedido"].nunique(),
                "Loggers": len(sem_entrega),
            },
            {
                "Corte entrega": "Total",
                "Pedidos": out["Pedido"].nunique(),
                "Loggers": len(out),
            },
        ]
    )

    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        antes.to_excel(writer, index=False, sheet_name="Entrega antes 27-05-2026")
        apos.to_excel(writer, index=False, sheet_name="Entrega apos 27-05-2026")
        resumo_corte.to_excel(writer, index=False, sheet_name="Resumo corte entrega")
        res_antes.to_excel(writer, index=False, sheet_name="Resumo pedidos antes")
        res_apos.to_excel(writer, index=False, sheet_name="Resumo pedidos apos")
        out.to_excel(writer, index=False, sheet_name="Analitico completo")
        res_pedido.to_excel(writer, index=False, sheet_name="Resumo por pedido")
        res_prefixo.to_excel(writer, index=False, sheet_name="Resumo por prefixo")
        res_uf.to_excel(writer, index=False, sheet_name="Resumo por UF")
        res_modal.to_excel(writer, index=False, sheet_name="Resumo por modal")
        res_mes.to_excel(writer, index=False, sheet_name="Resumo por mes entrega")
        res_termico.to_excel(writer, index=False, sheet_name="Resumo tipo termico")
        if not sem_entrega.empty:
            sem_entrega.to_excel(writer, index=False, sheet_name="Sem data entrega")

    out.to_csv(csv, index=False, sep=";", encoding="utf-8-sig")
    antes.to_csv(
        OUT / "outros_pendentes_antes_27-05-2026.csv",
        index=False,
        sep=";",
        encoding="utf-8-sig",
    )
    apos.to_csv(
        OUT / "outros_pendentes_apos_27-05-2026.csv",
        index=False,
        sep=";",
        encoding="utf-8-sig",
    )

    print(f"Total pedidos: {out['Pedido'].nunique()} | loggers: {len(out)}")
    print(f"  Antes 27/05/2026: {antes['Pedido'].nunique()} pedidos | {len(antes)} loggers")
    print(f"  A partir 27/05/2026: {apos['Pedido'].nunique()} pedidos | {len(apos)} loggers")
    if len(sem_entrega):
        print(f"  Sem data entrega: {sem_entrega['Pedido'].nunique()} pedidos | {len(sem_entrega)} loggers")
    print(f"Excel: {xlsx}")
    print(f"CSV: {csv}")


if __name__ == "__main__":
    main()
