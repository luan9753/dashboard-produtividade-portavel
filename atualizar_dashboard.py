"""Atualiza dashboard_produtividade_completo.html com dados frescos do AuraVTC."""
from __future__ import annotations

import json
import shutil
import sys
import warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

GERAR_DIR = Path(
    r"C:\Users\luan.machado\Desktop\Área de Trabalho\WorkSpace\Relatórios - Caixa Nova\Indicador de produtividade"
)
BACKUP_ORIGEM = Path(
    r"C:\Users\luan.machado\Desktop\Área de Trabalho\WorkSpace\Indicador produtividade dashboard\dashboard_produtividade_completo.html"
)
sys.path.insert(0, str(GERAR_DIR))
import gerar_indicador as gi  # noqa: E402

PASTA = Path(__file__).resolve().parent
HTML_PATH = PASTA / "dashboard_produtividade_completo.html"
TZ = ZoneInfo("America/Sao_Paulo")


def fmt_date(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def serializar_stage_entregue(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "pedido": str(r["pedido"]),
                "logger": str(r["logger"]),
                "uf": r["uf"] or "",
                "embalagem": r["embalagem"] or "",
                "faixa": r["faixa_termica"] or "",
                "equipamento": r.get("equipamento") or gi.classificar_equipamento(str(r["logger"])),
                "modal": gi.normalizar_modal(r.get("modal")),
                "tipo_termico": r.get("tipo_termico")
                or gi.classificar_tipo_termico(r.get("faixa_termica") or ""),
                "status": r["status"],
                "data_coleta": fmt_date(r["coleta"]),
                "data_entrega": fmt_date(r["entrega"]),
                "mes_entrega": r.get("mes_entrega") or gi.mes_de_data(r["entrega"]) or "",
            }
        )
    return rows


def serializar_stage_transito(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "pedido": str(r["pedido"]),
                "logger": str(r["logger"]),
                "uf": r["uf"] or "",
                "embalagem": r["embalagem"] or "",
                "faixa": r["faixa_termica"] or "",
                "equipamento": r.get("equipamento") or gi.classificar_equipamento(str(r["logger"])),
                "modal": gi.normalizar_modal(r.get("modal")),
                "tipo_termico": r.get("tipo_termico")
                or gi.classificar_tipo_termico(r.get("faixa_termica") or ""),
                "status": "em_transito",
                "data_coleta": fmt_date(r["coleta"]),
                "data_entrega": "",
                "mes_entrega": "",
            }
        )
    return rows


def serializar_sla_dashboard(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "order_item_id": str(r["order_item_id"]),
                "pedido": str(r["pedido"]),
                "logger": str(r["logger"]),
                "cliente": r.get("cliente") or "",
                "equipamento": r["equipamento"],
                "modal": gi.normalizar_modal(r.get("modal")),
                "data_entrega": fmt_date(r["entrega"]),
                "mes_entrega": r.get("mes_entrega") or gi.mes_de_data(r["entrega"]) or "",
                "data_inclusao": fmt_date(r["inclusao"]),
                "dias": int(r["dias_inclusao"]) if pd.notna(r["dias_inclusao"]) else 0,
                "status_sla": "dentro" if r["dentro_sla"] else "fora",
            }
        )
    return rows


def build_payload(
    df: pd.DataFrame,
    df_transito: pd.DataFrame,
    so_ord: pd.DataFrame,
    df_sla: pd.DataFrame,
) -> dict:
    stage = serializar_stage_entregue(df) + serializar_stage_transito(df_transito)
    return {
        "generatedAt": datetime.now(TZ).strftime("%d/%m/%Y %H:%M"),
        "params": {
            "dataMin": gi.DATA_MIN,
            "slaDataMin": gi.SLA_DATA_MIN,
            "slaPrazoDias": gi.SLA_PRAZO_DIAS,
            "dsn": "AuraVTC",
            "pedidosExcluidosSla": len(gi.SLA_PEDIDOS_EXCLUIR),
        },
        "onlyOrder": len(so_ord),
        "stage": stage,
        "sla": serializar_sla_dashboard(df_sla),
    }


def html_esta_integrado(content: str) -> bool:
    return (
        "const DATA = " in content
        and "const stage" in content
        and "function render" in content
        and "</script>" in content
        and content.strip().endswith("</html>")
    )


