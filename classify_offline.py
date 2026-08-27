"""
Classifica e filtra notícias usando apenas regras de palavras-chave -- sem
chamar nenhuma API paga. Mais simples que a versão com IA (summarize_news.py),
mas roda de graça.

Como funciona:
1. Cada notícia é comparada contra listas de palavras-chave por categoria.
2. A primeira categoria (na ordem de config.CATEGORIES) cujo palavra-chave
   aparecer no título/resumo da notícia é escolhida.
3. Se o histórico de feedback (like/dislike) estiver disponível, notícias de
   fontes historicamente bem avaliadas são priorizadas dentro de cada
   categoria.
4. Respeita o limite de itens por categoria definido em config.CATEGORIES.

Limitação: como não há um modelo de linguagem envolvido, o título exibido é
o título original da notícia (sem reescrita/resumo), e a classificação pode
errar em notícias ambíguas ou que não usem as palavras-chave esperadas.
"""
import re

from config import CATEGORIES

CATEGORY_KEYWORDS = {
    "cambio_juros": [
        "dólar", "dolar", "câmbio", "cambio", "real (moeda)", "juro", "juros",
        "selic", "copom", "taxa de juros", "inflação", "inflacao", "ipca",
        "banco central", "bcb",
    ],
    "bolsa": [
        # foco em bolsa/empresas brasileiras -- evita capturar qualquer
        # notícia de "ações" de empresas estrangeiras (isso vai para
        # "internacional")
        "ibovespa", "bovespa", "b3", "bolsa brasileira", "pregão da b3",
        "mercado acionário brasileiro", "small cap", "small caps",
        "blue chip", "blue chips",
    ],
    "empresas": [
        "petrobras", "ações da vale", "mineradora vale", "itaú", "itau",
        "bradesco", "banco do brasil", "ambev", "weg", "magazine luiza",
        "magalu",
        # resultados/balanços de empresas (earnings season)
        "resultados trimestrais", "resultado trimestral", "balanço trimestral",
        "balanco trimestral", "temporada de resultados", "divulga balanço",
        "divulga balanco", "lucro líquido de", "lucro liquido de",
        "lucro do trimestre",
        # M&A, dividendos e fatos relevantes
        "aquisição", "aquisicao", "adquire fatia", "adquire participação",
        "adquire participacao", "compra fatia", "compra participação",
        "compra participacao", "vende fatia", "vende participação",
        "vende participacao", "fusão", "fusao",
        "oferta pública de aquisição", "oferta publica de aquisicao",
        " opa ", "dividendos", "juros sobre capital próprio", "jcp",
        "fato relevante", "aprova incorporação", "aprova incorporacao",
        "recompra de ações", "recompra de acoes", "buyback",
    ],
    "commodities": [
        "petróleo", "petroleo", "brent", "minério", "minerio", "soja",
        "milho", "commodity", "commodities", "ouro", "café", "cafe",
    ],
    "cripto": [
        "bitcoin", "criptomoeda", "criptomoedas", "cripto", "ethereum",
        "blockchain", "binance", "altcoin", "stablecoin", "token cripto",
        "moeda digital",
    ],
    "internacional": [
        "estados unidos", " eua ", "fed ", "federal reserve", "china",
        "zona do euro", "europa", "reino unido", "japão", "japao", "opep",
        "wall street", "nasdaq", "dow jones", "s&p 500", "bolsas americanas",
        "bolsas europeias", "bolsas asiáticas", "bolsas asiaticas", "ftse",
        "nikkei", "hang seng",
        # geopolítica
        "sanções", "sanção", "sanções dos eua", "tensões geopolíticas",
        "tensao geopolitica", "tensões geopolíticas", "oriente médio",
        "oriente medio", "guerra comercial", "escalada de tensões",
        "escalada de tensoes", "conflito no", "guerra na",
    ],
    "politica_fiscal": [
        "congresso nacional", "câmara dos deputados", "camara dos deputados",
        "senado federal", "reforma tributária", "reforma tributaria",
        "arcabouço fiscal", "arcabouco fiscal", "risco fiscal", "meta fiscal",
        "déficit fiscal", "deficit fiscal", "superávit fiscal", "superavit fiscal",
        "ministério da fazenda", "ministerio da fazenda", "pacote fiscal",
        "planalto", "governo federal", "stf", "supremo tribunal federal",
        "medida provisória", "medida provisoria", "projeto de lei",
        # eleições (2026 é ano eleitoral no Brasil)
        "eleição", "eleicao", "eleições", "eleicoes", "corrida presidencial",
        "corrida eleitoral", "disputa presidencial", "candidato à presidência",
        "candidato a presidencia", "candidata à presidência",
        "candidata a presidencia", "pesquisa eleitoral", "pesquisa datafolha",
        "datafolha", "pesquisa quaest", "quaest", "pesquisa genial",
        "primeiro turno", "segundo turno", "tse", "tribunal superior eleitoral",
        "urnas eletrônicas", "urnas eletronicas", "debate presidencial",
        "campanha eleitoral", "reeleição", "reeleicao",
    ],
    "credito_privado": [
        "crédito privado", "credito privado", "debênture", "debenture",
        "cdb", "fidc", "spread de crédito", "spread de credito",
    ],
    "fundos": [
        "fundo multimercado", "fundos multimercado", "fundo de ações",
        "fundos de ações", "captação líquida", "captacao liquida",
        "resgate de fundos", "anbima", "gestora de recursos", "hedge fund",
        "fundo de investimento", "fundos de investimento",
    ],
    "imoveis": [
        "imóvel", "imovel", "imóveis", "imoveis", "fii", "fiis",
        "fundo imobiliário", "fundo imobiliario", "aluguel",
        "construção civil", "construcao civil",
    ],
}


