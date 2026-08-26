/**
 * Web App do Google Apps Script — recebe votos (like/dislike) do dashboard
 * e os grava numa planilha Google. Também expõe uma leitura em JSON,
 * usada pelo script Python para "aprender" as preferências da equipe.
 *
 * COMO CONFIGURAR:
 * 1. Crie uma Planilha Google nova.
 * 2. Renomeie a primeira aba para "feedback" e coloque estes cabeçalhos
 *    na linha 1: timestamp | id | title | source | category | vote
 * 3. Na planilha, vá em Extensões > Apps Script.
 * 4. Apague o conteúdo padrão e cole este arquivo inteiro.
 * 5. Troque SHEET_ID abaixo pelo ID da planilha (está na URL dela,
 *    entre /d/ e /edit).
 * 6. Clique em "Implantar" > "Nova implantação" > tipo "Web App".
 *    - Executar como: você mesmo
 *    - Quem pode acessar: qualquer pessoa (necessário para o dashboard
 *      conseguir enviar o voto sem exigir login)
 * 7. Copie a URL gerada (termina em /exec) e cole em FEEDBACK_WEBAPP_URL
 *    no arquivo .env do projeto Python.
 */

const SHEET_ID = 'COLE_AQUI_O_ID_DA_SUA_PLANILHA';
const SHEET_NAME = 'feedback';

function doGet(e) {
  const params = e.parameter;
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME);

  // Modo leitura: usado pelo script Python para carregar o histórico
  if (params.action === 'read') {
    const data = sheet.getDataRange().getValues();
    const headers = data[0];
    const rows = data.slice(1).map(function (row) {
      const obj = {};
      headers.forEach(function (h, i) { obj[h] = row[i]; });
      return obj;
    });
    return ContentService.createTextOutput(JSON.stringify(rows))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Modo escrita: registra um voto vindo do dashboard
  sheet.appendRow([
    new Date(),
    params.id || '',
    params.title || '',
    params.source || '',
    params.category || '',
    params.vote || ''
  ]);

  return ContentService.createTextOutput(
    JSON.stringify({ status: 'ok' })
  ).setMimeType(ContentService.MimeType.JSON);
}
