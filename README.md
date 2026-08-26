# Morning call — Integrity

Pipeline automatizado: coleta notícias de mercado, resume/classifica com IA,
gera um dashboard estático em HTML, publica no GitHub Pages e envia o link
por e-mail para a equipe via Gmail.

## Estrutura

```
morning-call/
├── config.py              # configurações centrais (lê do .env)
├── collect_news.py         # coleta RSS + dados de mercado (câmbio, Ibovespa, Selic, petróleo)
├── summarize_news.py       # filtra, resume e classifica notícias via API da Anthropic
├── generate_dashboard.py   # gera o HTML final a partir do template
├── send_email.py           # envia e-mail via Gmail API (OAuth2)
├── main.py                 # orquestra o fluxo completo
├── templates/
│   └── dashboard_template.html
├── requirements.txt
└── .env.example
```

## Sobre o custo (API paga vs. modo gratuito)

Por padrão, o projeto roda **sem custo de API nenhum**: em vez de pedir para
o Claude resumir e classificar as notícias, o script (`classify_offline.py`)
faz isso sozinho usando palavras-chave (ex: notícia com "Selic" ou "Copom"
vai para a categoria de câmbio e juros). Isso é controlado pela variável
`SUMMARIZATION_MODE` no `.env`:

- `SUMMARIZATION_MODE=offline` (padrão): classificação por palavras-chave,
  sem chamar nenhuma API paga. O título exibido é o título original da
  notícia (sem reescrita).
- `SUMMARIZATION_MODE=ai`: usa a API da Anthropic para escrever um resumo
  mais curto e classificar com mais precisão -- tem um custo bem pequeno por
  execução (poucos centavos de dólar/dia), e exige `ANTHROPIC_API_KEY`
  preenchida no `.env`.

Se quiser começar 100% de graça e migrar para o modo com IA depois, basta
trocar essa variável -- o resto do fluxo (coleta, geração do HTML, envio de
e-mail, feedback) funciona igual nos dois modos.

**Limitação do modo offline**: como não há um modelo de linguagem
analisando o conteúdo, a classificação pode errar em notícias ambíguas ou
que usem termos fora da lista de palavras-chave em `classify_offline.py`
(fica fácil de editar essa lista se perceber que alguma notícia relevante
está sendo deixada de fora).

## Configuração inicial (uma única vez)

### 1. Instalar dependências

```bash
python -m venv venv
source venv/bin/activate   # no Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Preencha no `.env`:
- `ANTHROPIC_API_KEY`: sua chave da API da Anthropic (console.anthropic.com)
- `RECIPIENTS`: e-mails da equipe, separados por vírgula
- `DASHBOARD_PUBLIC_URL`: preenchido depois que o GitHub Pages estiver configurado (passo 4)

### 3. Configurar o envio de e-mail (Gmail via senha de app)

Não precisa de Google Cloud Console nem OAuth -- só uma senha de app:

1. Acesse [myaccount.google.com/security](https://myaccount.google.com/security)
   com a conta `theo@integritywm.com.br`
2. Se a **verificação em duas etapas** ainda não estiver ativa, ative-a
   (é obrigatório para gerar senha de app)
3. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Dê um nome (ex: "morning-call") e clique em **Gerar**
5. Copie a senha de 16 letras que aparece (sem espaços) e cole em
   `GMAIL_APP_PASSWORD` no `.env`

**Importante**: essa senha de app é diferente da sua senha normal do Gmail
-- ela só serve pra esse tipo de automação e pode ser revogada a qualquer
momento na mesma página, sem afetar seu login normal.

### 4. Criar o repositório no GitHub e configurar o Pages

**a) Criar a conta e o repositório (se ainda não tiver)**
1. Crie uma conta em [github.com](https://github.com) (se ainda não tiver)
2. Clique em **New repository** (ou "+" no canto superior direito > "New repository")
3. Nome: `morning-call` (ou o que preferir) -- deixe como **Public**
   (o GitHub Pages gratuito exige repositório público)
4. Não marque nenhuma opção de inicializar com README -- deixe em branco
5. Clique em **Create repository**

**b) Criar um token de acesso (para o script conseguir publicar sozinho)**
1. No GitHub, vá em **Settings** (do seu perfil, não do repositório) >
   **Developer settings** > **Personal access tokens** > **Fine-grained tokens**
2. Clique em **Generate new token**
3. Em "Repository access", escolha **Only select repositories** e selecione
   o `morning-call` que você criou
4. Em "Permissions" > "Repository permissions", encontre **Contents** e
   mude para **Read and write**
5. Clique em **Generate token**
6. **Copie o token gerado agora** (começa com `github_pat_...`) -- ele só
   aparece uma vez, se perder precisa gerar outro

**c) Conectar sua pasta local ao repositório**

No terminal, dentro da pasta `morning-call`, rode (trocando `SEU-USUARIO`,
`SEU-TOKEN` e o nome do repo se for diferente):

```bash
git init
git branch -M main
git add .
git commit -m "Primeira versão do morning call"
git remote add origin https://SEU-TOKEN@github.com/SEU-USUARIO/morning-call.git
git push -u origin main
```

**Importante**: o token fica salvo só na configuração local do git dessa
pasta (no arquivo `.git/config`), nunca é commitado nem exposto -- mas
mesmo assim, não compartilhe esse comando com o token real em nenhum lugar
público.

**d) Ativar o GitHub Pages**
1. No repositório, vá em **Settings** > **Pages** (menu lateral esquerdo)
2. Em "Build and deployment" > "Source", escolha **Deploy from a branch**
3. Em "Branch", escolha `main` e a pasta **/docs**
4. Clique em **Save**
5. Espere 1-2 minutos e a URL pública vai aparecer no topo dessa mesma
   página (algo como `https://SEU-USUARIO.github.io/morning-call/`)