def aplicar_patches_visuais() -> None:
    """Garante títulos, ids, CSS e JS (Outros→Syos) após restore/atualização."""
    content = HTML_PATH.read_text(encoding="utf-8")
    changed = False

    panel_replacements = [
        (
            '<article class="panel span3"><h2>Pend&ecirc;ncias por tipo de equipamento</h2>'
            '<div class="scroll" id="chartEquip"></div></article>',
            '<article class="panel span3" id="panel-equip-pending"><h2>Pend&ecirc;ncia por equipamento</h2>'
            '<div class="scroll" id="chartEquip"></div></article>',
        ),
        (
            '<article class="panel span3" id="panel-equip-pending"><h2>Pend&ecirc;ncias por tipo de equipamento</h2>'
            '<div class="scroll" id="chartEquip"></div></article>',
            '<article class="panel span3" id="panel-equip-pending"><h2>Pend&ecirc;ncia por equipamento</h2>'
            '<div class="scroll" id="chartEquip"></div></article>',
        ),
        (
            '<article class="panel span3"><h2>Pend&ecirc;ncias por m&ecirc;s de entrega</h2>'
            '<div class="scroll" id="chartMonth"></div></article>',
            '<article class="panel span3" id="panel-month-pending"><h2>Pend&ecirc;ncia por m&ecirc;s</h2>'
            '<div class="scroll" id="chartMonth"></div></article>',
        ),
        (
            '<article class="panel span3"><h2>% de loggers Ares no prazo por m&ecirc;s</h2>'
            '<div class="scroll" id="chartSlaMonth"></div></article>',
            '<article class="panel span3" id="panel-sla-month"><h2>% loggers Ares no prazo por m&ecirc;s</h2>'
            '<div class="scroll" id="chartSlaMonth"></div></article>',
        ),
        (
            '<article class="panel span3"><h2>Pend&ecirc;ncias por tipo t&eacute;rmico</h2>'
            '<div class="scroll" id="chartThermal"></div></article>',
            '<article class="panel span3" id="panel-thermal-pending"><h2>Pend&ecirc;ncia por tipo t&eacute;rmico</h2>'
            '<div class="scroll" id="chartThermal"></div></article>',
        ),
    ]
    for old, new in panel_replacements:
        if old in content:
            content = content.replace(old, new, 1)
            changed = True

    link = '<link rel="stylesheet" href="equip-card-overrides.css">'
    if link not in content:
        content = content.replace("</head>", f"  {link}\n</head>", 1)
        changed = True

    if '<section class="cards">' in content and 'id="kpi-cards"' not in content:
        content = content.replace(
            '<section class="cards">',
            '<section class="cards" id="kpi-cards">',
            1,
        )
        changed = True

    js_helpers = (
        'function mergeOutrosSyos(v){ return v==="Outros"?"Syos":(v||"Sem categoria"); }\n'
        '    function groupEquip(rows, pred=()=>true){\n'
        '      return group(rows.map(r=>({...r,equipamento:mergeOutrosSyos(r.equipamento)})),"equipamento",pred);\n'
        "    }\n"
    )
    if "function mergeOutrosSyos" not in content:
        anchor = (
            'function group(rows, field, pred=()=>true){\n'
            '      const m=new Map(); rows.forEach(r=>{ if(!pred(r)) return; const k=r[field] || "Sem categoria"; m.set(k,(m.get(k)||0)+1); });\n'
            '      return [...m.entries()].map(([label,value])=>({label,value})).sort((a,b)=>b.value-a.value || a.label.localeCompare(b.label));\n'
            "    }\n"
        )
        if anchor in content:
            content = content.replace(anchor, anchor + "    " + js_helpers, 1)
            changed = True

    old_charts = (
        'chart("chartEquip",group(fs,"equipamento",r=>r.status==="pendente")); '
        'chart("chartMonth",group(fs,"mes_entrega",r=>r.status==="pendente")); '
        'chart("chartThermal",group(fs,"tipo_termico",r=>r.status==="pendente")); '
        'chartUfMap("chartUf",group(fs,"uf",r=>r.status==="pendente")); '
        'chart("chartTransit",group(fs,"equipamento",r=>r.status==="em_transito"));'
    )
    new_charts = (
        'chart("chartEquip",groupEquip(fs,r=>r.status==="pendente")); '
        'chart("chartMonth",group(fs,"mes_entrega",r=>r.status==="pendente")); '
        'chart("chartThermal",group(fs,"tipo_termico",r=>r.status==="pendente")); '
        'chartUfMap("chartUf",group(fs,"uf",r=>r.status==="pendente")); '
        'chart("chartTransit",groupEquip(fs,r=>r.status==="em_transito"));'
    )
    if old_charts in content:
        content = content.replace(old_charts, new_charts, 1)
        changed = True

    old_sla = (
        'function slaGroup(rows, field, aresOnly=false){\n'
        '      const m=new Map(); rows.forEach(r=>{ if(aresOnly && !["Ares","Ares com sonda"].includes(r.equipamento)) return; const k=r[field] || "Sem categoria"; const o=m.get(k)||{label:k,total:0,dentro:0,fora:0}; o.total++; if(r.status_sla==="dentro") o.dentro++; else o.fora++; m.set(k,o); });\n'
        '      return [...m.values()].sort((a,b)=>String(a.label).localeCompare(String(b.label)));\n'
        "    }"
    )
    new_sla = (
        'function slaGroup(rows, field, aresOnly=false){\n'
        '      const m=new Map(); rows.forEach(r=>{ if(aresOnly && !["Ares","Ares com sonda"].includes(r.equipamento)) return; const raw=r[field] || "Sem categoria"; const k=field==="equipamento"?mergeOutrosSyos(raw):raw; const o=m.get(k)||{label:k,total:0,dentro:0,fora:0}; o.total++; if(r.status_sla==="dentro") o.dentro++; else o.fora++; m.set(k,o); });\n'
        '      return [...m.values()].sort((a,b)=>String(a.label).localeCompare(String(b.label)));\n'
        "    }"
    )
    if old_sla in content and "mergeOutrosSyos(raw)" not in content:
        content = content.replace(old_sla, new_sla, 1)
        changed = True

    modal_filter_html = (
        '<div class="filter"><label>Modal</label>'
        '<select id="modalFilter">'
        '<option value="Todos">Todos</option>'
        '<option value="Rodovi\u00e1rio">Rodovi\u00e1rio</option>'
        '<option value="MultiModal">MultiModal</option>'
        "</select></div>"
    )
    status_filter_end = (
        '<option value="em_transito">Em tr&acirc;nsito</option></select></div>'
    )
    if 'id="modalFilter"' not in content and status_filter_end in content:
        content = content.replace(
            status_filter_end,
            status_filter_end + "\n      " + modal_filter_html,
            1,
        )
        changed = True

    old_filtered_stage = (
        'function filteredStage(){\n'
        '      const ds=byId("dateStart").value, de=byId("dateEnd").value, st=byId("statusFilter").value, eq=byId("equipFilter").value, th=byId("thermalFilter").value, uf=byId("ufFilter").value, q=byId("searchFilter").value.trim().toUpperCase();\n'
        '      return stage.filter(r => {\n'
        '        const d = stageDate(r) || "";\n'
        '        return (!ds || d >= ds) && (!de || d <= de) && (st==="Todos" || r.status===st) && (eq==="Todos" || r.equipamento===eq) && (th==="Todos" || r.tipo_termico===th) && (uf==="Todos" || r.uf===uf) && (!q || `${r.pedido} ${r.logger}`.toUpperCase().includes(q));\n'
        "      });\n"
        "    }"
    )
    new_filtered_stage = (
        'function filteredStage(){\n'
        '      const ds=byId("dateStart").value, de=byId("dateEnd").value, st=byId("statusFilter").value, md=byId("modalFilter").value, eq=byId("equipFilter").value, th=byId("thermalFilter").value, uf=byId("ufFilter").value, q=byId("searchFilter").value.trim().toUpperCase();\n'
        '      return stage.filter(r => {\n'
        '        const d = stageDate(r) || "";\n'
        '        return (!ds || d >= ds) && (!de || d <= de) && (st==="Todos" || r.status===st) && (md==="Todos" || r.modal===md) && (eq==="Todos" || r.equipamento===eq) && (th==="Todos" || r.tipo_termico===th) && (uf==="Todos" || r.uf===uf) && (!q || `${r.pedido} ${r.logger}`.toUpperCase().includes(q));\n'
        "      });\n"
        "    }"
    )
    if old_filtered_stage in content:
        content = content.replace(old_filtered_stage, new_filtered_stage, 1)
        changed = True

    old_filtered_sla = (
        'function filteredSla(){\n'
        '      const ds=byId("dateStart").value, de=byId("dateEnd").value, eq=byId("equipFilter").value, q=byId("searchFilter").value.trim().toUpperCase();\n'
        '      return sla.filter(r => (!ds || r.data_entrega >= ds) && (!de || r.data_entrega <= de) && (eq==="Todos" || r.equipamento===eq) && (!q || `${r.pedido} ${r.logger} ${r.cliente}`.toUpperCase().includes(q)));\n'
        "    }"
    )
    new_filtered_sla = (
        'function filteredSla(){\n'
        '      const ds=byId("dateStart").value, de=byId("dateEnd").value, md=byId("modalFilter").value, eq=byId("equipFilter").value, q=byId("searchFilter").value.trim().toUpperCase();\n'
        '      return sla.filter(r => (!ds || r.data_entrega >= ds) && (!de || r.data_entrega <= de) && (md==="Todos" || r.modal===md) && (eq==="Todos" || r.equipamento===eq) && (!q || `${r.pedido} ${r.logger} ${r.cliente}`.toUpperCase().includes(q)));\n'
        "    }"
    )
    if old_filtered_sla in content:
        content = content.replace(old_filtered_sla, new_filtered_sla, 1)
        changed = True

    old_listeners = (
        '["dateStart","dateEnd","statusFilter","equipFilter","thermalFilter","ufFilter","searchFilter"]'
    )
    new_listeners = (
        '["dateStart","dateEnd","statusFilter","modalFilter","equipFilter","thermalFilter","ufFilter","searchFilter"]'
    )
    if old_listeners in content:
        content = content.replace(old_listeners, new_listeners, 1)
        changed = True

    if "grid-template-columns:repeat(7,1fr)" in content:
        content = content.replace(
            "grid-template-columns:repeat(7,1fr)",
            "grid-template-columns:repeat(8,1fr)",
            1,
        )
        changed = True
    if "grid-template-columns:repeat(7,minmax(0,1fr))" in content:
        content = content.replace(
            "grid-template-columns:repeat(7,minmax(0,1fr))",
            "grid-template-columns:repeat(8,minmax(0,1fr))",
            1,
        )
        changed = True

    if changed:
        HTML_PATH.write_text(content, encoding="utf-8")


