"""
Monta o corpo HTML (e a versao em texto puro) do e-mail diario do Morning Call.

Todo o estilo fica inline e o layout usa tabelas: e o que Gmail e Outlook
renderizam de forma confiavel (eles ignoram <style>, flexbox e fontes web).
"""
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from config import CATEGORIES

BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")

# Paleta Integrity (preto + dourado do logo)
PRETO = "#111111"
DOURADO = "#B8975A"
FUNDO = "#F4F2EE"
TEXTO = "#2B2B2B"
CINZA = "#7A7A7A"
VERDE = "#1E7B4A"
VERMELHO = "#B3261E"

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

# Indicadores que aparecem no e-mail (chave em market_data -> nome curto).
# O dashboard continua mostrando todos; no e-mail ficam so os principais.
EMAIL_INDICADORES = [
    ("Ibovespa", "Ibovespa"),
    ("S&P 500", "S&P 500"),
    ("USD/BRL", "Dólar"),
    ("Selic", "Selic"),
    ("Petróleo (Brent)", "Brent"),
]

# Quantas manchetes entram no bloco "Destaques do dia" (1 por categoria)
MAX_DESTAQUES = 5


def _data_extenso(d) -> str:
    return f"{DIAS[d.weekday()].capitalize()}, {d.day} de {MESES[d.month - 1]} de {d.year}"


def _fmt_valor(label, value):
    if value is None:
        return None
    if label in ("Ibovespa", "S&P 500"):
        return f"{value:,.0f}".replace(",", ".")
    if label == "USD/BRL":
        return f"R$ {value:.2f}".replace(".", ",")
    if label == "Selic":
        return f"{value:.2f}%".replace(".", ",")
    if label == "Petróleo (Brent)":
        return f"US$ {value:.2f}".replace(".", ",")
    return str(value)


def _indicadores(market_data):
    itens = []
    for chave, nome in EMAIL_INDICADORES:
        m = (market_data or {}).get(chave) or {}
        valor = _fmt_valor(chave, m.get("value"))
        if valor is None:
            continue
        itens.append({"nome": nome, "valor": valor, "variacao": m.get("change_pct")})
    return itens


def _destaques(news):
    """Pega a 1a noticia de cada categoria (na ordem do config) ate MAX_DESTAQUES."""
    itens = []
    for chave, titulo_cat, _icone, _qtd in CATEGORIES:
        lista = (news or {}).get(chave) or []
        if lista:
            n = lista[0]
            itens.append({"categoria": titulo_cat, "titulo": n.get("title", ""),
                          "fonte": n.get("source", ""), "link": n.get("link", "")})
        if len(itens) >= MAX_DESTAQUES:
            break
    return itens


def _bloco_indicadores(indicadores):
    if not indicadores:
        return ""
    celulas = []
    for i, ind in enumerate(indicadores):
        borda = "" if i == len(indicadores) - 1 else "border-right:1px solid #ECE7DD;"
        var = ind.get("variacao")
        var_html = ""
        if var is not None:
            cor = VERDE if var >= 0 else VERMELHO
            seta = "▲" if var >= 0 else "▼"
            pct = f"{var:+.2f}%".replace(".", ",")
            var_html = f'<div style="font-size:12px;color:{cor};font-weight:bold;">{seta} {pct}</div>'
        celulas.append(
            f'<td align="center" valign="top" width="{100 // len(indicadores)}%" style="padding:12px 4px;{borda}">'
            f'<div style="font-size:11px;color:{CINZA};text-transform:uppercase;letter-spacing:1px;">'
            f'{escape(ind["nome"])}</div>'
            f'<div style="font-size:16px;color:{PRETO};font-weight:bold;padding:4px 0 2px;">'
            f'{escape(ind["valor"])}</div>{var_html}</td>'
        )
    return f"""
        <tr><td style="padding:0 32px 8px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                 style="background:#FBFAF7;border:1px solid #ECE7DD;border-radius:6px;">
            <tr>{''.join(celulas)}</tr>
          </table>
        </td></tr>"""


def _bloco_destaques(destaques):
    if not destaques:
        return ""
    linhas = []
    for i, d in enumerate(destaques):
        borda = "" if i == len(destaques) - 1 else "border-bottom:1px solid #EFEFEF;"
        titulo = escape(d["titulo"])
        if d.get("link"):
            titulo = (f'<a href="{escape(d["link"], quote=True)}" target="_blank" '
                      f'style="color:{PRETO};text-decoration:none;">{titulo}</a>')
        fonte = (f'<div style="font-size:12px;color:{CINZA};padding-top:3px;">{escape(d["fonte"])}</div>'
                 if d.get("fonte") else "")
        linhas.append(
            f'<tr><td style="padding:12px 0;{borda}">'
            f'<div style="font-size:10px;color:{DOURADO};font-weight:bold;text-transform:uppercase;'
            f'letter-spacing:1.2px;padding-bottom:3px;">{escape(d["categoria"])}</div>'
            f'<div style="font-size:15px;color:{PRETO};font-weight:bold;line-height:21px;">{titulo}</div>'
            f'{fonte}</td></tr>'
        )
    return f"""
        <tr><td style="padding:20px 32px 0;">
          <div style="font-size:12px;color:{PRETO};font-weight:bold;text-transform:uppercase;
                      letter-spacing:1.5px;border-left:3px solid {DOURADO};padding-left:10px;">
            Destaques do dia</div>
        </td></tr>
        <tr><td style="padding:4px 32px 0;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            {''.join(linhas)}
          </table>
        </td></tr>"""


