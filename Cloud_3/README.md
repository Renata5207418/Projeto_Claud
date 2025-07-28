# Cloud_3 – Processamento de “Tomados”

Automatiza a etapa de pós-triagem (“Cloud_3”) a partir das notificações de “TOMADOS” geradas pelo Cloud_2.  
Recebe mensagens no Pub/Sub, extrai campos de PDFs via Document AI, gera linhas de CSV e arquivos de tomadores, e faz upload dos resultados para o GCS.

---

## 📂 Estrutura do Projeto

```

Cloud\_3/
├── config/
│   └── settings.py            # Carrega variáveis do .env e validações básicas
├── db/
│   └── triage\_consulta.py     # Leitura/atualização de tomados\_status no SQLite
├── utils/
│   ├── acumuladores.py        # Dicionário código→valor de acumuladores
│   ├── consulta\_for.py        # Consulta CNPJ na API ReceitaWS
│   ├── document\_ai.py         # Wrapper genérico para Document AI
│   ├── tratamentos.py         # Limpeza de strings (CNPJ, datas, valores...)
│   ├── tratamentos\_csv.py     # Pipeline de CSV e split de tomadores
│   └── gcs\_upload.py          # Função para upload em GCS (não mostrado aqui)
│ 
├── cloud3_subscriber.py       # Subscriber Pub/Sub que dispara o processamento
├── processa_tomados.py        # Lógica principal para extrair, gerar e enviar resultados
├── logs/                      # Arquivos de log gerados em runtime
├── heartbeat.json             # Atualizado por worker/subscriber para monitoramento
├── triage\_status.db           # SQLite de status de triagem (tomados\_status)
├── .env                       # Variáveis de ambiente (credentials, paths, IDs)
├── .gitignore
└── README.md                  # Esta documentação

````

---

## ⚙️ Pré-requisitos

- **Python 3.9+**  
- Conta de serviço GCP com permissões para:
  - Document AI  
  - Pub/Sub (assinatura)  
  - Cloud Storage (upload de arquivos)  
- **SQLite** (já utilizado via `sqlite3` no script)  
- Acesso público ou credenciado à API ReceitaWS (receitaws.com.br)  

---

## 🔧 Configuração

1. **Crie um arquivo `.env` na raiz** com as variáveis abaixo:

   ```ini
   # SQLite de status de triagem
   TRIAGE_DB_PATH=/caminho/para/triage_status.db

   # Pasta de entrada (pastas “ID-APELIDO” com subpasta TOMADOS/)
   SEPARADOS_DIR=/caminho/para/separados

   # Google Cloud Project e Document AI
   GCLOUD_PROJECT_ID=meu-project-id
   GCLOUD_LOCATION=us
   GCLOUD_PROCESSOR_ID=meu-processor-id
   GCLOUD_PROCESSOR_VERSION_ID=meu-processor-version

   # Credenciais ADC
   GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/service-account.json

   # MIME type esperado (geralmente application/pdf)
   GCLOUD_MIME_TYPE=application/pdf

   # GCS para resultados “tomados”
   GCS_BUCKET_TOMADOS=meu-bucket
   GCS_PREFIX_RESULTADOS=tomados_saida

   # Páginas a extrair (ex.: "1,2,3")
   PAGE_SELECTOR=1

   # Segundos de espera entre chamadas Document AI (evita quotas)
   TEMPO_ESPERA=16

   # Pub/Sub
   PROJECT_ID=meu-project-id       # opcional, usa GCLOUD_PROJECT_ID por padrão
   SUBSCRIPTION_ID=cloud3-tomados-sub
````

2. **Não versionar** o `.env` nem o JSON de credenciais (já incluídos em `.gitignore`).

---

## 🚀 Instalação

```bash
git clone https://seu-repo/Cloud_3.git
cd Cloud_3
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate          # Windows
pip install -r requirements.txt # inclua google-cloud-documentai, google-cloud-pubsub, pandas, requests...
```

---

## ▶️ Uso

### 1. Subscriber Pub/Sub

Fica escutando mensagens e dispara o processamento:

```bash
python -m scripts.cloud3_subscriber
```

* Conecta à assinatura `PROJECT_ID/SUBSCRIPTION_ID`.
* Callback puxa `os_id` e `pasta`, verifica status, chama `processar_os_pubsub()`.

### 2. Processamento Batch (loop principal)

Pode-se rodar em modo polling (sem Pub/Sub):

```bash
python -m scripts.processa_tomados
```

* Varre `triage_status.db` por `tomados_status = 'Pendente'`.
* Para cada OS:

  1. Lê todos os PDFs em `SEPARADOS_DIR/<ID-APELIDO>/TOMADOS/`
  2. Processa cada PDF com Document AI
  3. Aplica padrões (CNPJ, datas, códigos de serviço, CSRF, acumuladores…)
  4. Gera CSV e arquivos de tomadores via `tratamentos_csv.exe()`
  5. Renomeia PDFs originais e atualiza `GERAL.txt`
  6. Envia `GERAL.txt` e arquivos de tomadores para GCS
  7. Atualiza `tomados_status = 'Concluído'` em triage\_status.db

---

## 🛠️ Monitoramento e Logs

* **Logs**: em `logs/`, um arquivo `tomados.log` (configurado pelo `logging.basicConfig`).
* **Heartbeat**: `heartbeat.json` no diretório de scripts, com a última mensagem e timestamp:

  ```json
  { "ts": "2025-07-17T15:23:00Z", "msg": "empresa 12345-CLIENTE" }
  ```

  Use em health checks ou dashboards.

---

## 🔄 Contribuição

1. Fork do repositório
2. Nova branch (`git checkout -b feature/xyz`)
3. Commits atômicos e claros
4. Pull Request para revisão

---

## 🤝 Licença

MIT © Renata Boppré Scharf

```
```
