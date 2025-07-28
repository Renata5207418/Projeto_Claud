# Cloud_1 RPA Project

Automação de download e triagem de anexos de Ordens de Serviço (OS) no portal Onvio, com monitoramento de status via API, fila de processamento e classificação de documentos.  

---

## 🚀 Visão Geral

Este projeto automatiza todo o fluxo de:

1. **Login** no portal Onvio (via Selenium/Chrome)  
2. **Descoberta** de novas OS — semeia IDs pendentes no banco  
3. **Download** de anexos de cada OS  
4. **Organização** de arquivos em pastas de “baixados” e “separados”  
5. **Registro** de status (pendente, sucesso, falha) em SQLite  
6. **Publicação** de IDs processados em fila (queue.db) para etapas subsequentes  
7. **Exposição** de API de status (`/overview` e `/os/{os_id}`) via FastAPI  
8. **Heartbeat** para monitoramento externo (arquivo `heartbeat.json`)  
9. **Logs** centralizados em `logs/bot_onvio.log`

---

## 📋 Estrutura de Pastas

```

Cloud\_1/
├── .chrome\_profile/                   # Perfil Chrome para sessão persistente
├── .venv/                             # Ambiente virtual Python
├── api/
│   └── status\_server.py              # FastAPI de status
├── config/
│   └── settings.py                   # Configurações Pydantic + .env
├── db/
│   ├── db.py                         # Tabela os\_downloads e operações
│   └── message\_queue.py              # Fila simple SQLite queue.db
├── keys/
│   └── firestore-bot.json            # Credenciais Firestore (GCP)
├── logs/
│   └── bot\_onvio.log                 # Log principal de execução
├── scripts/
│   ├── download.py                   # Loop de download de anexos
│   └── login.py                      # Fluxo de autenticação no portal
├── utils/
│   ├── helpers.py                    # Espera de download e mover arquivos
│   └── logging\_config.py             # Configuração de logger
├── .env                              # Variáveis de ambiente (não versionado)
├── .gitignore                        # Ignorando .env e keys/\*.json
├── heartbeat.json                    # Timestamp e status para monitor externo
├── os\_status.db                      # SQLite de OS/status
├── queue.db                          # SQLite da fila de IDs
└── README.md                         # Este documento

````

---

## ⚙️ Pré-requisitos

- Python 3.9+  
- Google Chrome instalado  
- ChromeDriver compatível com sua versão do Chrome e disponível no `PATH`  
- Acesso de rede ao portal Onvio  
- Conta Onvio com permissão para download de anexos  
- GCP Service Account com acesso ao Firestore (opcional, se usar notificações Cloud)  

---

## 🔧 Instalação e Configuração

1. **Clone o repositório**  
   ```bash
   git clone https://seu-repositorio.git Cloud_1
   cd Cloud_1
````

2. **Crie e ative o virtualenv**

   ```bash
   python -m venv .venv
   source .venv/bin/activate       # Linux/macOS
   .venv\Scripts\activate          # Windows
   ```

3. **Instale dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o `.env`** (na raiz do projeto)

   ```ini
   # GCP
   GCP_PROJECT=<seu-projeto-gcp>
   GOOGLE_APPLICATION_CREDENTIALS=keys/firestore-bot.json

   # Portal Onvio
   ONVIO_USER=<seu-usuario>
   ONVIO_PASS=<sua-senha>

   # Diretórios de trabalho
   DOWNLOAD_DIR=/caminho/para/downloads
   BAIXADOS_DIR=/caminho/para/baixados
   SEPARADOS_DIR=/caminho/para/separados
   ```

5. **Verifique o ChromeDriver**

   * Baixe da [https://sites.google.com/a/chromium.org/chromedriver/](https://sites.google.com/a/chromium.org/chromedriver/)
   * Adicione ao `PATH`, ou coloque-o na mesma pasta do script.

---

## 🏃 Como Executar

### 1. API de Status

Inicie o servidor FastAPI para consultas de status:

```bash
uvicorn api.status_server:app --host 0.0.0.0 --port 8000
```

* **GET** `/overview` → `{"pendentes": X, "sucesso": Y, "falha": Z}`
* **GET** `/os/{os_id}` → Detalhes da OS ou `{"erro":"não encontrada"}`

### 2. Bot de Download

Execute o script principal:

```bash
python scripts/download.py
```

Ele:

* Faz login (ou reutiliza sessão)
* Semeia novos IDs
* Baixa anexos de OS pendentes/falhas
* Atualiza `os_status.db` e `queue.db`
* Gera/atualiza `heartbeat.json`
* Registra logs em `logs/bot_onvio.log`

---

## 📊 Logs e Monitoramento

* **Logs**: `logs/bot_onvio.log` (INFO+). Considere adicionar rotação de logs em produção.
* **Heartbeat**: `heartbeat.json` contém:

  ```json
  { "ts": "2025-07-17T15:23:00Z", "msg": "ok" }
  ```

  Use para checar saúde do serviço por ferramentas de monitoramento.

---

## 🔄 Fila de Processamento

A tabela `queue.db` mantém uma fila simples de `os_id` processados com:

* **publish(os\_id)** → adiciona
* **pull()** → retorna e remove o próximo `os_id` (FIFO)

Isso permite desacoplar etapas posteriores (e.g. triagem de conteúdo).

---

## 📝 .gitignore

```gitignore
# Credenciais
.env
keys/*.json

# Ambientes e caches
.venv/
__pycache__/

# Logs e bancos locais
logs/
*.db
```

---

## 📖 Contribuição

1. Fork este repositório
2. Crie uma *feature branch* (`git checkout -b feature/xyz`)
3. Commit suas mudanças (`git commit -m "Add xyz"`)
4. Push para sua branch (`git push origin feature/xyz`)
5. Abra um Pull Request

---

## 🛡️ Segurança

* **Nunca** exponha `ONVIO_PASS` ou chaves GCP em logs públicos
* Armazene credenciais sensíveis apenas em variáveis de ambiente
* Revise permissões de pastas (`.chrome_profile`, `logs/`, diretórios de download)

---

## 🤝 Licença

MIT © Renata Boppré Scharf
