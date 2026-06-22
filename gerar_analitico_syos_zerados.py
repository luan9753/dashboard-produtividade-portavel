"""Analítico completo: Syos pendentes em pedidos sem nada na orders."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pyodbc

GERAR_DIR = Path(
    r"C:\Users\luan.machado\Desktop\Área de Trabalho\WorkSpace\Relatórios - Caixa Nova\Indicador de produtividade"
)
OUT = Path(__file__).resolve().parent
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


def pedidos_com_insercao_orders() -> set[str]:
    conn = pyodbc.connect("DSN=AuraVTC", timeout=180)
    try:
        df = pd.read_sql(
            """
            SELECT DISTINCT btrim(o.order_code) AS pedido
            FROM public.orders o
            JOIN public.order_items oi ON oi.fk_order = o.id
            JOIN public.devices d ON d.id = oi.fk_device
            WHERE d.serial_number IS NOT NULL AND btrim(d.serial_number) <> ''
            """,
            conn,
        )
    finally:
        conn.close()
    return set(df["pedido"].astype(str).str.strip())


def main() -> None:
    print("Carregando AuraVTC...")
    df, df_transito, _, _ = gi.carregar()
    full = pd.concat([df, df_transito], ignore_index=True)
    pend_syos = full[
        (full["status"] == "pendente") & (full["equipamento"] == "Syos")
    ].copy()

    pedidos_inseridos = pedidos_com_insercao_orders()
    pedidos_zero = (
        set(pend_syos["pedido"].astype(str).str.strip()) - pedidos_inseridos
    )
    base = pend_syos[
        pend_syos["pedido"].astype(str).str.strip().isin(pedidos_zero)
    ].copy()
    base = base.sort_values(["coleta", "pedido", "logger"], ascending=[False, True, True])

    qtd_por_pedido = base.groupby("pedido")["logger"].transform("count")

    out = pd.DataFrame(
        {
            "Pedido": base["pedido"].astype(str),
            "Logger": base["logger"].astype(str),
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
            "Chave pedido+logger": base.get("chave", "").fillna("").astype(str),
            "Pedido zerado na orders": "Sim",
            "Qtd loggers Syos pendentes no pedido": qtd_por_pedido.values,
        }
    )

    res_pedido = (
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
        .sort_values(["Data_coleta_max", "Pedido"], ascending=[False, True])
    )

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

    xlsx = OUT / "syos_pendentes_pedidos_zerados_orders.xlsx"
    csv = OUT / "syos_pendentes_pedidos_zerados_orders.csv"

    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        out.to_excel(writer, index=False, sheet_name="Analitico completo")
        res_pedido.to_excel(writer, index=False, sheet_name="Resumo por pedido")
        res_uf.to_excel(writer, index=False, sheet_name="Resumo por UF")
        res_modal.to_excel(writer, index=False, sheet_name="Resumo por modal")
        res_mes.to_excel(writer, index=False, sheet_name="Resumo por mes entrega")
        res_termico.to_excel(writer, index=False, sheet_name="Resumo tipo termico")

    out.to_csv(csv, index=False, sep=";", encoding="utf-8-sig")

    print(f"Pedidos: {len(pedidos_zero)}")
    print(f"Loggers: {len(out)}")
    print(f"Excel: {xlsx}")
    print(f"CSV: {csv}")


if __name__ == "__main__":
    main()
