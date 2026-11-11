"""
Envia o e-mail com o link do morning call usando SMTP + "senha de app" do
Gmail -- NAO precisa de Google Cloud Console, projeto, nem OAuth.

Configuracao necessaria (uma unica vez):
1. Ative a verificacao em duas etapas na conta theo@integritywm.com.br,
   se ainda nao estiver ativa: myaccount.google.com/security
2. Gere uma "senha de app": myaccount.google.com/apppasswords
   - De um nome, ex: "morning-call", e clique em Gerar
   - Copie a senha de 16 letras (sem espacos) e cole em
     GMAIL_APP_PASSWORD no .env
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import RECIPIENTS, SENDER_EMAIL, GMAIL_APP_PASSWORD, DASHBOARD_PUBLIC_URL
from email_template import montar_email

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # SSL


def send_morning_call_email(dashboard_url: str = None, news: dict = None, market_data: dict = None):
    dashboard_url = dashboard_url or DASHBOARD_PUBLIC_URL
    if not dashboard_url:
        raise ValueError("DASHBOARD_PUBLIC_URL nao configurada (ver .env)")
    if not RECIPIENTS:
        raise ValueError("Nenhum destinatario configurado em RECIPIENTS (ver .env)")
    if not GMAIL_APP_PASSWORD:
        raise ValueError(
            "GMAIL_APP_PASSWORD nao configurada (ver .env) -- "
            "gere uma senha de app em myaccount.google.com/apppasswords"
        )

    # Corpo em HTML (layout Integrity) + versao em texto puro como alternativa
    html, texto = montar_email(dashboard_url, news, market_data)
    message = MIMEMultipart("alternative")
    message.attach(MIMEText(texto, "plain", "utf-8"))
    message.attach(MIMEText(html, "html", "utf-8"))  # o HTML precisa vir por ultimo

    message["Subject"] = "Morning call — Integrity"
    message["From"] = SENDER_EMAIL
    message["To"] = ", ".join(RECIPIENTS)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENTS, message.as_string())

    print(f"E-mail enviado para: {', '.join(RECIPIENTS)}")


if __name__ == "__main__":
    send_morning_call_email()
