"""Lista Sensor web pendentes de inserção a partir do dashboard ou AuraVTC."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parent
HTML = PASTA / "dashboard_produtividade_completo.html"
GERAR_DIR = Path(
    r"C:\Users\luan.machado\Desktop\Área de Trabalho\WorkSpace\Relatórios - Caixa Nova\Indicador de produtividade"
)


def fmt_br_date(value: str) -> str:
    if not value:
        return ""
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value


def carregar_do_html() -> tuple[list[dict], str]:
    html = HTML.read_text(encoding="utf-8")
    start = html.find("const DATA = ") + len("const DATA = ")
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(html[start:], start):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                data = json.loads(html[start : i + 1])
                break
    else:
        raise RuntimeError("Não foi possível ler DATA do HTML.")

    rows = [
        r
        for r in data.get("stage", [])
        if r.get("status") == "pendente" and r.get("equipamento") == "Sensor web"
    ]
    return rows, data.get("generatedAt", "")


def carregar_do_banco() -> tuple[list[dict], str]:
    sys.path.insert(0, str(GERAR_DIR))
    import gerar_indicador as gi  # noqa: E402

    df, df_transito, _, _ = gi.carregar()
    full = pd.concat([df, df_transito], ignore_index=True)
    pend = full[
        (full["status"] == "pendente") & (full["equipamento"] == "Sensor web")
    ].copy()
    rows = []
    for _, r in pend.iterrows():
        rows.append(
            {
                "pedido": str(r["pedido"]),
                "logger": str(r["logger"]),
                "data_coleta": fmt_br_date(
                    pd.Timestamp(r["coleta"]).strftime("%Y-%m-%d")
                    if pd.notna(r.get("coleta"))
                    else ""
                ),
                "data_entrega": fmt_br_date(
                    pd.Timestamp(r["entrega"]).strftime("%Y-%m-%d")
                    if pd.notna(r.get("entrega"))
                    else ""
                ),
                "uf": r.get("uf") or "",
            }
        )
    return rows, datetime.now().strftime("%d/%m/%Y %H:%M (banco)")


def normalizar(rows: list[dict]) -> pd.DataFrame:
    out = []
    for r in rows:
        out.append(
            {
                "Pedido": str(r.get("pedido", "")),
                "Logger": str(r.get("logger", "")),
                "Data coleta": fmt_br_date(r.get("data_coleta", ""))
                if "-" in str(r.get("data_coleta", ""))
                else str(r.get("data_coleta", "")),
                "Data entrega": fmt_br_date(r.get("data_entrega", ""))
                if "-" in str(r.get("data_entrega", ""))
                else str(r.get("data_entrega", "")),
                "UF": str(r.get("uf", "") or ""),
            }
        )
    df = pd.DataFrame(out)
    if df.empty:
        return df
    return df.sort_values(
        ["Data coleta", "Pedido", "Logger"], ascending=[False, True, True]
    ).reset_index(drop=True)


def main() -> int:
    fonte = "html"
    try:
        rows, gerado = carregar_do_html()
    except Exception:
        fonte = "banco"
        rows, gerado = carregar_do_banco()

    df = normalizar(rows)
    xlsx = PASTA / "sensor_web_pendentes.xlsx"
    csv = PASTA / "sensor_web_pendentes.csv"
    df.to_excel(xlsx, index=False, sheet_name="Sensor web pendentes")
    df.to_csv(csv, index=False, sep=";", encoding="utf-8-sig")

    print(f"Fonte: {fonte}")
    print(f"Dados de: {gerado}")
    print(f"Total Sensor web pendentes: {len(df)}")
    print(f"Arquivos: {xlsx.name} | {csv.name}")
    print()
    if df.empty:
        print("Nenhum Sensor web pendente encontrado.")
        return 0

    print("| Pedido | Logger | Data coleta | Data entrega | UF |")
    print("| --- | --- | --- | --- | --- |")
    for _, r in df.iterrows():
        print(
            f"| {r['Pedido']} | {r['Logger']} | {r['Data coleta']} | {r['Data entrega']} | {r['UF']} |"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
