# Triagem Cloud

Solução integrada para gestão de downloads, triagem e automações, utilizando React no frontend e FastAPI no backend.

---

## 🗂 Estrutura do Projeto

```

Cloud_front/
├── .venv/                               
├── keys/
│   └── credenciais_Cloud.json
├── node_modules/
├── rpa-front/
│   ├── node_modules/
│   ├── public/
│   └── src/
│       ├── auth/
│       │   ├── AuthContext.tsx         
│       │   └── PrivateRoute.tsx        
│       ├── components/
│       │   └── Sidebar.tsx
│       ├── hooks/
│       │   └── useFetch.ts
│       ├── pages/
│       │   ├── DashboardPage.tsx
│       │   ├── DownloadsPage.tsx
│       │   ├── LoginPage.tsx
│       │   ├── MensagensPage.tsx
│       │   ├── ResetPage.tsx
│       │   └── TriagemPage.tsx
│       ├── services/
│       │   └── api.ts                  
│       ├── static/
│       │   └── img/  
│       │   ├── logosc.png
│       ├──App.css
│       ├── App.test.tsx
│       ├──App.tsx
│       ├──index.css
│       ├──index.tsx
│       ├── logo.svg
│       ├──react-app-env.d.ts
│       ├──reportWebVitals.ts
│      └──setupTests.ts
│   ├── .gitignore        
│   ├──  package.json                         
│   ├──  package-lock.json           
│   ├── tsconfig.json                    
├── scripts/
│   └── init_auth_db.py                  
├── .env                                 
├── api.py                               
├── auth.db                              
├── auth_utils.py                        
├── auth_routes.py 
├── package.json                         
├── package-lock.json                   
└── test_gcs.py                          
                   

````

---

## 🚀 Como rodar em desenvolvimento

### **Backend (FastAPI)**

1. **Instale dependências Python** (recomendo usar um ambiente virtual):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
   pip install -r requirements.txt
````

2. **Configure o `.env`** (exemplo):

   ```
   RESEND_API_KEY=your-key
   # outros secrets...
   ```

3. **Inicie a API:**

   ```bash
   uvicorn api:app --reload
   ```

   > API rodando em `http://localhost:8000`

---

### **Frontend (React)**

1. **Acesse a pasta do frontend:**

   ```bash
   cd rpa-front
   ```

2. **Instale as dependências:**

   ```bash
   npm install
   ```

3. **Rode em modo desenvolvimento:**

   ```bash
   npm start
   ```

   > App acessível em `http://localhost:3000`

---

## 🏗️ Build e Deploy para Produção

### **1. Gerar o build do frontend**

No diretório `rpa-front`:

```bash
npm run build
```

Isso cria a pasta `/build` com todos os arquivos otimizados para produção.

---

### **2. Servir o build**

Você pode servir a pasta `build` de várias formas:

#### **A. Usando um servidor web dedicado**

* **Nginx**: Configure o root para `build`.
* **Apache**: Use `DocumentRoot`.
* **Vercel/Netlify**: Faça o deploy apontando para `/build`.

#### **B. Usando Node.js (serve)**

```bash
npm install -g serve
serve -s build
```

#### **C. Servindo pelo próprio FastAPI**

No `api.py`, adicione:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="rpa-front/build", html=True), name="static")
```

Agora o frontend será servido pela mesma porta da API!

---

### **3. Ajustes de produção**

* **API URL:**
  Certifique-se de que o frontend aponta para o backend correto (ajuste `baseURL` do axios se necessário).
* **CORS:**
  O backend já está configurado para aceitar o frontend em localhost. Para produção, ajuste os domínios permitidos no CORS.
* **Ambiente:**
  Configure `.env` para produção no backend (e também no frontend, se usar variáveis públicas).

---

## 🔐 Autenticação

* Usa JWT HttpOnly tokens (acesso + refresh).
* Refresh automático com axios interceptors.
* Cookies seguros (`HttpOnly`, `SameSite=Lax`).

---

## 📁 Estrutura de Pastas (Frontend)

* `src/auth` — Contexto de autenticação, rotas privadas.
* `src/pages` — Cada tela principal.
* `src/hooks/useFetch.ts` — Hook de fetch autenticado.
* `src/services/api.ts` — Configuração do axios.

---

## 💡 Dicas

* O backend FastAPI pode ser servido junto com o build React para facilitar o deploy em VPS ou serviços cloud.
* Para novos endpoints, siga o padrão REST usado em `api.py`.
* Configure o Resend API Key para recuperação de senha.

---

## 🛠️ Scripts Úteis

* **Iniciar banco:**
  `python scripts/init_auth_db.py`
* **Build produção:**
  `npm run build` (no rpa-front)
* **Testes React:**
  `npm run test`

---

## 📧 Contato

Dúvidas ou sugestões: **renata.boppre@gmail.com**

---

```