6. Copie essa URL e cole em `DASHBOARD_PUBLIC_URL` no `.env`

Depois disso, toda vez que `python main.py` rodar, ele vai gerar o
`docs/index.html`, commitar e dar push automaticamente -- o GitHub Pages
atualiza a página pública sozinho em menos de um minuto.

## Rodando manualmente

```bash
python main.py
```

## Agendando a execução automática

**Opção simples — cron (Linux/Mac, se rodar num servidor próprio):**
```bash
crontab -e
# roda de segunda a sexta às 6h
0 6 * * 1-5 cd /caminho/para/morning-call && venv/bin/python main.py
```

**Opção recomendada — GitHub Actions** (não depende de nenhuma máquina ligada):
crie `.github/workflows/morning-call.yml` com um `schedule` cron e os
secrets (`ANTHROPIC_API_KEY`, `RECIPIENTS`, credenciais do Gmail) configurados
em Settings → Secrets do repositório. Posso montar esse workflow também —
é só pedir.

## Configurando o like/dislike (feedback)

O dashboard tem botões de 👍/👎 em cada notícia. O voto é enviado para uma
planilha Google via Google Apps Script, e nas próximas execuções o script
lê esse histórico e ajusta o prompt da IA para priorizar o que a equipe
gostou e evitar o que não gostou. **Importante**: isso é uma heurística
baseada em histórico, não um modelo treinado -- funciona bem para curadoria,
mas não é "aprendizado de máquina" no sentido literal.

1. Crie uma Planilha Google nova
2. Renomeie a primeira aba para `feedback` e coloque na linha 1 os
   cabeçalhos: `timestamp | id | title | source | category | vote`
3. Na planilha, vá em **Extensões > Apps Script**, apague o conteúdo padrão
   e cole o conteúdo de `apps_script/feedback_webapp.gs`
4. Troque `SHEET_ID` no código pelo ID da planilha (está na URL, entre
   `/d/` e `/edit`)
5. Clique em **Implantar > Nova implantação > Web App**
   - Executar como: você mesmo
   - Quem pode acessar: qualquer pessoa
6. Copie a URL gerada (termina em `/exec`) e cole em `FEEDBACK_WEBAPP_URL`
   no `.env`
7. Rode `python main.py` normalmente -- o feedback já entra automaticamente
   no fluxo (carregado antes do resumo, salvo a cada clique no dashboard)

## Ajustando fontes e categorias

- Fontes de notícia (RSS): edite `RSS_FEEDS` em `config.py`
- Categorias e quantidade de itens por categoria: edite `CATEGORIES` em `config.py`
- Indicadores de mercado: edite `MARKET_TICKERS` em `config.py`
