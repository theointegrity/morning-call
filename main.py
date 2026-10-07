"""
Orquestra o fluxo completo do morning call:
coleta -> feedback -> classificacao -> geracao do HTML -> publicacao (GitHub
Pages) -> e-mail com o link.

Uso: python main.py

Agendamento (GitHub Actions): o cron do GitHub pode atrasar horas, entao o
workflow dispara varias vezes de madrugada. A primeira execucao que chegar
espera ate SEND_NOT_BEFORE, envia e grava a data em SENT_MARKER_PATH (que
fica commitado no repositorio); as seguintes veem a marca e encerram.

Execucao de teste (MORNING_CALL_TEST=true): nao espera, nao publica no
GitHub Pages e nao le nem grava a marca de envio.
"""
import os
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from collect_news import fetch_raw_news, fetch_market_data
from classify_offline import classify_offline
from summarize_news import summarize_and_classify
from generate_dashboard import generate_html
from send_email import send_morning_call_email
from load_feedback import load_feedback_summary
from config import OUTPUT_HTML_PATH, DASHBOARD_PUBLIC_URL, SUMMARIZATION_MODE

BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")

# Horario minimo (Brasilia) para coletar as noticias e enviar o e-mail.
SEND_NOT_BEFORE = (7, 0)

# Guarda a data (AAAA-MM-DD) do ultimo envio para a lista real. Como o runner
# do GitHub e descartado a cada execucao, o arquivo e commitado no repositorio.
SENT_MARKER_PATH = "state/ultimo_envio.txt"

TEST_RUN = os.getenv("MORNING_CALL_TEST", "").lower() == "true"


def log(msg: str):
    """print com horario de Brasilia, para dar para ver quanto tempo cada etapa levou."""
    print(f"[{datetime.now(BRASILIA_TZ):%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def today_str() -> str:
    return datetime.now(BRASILIA_TZ).date().isoformat()


def git_push():
    """git push com ate 3 tentativas, trazendo antes o que outra execucao tenha publicado."""
    for _ in range(3):
        if subprocess.run(["git", "push", "-q"]).returncode == 0:
            return
        subprocess.run(["git", "pull", "--rebase", "-q"], check=True)
    raise RuntimeError("git push falhou 3 vezes")


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
        log("(nada mudou desde a ultima publicacao)")
        return
    git_push()


def sync_with_remote():
    """
    Traz a versao mais recente do repositorio. Necessario porque uma execucao
    que ficou na fila comeca com o codigo de quando foi disparada, sem a marca
    de envio que outra execucao possa ter gravado nesse meio-tempo.
    """
    result = subprocess.run(["git", "pull", "--ff-only", "-q"], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"[aviso] git pull falhou, usando a copia local: {result.stderr.strip()}")


def already_sent_today() -> bool:
    try:
        with open(SENT_MARKER_PATH, encoding="utf-8") as f:
            return f.read().strip() == today_str()
    except FileNotFoundError:
        return False


def mark_sent_today():
    os.makedirs(os.path.dirname(SENT_MARKER_PATH), exist_ok=True)
    with open(SENT_MARKER_PATH, "w", encoding="utf-8") as f:
        f.write(today_str() + "\n")
    subprocess.run(["git", "add", SENT_MARKER_PATH], check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Registra envio do morning call"], check=True)
    git_push()


def wait_until_send_time():
    now = datetime.now(BRASILIA_TZ)
    send_at = now.replace(hour=SEND_NOT_BEFORE[0], minute=SEND_NOT_BEFORE[1], second=0, microsecond=0)
    if now < send_at:
        log(f"cedo demais; aguardando ate {send_at:%H:%M} para coletar e enviar...")
        time.sleep((send_at - now).total_seconds())


def run(test_run: bool = False):
    log("1/6 -> coletando noticias e dados de mercado...")
    raw_news = fetch_raw_news()
    market_data = fetch_market_data()
    log(f"{len(raw_news)} noticias brutas coletadas")

    log("2/6 -> carregando feedback (likes/dislikes) da equipe...")
    feedback = load_feedback_summary()

    log("3/6 -> classificando noticias...")
    if SUMMARIZATION_MODE == "ai":
        news = summarize_and_classify(raw_news, feedback)
    else:
        news = classify_offline(raw_news, feedback)

    log("4/6 -> gerando dashboard HTML...")
    path, _html = generate_html(news, market_data)
    log(f"gerado em {path}")

    if test_run:
        log("5/6 -> (teste) publicacao no GitHub Pages pulada")
    else:
        log("5/6 -> publicando no GitHub Pages...")
        try:
            publish_to_github_pages()
        except Exception as e:
            log(f"[aviso] publicacao falhou, confira a configuracao do git: {e}")

    log("6/6 -> enviando e-mail com o link...")
    send_morning_call_email(DASHBOARD_PUBLIC_URL)

    if not test_run:
        # Se isto falhar, o e-mail ja saiu mas a marca nao: a proxima execucao
        # agendada do dia enviaria de novo. Deixa o erro estourar para o job
        # ficar vermelho no GitHub e chamar atencao.
        mark_sent_today()
        log(f"envio registrado em {SENT_MARKER_PATH}")

    log("concluido.")


def main():
    if TEST_RUN:
        log("execucao de TESTE: sem espera, sem publicar e sem marca de envio")
        run(test_run=True)
        return

    sync_with_remote()
    if already_sent_today():
        log("o morning call de hoje ja foi enviado por outra execucao; nada a fazer.")
        return

    wait_until_send_time()
    run()


if __name__ == "__main__":
    main()