# Ordem de PRIORIDADE na hora de classificar (não é a ordem de exibição,
# essa continua vindo de config.CATEGORIES). Categorias mais específicas
# vêm primeiro para não perderem notícias para categorias genéricas --
# ex: uma notícia sobre "FII" que também cita "Itaú" deve cair em
# "imoveis", não em "bolsa" só porque "Itaú" aparece antes na lista.
CLASSIFICATION_PRIORITY = [
    "cripto", "credito_privado", "imoveis", "fundos",
    "politica_fiscal", "empresas", "commodities", "cambio_juros",
    "internacional", "bolsa",
]


def _classify_item(item: dict) -> str | None:
    text = f" {item.get('title', '')} {item.get('summary', '')} ".lower()
    for key in CLASSIFICATION_PRIORITY:
        for keyword in CATEGORY_KEYWORDS.get(key, []):
            pattern = r"\b" + re.escape(keyword.strip()) + r"\b"
            if re.search(pattern, text):
                return key
    return None


def _source_rank(item: dict, source_scores: dict) -> int:
    scores = source_scores.get(item.get("source", ""), {})
    return scores.get("like", 0) - scores.get("dislike", 0)


def classify_offline(raw_news: list[dict], feedback: dict | None = None) -> dict:
    limits = {key: qty for key, _t, _i, qty in CATEGORIES}
    result = {key: [] for key in limits}

    source_scores = (feedback or {}).get("source_scores", {})
    # notícias de fontes mais bem avaliadas entram primeiro em cada categoria
    ordered = sorted(raw_news, key=lambda item: _source_rank(item, source_scores), reverse=True)

    for item in ordered:
        category = _classify_item(item)
        if category is None:
            continue
        if len(result[category]) >= limits[category]:
            continue
        result[category].append({
            "title": item["title"],
            "source": item["source"],
            "link": item["link"],
        })

    return result


if __name__ == "__main__":
    import json
    from collect_news import fetch_raw_news

    raw = fetch_raw_news()
    print(json.dumps(classify_offline(raw), indent=2, ensure_ascii=False))
