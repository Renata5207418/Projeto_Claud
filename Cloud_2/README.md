# Cloud_2 Triagem Automática

Automatiza a triagem de documentos baixados (ordens de serviço) e seu envio para a estrutura de clientes, com:

- Extração recursiva de ZIP/RAR (tratando entradas corrompidas)  
- Classificação de PDFs via Document AI (Google)  
- Organização de arquivos por tipo e confiança  
- Registro de status em SQLite (`triage_status.db`)  
- Fila de jobs em SQLite (`queue.db`) para processamento assíncrono  
- Notificação de “TOMADOS” via Pub/Sub (Cloud 3)  
- Worker dedicado para processar cada OS individualmente  

---

## 📂 Estrutura de Pastas

```

Cloud\_2/
├── config/
│   └── settings.py           # Leitura de .env e validação de paths / credenciais
├── db/
│   ├── banco\_dominio.py      # Consulta ao banco legado para obter códigos de empresa
│   ├── queue\_cliente.py      # Fila SQLite de OS pendentes de triagem
│   └── triagem\_db.py         # Tabela os\_triagem e funções CRUD
├── scripts/
│   ├── triagem.py            # Pipeline completo de extração e classificação
│   └── triagem\_worker.py     # Worker que consome queue\_cliente e executa triagem.py
├── utils/
│   ├── extensoes.py          # Agrupamento de arquivos por extensão (`organiza_extensao`)
│   ├── extract.py            # Extração manual de ZIP/RAR (prefixos randômicos)
│   ├── logging\_config.py     # Configuração de loggers para módulos
│   └── pubsub\_notify.py      # Publicação de mensagens em Pub/Sub
├── logs/                     # Arquivos de log gerados em tempo de execução
├── queue.db                  # SQLite da fila de triagem (QUEUE\_DB\_PATH)
├── triage\_status.db          # SQLite de status de triagem (triage\_db\_path)
├── .env                      # Variáveis de ambiente (não versionado)
├── .gitignore                # Ignora credenciais e arquivos temporários
└── README.md                 # Documentação deste projeto

````

---

## ⚙️ Pré-requisitos

- **Python 3.9+**  
- **Google Cloud SDK** configurado (ADC ou `GOOGLE_APPLICATION_CREDENTIALS`)  
- **Credenciais** do Firestore/Document AI e Pub/Sub (Service Account JSON)  
- **Acesso** ao banco SQL Anywhere (via `sqlanydb`)  
- **Permissões** de leitura/gravação nas pastas definidas em `.env`  

---

## 🔧 Instalação

1. **Clone o repositório**  
   ```bash
   git clone https://seu-repositorio.git Cloud_2
   cd Cloud_2
````

2. **Crie e ative seu virtualenv**

   ```bash
   python -m venv .venv
   source .venv/bin/activate    # Linux/macOS
   .venv\Scripts\activate       # Windows
   ```

3. **Instale dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure seu `.env`** na raiz do projeto:

   ```ini
   # Caminhos de banco
   QUEUE_DB_PATH=C:\caminho\para\queue.db
   # Triagem
   SEPARADOS_DIR=C:\caminho\para\separados
   CLIENTES_DIR=C:\caminho\para\clientes
   TESTES_DIR=C:\caminho\para\testes
   # Pub/Sub
   PUBSUB_TOPIC_CLOUD3=tomados-processar
   PUBSUB_PROJECT_ID=seu-project-id
   GCS_BUCKET_TOMADOS=seu-bucket
   GCS_PREFIX_TOMADOS=prefixo/tomados
   # Firestore / Document AI
   GOOGLE_APPLICATION_CREDENTIALS=keys/firestore-bot.json
   # Banco legado
   DB_HOST=...
   DB_PORT=...
   DB_NAME=...
   DB_USER=...
   DB_PASSWORD=...

   # (Opcional) `triage_status.db` será criado automaticamente
   ```

   > **Importante:** o `.env` está no `.gitignore` para não vazar credenciais.

---

## ▶️ Uso

### 1. Pipeline de Triagem (síncrono)

Para testar ou rodar uma pasta específica **manualmente**:

```bash
cd Cloud_2
python -m scripts.triagem
```

Isso irá:

1. Extrair ZIPs/RARs recursivamente
2. Classificar PDFs página a página
3. Organizar arquivos em subpastas por tipo/confi­ança
4. Mover a pasta final para a estrutura de clientes
5. Registrar status em `triage_status.db`
6. Enviar notificações Pub/Sub para “TOMADOS”

### 2. Worker Assíncrono

Para processamento contínuo em background:

```bash
cd Cloud_2
python -m scripts.triagem_worker
```

O worker:

1. Enfileira (seed) todas as OS baixadas (`SEPARADOS_DIR`) ainda não triadas
2. Puxa um `os_id` da fila (`queue.db`)
3. Executa `triagem.exe()` e `mover_cliente()`
4. Atualiza status (`set_triagem_status`, `register_separacao`)
5. Retries automáticos até `max_attempts`
6. Mantém um `heartbeat.json` atualizado para monitoramento

---

## 📑 Logs e Monitoramento

* **Logs**: cada módulo grava em `logs/<nome>.log` (nível INFO+).
* **Heartbeat**: `heartbeat.json` contém:

  ```json
  { "ts": "2025-07-17T15:23:00Z", "msg": "Processando 12345-CLIENTE" }
  ```

  Use para check de saúde em sistemas de supervisão.

---

## 📄 .gitignore

```gitignore
# Credenciais e ambientes
.env
keys/*.json
.venv/
__pycache__/

# Logs e bancos
logs/
*.db
```

---

## 🤝 Contribuição

1. Fork este repositório
2. Crie uma branch (`git checkout -b feature/xyz`)
3. Commit suas mudanças (`git commit -m "Descrição do change"`)
4. Push para sua branch (`git push origin feature/xyz`)
5. Abra um Pull Request

---

## 🛡️ Segurança e Boas Práticas

* Nunca exponha credenciais em logs ou no repositório.
* Limite permissões da Service Account ao mínimo necessário.
* Considere usar **RotatingFileHandler** para controle de tamanho de log.
* Em cenários de alta concorrência, avalie usar fila gerenciada (Pub/Sub) em vez de SQLite.

---

## 📜 Licença

MIT © Renata Boppré Scharf