def restaurar_html_se_necessario() -> None:
    if HTML_PATH.exists() and html_esta_integrado(HTML_PATH.read_text(encoding="utf-8")):
        aplicar_patches_visuais()
        return
    if not BACKUP_ORIGEM.exists():
        raise RuntimeError(
            "HTML corrompido e backup não encontrado em:\n"
            f"  {BACKUP_ORIGEM}\n"
            "Copie manualmente um dashboard_produtividade_completo.html completo para esta pasta."
        )
    print("  HTML incompleto detectado — restaurando cópia íntegra do WorkSpace...")
    shutil.copy2(BACKUP_ORIGEM, HTML_PATH)
    aplicar_patches_visuais()


def localizar_bloco_data(content: str) -> tuple[int, int]:
    marker = "const DATA = "
    start = content.find(marker)
    if start == -1:
        raise RuntimeError("Marcador 'const DATA = ' não encontrado no HTML.")

    json_start = start + len(marker)
    if json_start >= len(content) or content[json_start] != "{":
        raise RuntimeError("HTML corrompido: JSON de DATA não começa com '{'.")

    depth = 0
    in_string = False
    escape = False
    for i in range(json_start, len(content)):
        ch = content[i]
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
                json_end = i + 1
                if json_end >= len(content) or content[json_end] != ";":
                    raise RuntimeError("HTML corrompido: ';' esperado após o JSON de DATA.")
                return json_start, json_end

    raise RuntimeError(
        "HTML corrompido: JSON de DATA não fecha.\n"
        "Restaure o arquivo completo (WorkSpace) e tente novamente."
    )