def montar_email(dashboard_url, news=None, market_data=None, saudacao="Bom dia, time!"):
    """Retorna (html, texto). news e market_data sao opcionais: sem eles sai so saudacao + botao."""
    hoje = datetime.now(BRASILIA_TZ).date()
    data_txt = _data_extenso(hoje)
    destaques = _destaques(news)
    link = escape(dashboard_url, quote=True)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Morning Call — Integrity</title></head>
<body style="margin:0;padding:0;background:{FUNDO};">
<div style="display:none;max-height:0;overflow:hidden;">Morning Call de {data_txt}: destaques do mercado e link para o relatório completo.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{FUNDO};">
<tr><td align="center" style="padding:24px 12px;">
  <table role="presentation" width="600" cellpadding="0" cellspacing="0"
         style="width:100%;max-width:600px;background:#FFFFFF;border-radius:8px;overflow:hidden;
                font-family:Helvetica,Arial,sans-serif;color:{TEXTO};">

    <tr><td style="background:{PRETO};padding:26px 32px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="font-family:Georgia,'Times New Roman',serif;font-size:20px;letter-spacing:5px;color:{DOURADO};">
          INTEGRITY
          <div style="font-family:Helvetica,Arial,sans-serif;font-size:9px;letter-spacing:3px;color:#8C7A55;padding-top:2px;">
            WEALTH MANAGEMENT</div>
        </td>
        <td align="right" style="font-size:11px;color:#BFBFBF;text-transform:uppercase;letter-spacing:2px;">
          Morning Call</td>
      </tr></table>
    </td></tr>
    <tr><td style="height:3px;background:{DOURADO};font-size:0;line-height:0;">&nbsp;</td></tr>

    <tr><td style="padding:28px 32px 18px;">
      <div style="font-size:12px;color:{CINZA};padding-bottom:6px;">{data_txt}</div>
      <div style="font-size:24px;font-weight:bold;color:{PRETO};padding-bottom:8px;">{escape(saudacao)}</div>
      <div style="font-size:15px;line-height:22px;color:{TEXTO};">
        O Morning Call de hoje já está disponível. Confira um resumo abaixo e acesse o relatório completo.</div>
    </td></tr>

    {_bloco_indicadores(_indicadores(market_data))}
    {_bloco_destaques(destaques)}

    <tr><td align="center" style="padding:28px 32px 32px;">
      <table role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td align="center" bgcolor="{PRETO}" style="border-radius:6px;">
          <a href="{link}" target="_blank"
             style="display:inline-block;padding:14px 34px;font-size:15px;font-weight:bold;
                    color:{DOURADO};text-decoration:none;border-radius:6px;letter-spacing:.5px;">
            Abrir o Morning Call completo &rarr;</a>
        </td></tr></table>
    </td></tr>

    <tr><td style="background:#FAF8F4;border-top:1px solid #ECE7DD;padding:18px 32px;
                   font-size:11px;line-height:17px;color:{CINZA};">
      Bom trabalho! &middot; Integrity Wealth Management<br>
      Uso interno. Conteúdo informativo, não constitui recomendação de investimento.
    </td></tr>
  </table>
</td></tr></table>
</body></html>"""

    linhas = [saudacao, "", f"Morning Call — {data_txt}", ""]
    for d in destaques:
        linhas.append(f"• [{d['categoria']}] {d['titulo']}")
    linhas += ["", f"Relatório completo: {dashboard_url}", "", "Bom trabalho!"]
    return html, "\n".join(linhas)


if __name__ == "__main__":
    # Preview com dados ficticios: python email_template.py  -> abre preview_email.html
    fake_news = {
        "cambio_juros": [{"title": "Exemplo de manchete sobre juros", "source": "Valor Econômico", "link": "https://example.com"}],
        "bolsa": [{"title": "Exemplo de manchete sobre a bolsa", "source": "InfoMoney", "link": "https://example.com"}],
        "internacional": [{"title": "Exemplo de manchete internacional", "source": "Reuters", "link": "https://example.com"}],
    }
    fake_market = {
        "Ibovespa": {"value": 128450, "change_pct": 0.84},
        "S&P 500": {"value": 6812.4, "change_pct": -0.42},
        "USD/BRL": {"value": 5.42, "change_pct": -0.31},
        "Selic": {"value": 15.0, "change_pct": None},
        "Petróleo (Brent)": {"value": 64.2, "change_pct": 1.1},
    }
    html, _ = montar_email("https://theointegrity.github.io/morning-call/", fake_news, fake_market)
    with open("preview_email.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("gerado preview_email.html")
