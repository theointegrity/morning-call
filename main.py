"""
Orquestra o fluxo completo do morning call:
coleta -> feedback -> classificacao -> geracao do HTML -> publicacao (GitHub
Pages) -> e-mail com o link.

Uso: python main.py
Agendamento sugerido: cron/GitHub Actions rodando de segunda a sexta, ~06:00.
"""
import subprocess

from collect_news import fetch_raw_news, fetch_market_data
from classify_offline import classify_offline
from summarize_news import summarize_and_classify
from generate_dashboard import generate_html
from send_email import send_morning_call_email
from load_feedback import load_feedback_summary
from config import OUTPUT_HTML_PATH, DASHBOARD_PUBLIC_URL, SUMMARIZATION_MODE


def publish_to_github_pages():
    """
    Publica o docs/index.html gerado no GitHub Pages via git push.
    Pressupoe que este projeto ja e um repositorio git com um remote
    'origin' configurado (ver README, secao GitHub Pages).
    """
    subprocess.run(["git", "add", OUTPUT_HTML_PATH], check=True)
    result = subprocess.run(
        ["git", "commit", "-m", "Atualiza morning call"],
        capture_output=True, text=True,
    )
    if "nothing to commit" in result.stdout:
        print("    (nada mudou desde a ultima publicacao)")
        return
    subprocess.run(["git", "push"], check=True)


def run():
    print("1/6 -> coletando noticias e dados de mercado...")
    raw_news = fetch_raw_news()
    market_data = fetch_market_data()
    print(f"    {len(raw_news)} noticias brutas coletadas")

    print("2/6 -> carregando feedback (likes/dislikes) da equipe...")
    feedback = load_feedback_summary()

    print("3/6 -> classificando noticias...")
    if SUMMARIZATION_MODE == "ai":
        news = summarize_and_classify(raw_news, feedback)
    else:
        news = classify_offline(raw_news, feedback)

    print("4/6 -> gerando dashboard HTML...")
    path, _html = generate_html(news, market_data)
    print(f"    gerado em {path}")

    print("5/6 -> publicando no GitHub Pages...")
    try:
        publish_to_github_pages()
    except Exception as e:
        print(f"[aviso] publicacao falhou, confira a configuracao do git: {e}")

    print("6/6 -> enviando e-mail com o link...")
    send_morning_call_email(DASHBOARD_PUBLIC_URL)

    print("concluido.")


if __name__ == "__main__":
    run()