def patch_html(payload: dict) -> None:
    content = HTML_PATH.read_text(encoding="utf-8")
    if not html_esta_integrado(content):
        raise RuntimeError(
            "HTML incompleto ou corrompido (falta JavaScript ou </html>).\n"
            "Execute novamente — o script tentará restaurar do WorkSpace automaticamente."
        )

    json_start, json_end = localizar_bloco_data(content)
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    new_content = content[:json_start] + data_json + content[json_end:]
    if not html_esta_integrado(new_content):
        raise RuntimeError("Substituição de DATA geraria HTML inválido. Nada foi gravado.")

    backup = HTML_PATH.with_suffix(".html.bak")
    shutil.copy2(HTML_PATH, backup)
    tmp = HTML_PATH.with_suffix(".html.tmp")
    tmp.write_text(new_content, encoding="utf-8")
    tmp.replace(HTML_PATH)


def main() -> int:
    warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable")
    restaurar_html_se_necessario()
    print("Consultando AuraVTC...")
    df, df_transito, so_ord, df_sla = gi.carregar()
    payload = build_payload(df, df_transito, so_ord, df_sla)
    print(f"  Stage: {len(payload['stage'])} (entregues {len(df)}, trânsito {len(df_transito)})")
    print(f"  SLA: {len(payload['sla'])}")
    print(f"  onlyOrder: {payload['onlyOrder']}")
    print(f"  Gerado em: {payload['generatedAt']}")
    patch_html(payload)
    aplicar_patches_visuais()
    print(f"HTML atualizado: {HTML_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
