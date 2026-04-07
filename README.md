# 🤖 Assistente de Atendimento Inteligente com Automação (GameVault)

Este projeto implementa um **Agente de IA completo para atendimento ao cliente**, utilizando LLMs, engenharia de prompt estruturada, ferramentas (Tools) e integração com automações simuladas.

Desenvolvido como parte de um desafio técnico para a vaga de **Analista de IA Júnior**.

---

## 🎯 Objetivo

Construir um assistente capaz de:

* Responder dúvidas com base em uma **base de conhecimento controlada**
* Evitar **alucinações**
* Consultar dados dinâmicos (estoque de jogos)
* Detectar situações críticas
* Acionar uma **automação (Webhook simulado)**

---

## 🧠 Stack Tecnológica

* **LLM:** Google Gemini 2.5 Flash *(ver observação abaixo)*
* **Framework:** LangChain (Agent + Tools)
* **Backend:** Python 3.11
* **Interface:** Streamlit
* **Banco de Dados:** PostgreSQL
* **Containerização:** Docker + Docker Compose

---

## ⚠️ Observação sobre o Modelo de IA

O desafio solicitava:

* OpenAI (GPT-4o / mini) **ou**
* Google Gemini 1.5 Flash

Devido à indisponibilidade de créditos na OpenAI e limitação de acesso ao modelo 1.5, foi utilizado:

👉 **Gemini 2.5 Flash**

A escolha mantém total compatibilidade técnica com o desafio, utilizando a mesma arquitetura de LLM + Tools + Prompt Engineering.

---

## 🏗️ Arquitetura do Agente

O sistema foi estruturado em quatro pilares principais:

### 1. Base de Conhecimento Híbrida

* 📌 **Estática:** políticas da loja (horário, entrega, troca)
* 📌 **Dinâmica:** dados do PostgreSQL (estoque de jogos)
* 📌 **RAG Local:** leitura de arquivos `.txt` e `.md` na pasta `/data`

---

### 2. Ferramentas (Tools)

#### 🔍 `consultar_estoque_jogos`

* Consulta o banco de dados em tempo real
* Usa LLM para formatar respostas com base nos dados
* Proíbe alucinação de jogos/preços

#### 🚨 `disparar_automacao_escalonamento`

* Simula envio de webhook:

```bash
>> [WEBHOOK → n8n] ESCALONAMENTO ATIVADO: [motivo]
```

* Retorna resposta padrão ao usuário

---

### 3. Engenharia de Prompt (Ponto Central)

O agente é controlado por um **System Prompt altamente restritivo**, com:

#### 🎭 Persona

"Maya", atendente virtual da GameVault
Tom amigável, objetivo e profissional

#### 🛑 Regras Críticas

* **Nunca inventar informações**
* **Responder apenas com base na base de conhecimento**
* **Encaminhar para humano quando necessário**

#### ⚡ Gatilhos de Automação

A tool de escalonamento é acionada automaticamente quando:

* Usuário pede um humano
* Linguagem agressiva
* Problemas graves (fraude, erro, cobrança)

#### 🔄 Uso de Tools

* Perguntas sobre jogos → `consultar_estoque_jogos`
* Situações críticas → `disparar_automacao_escalonamento`

---

### 4. Orquestração com LangChain

* Uso de `create_tool_calling_agent`
* Controle de contexto via `chat_history`
* Execução com `AgentExecutor`
* Tratamento de erros e limite de iterações

---

## 🗄️ Banco de Dados

Tabela `jogos` com:

* Nome
* Gênero
* Preço
* Estoque

Populado automaticamente via `init.sql`.

---

## 🐳 Como Executar

### 1. Clone o projeto

```bash
git clone <repo>
cd <repo>
```

### 2. Configure o `.env`

```bash
GOOGLE_API_KEY=sua_chave
DATABASE_URL=postgresql://postgres:postgres123@db:5432/gamevault
```

### 3. Suba o ambiente

```bash
docker-compose up --build
```

---

## 🌐 Acesso

Abra no navegador:

👉 http://localhost:8501

---

## 💡 Diferenciais do Projeto

* ✔ Engenharia de prompt robusta (anti-alucinação)
* ✔ Uso de Tools com tomada de decisão do agente
* ✔ Integração com banco de dados real
* ✔ RAG local com arquivos externos
* ✔ Automação simulada (n8n-ready)
* ✔ Interface interativa com Streamlit
* ✔ Ambiente totalmente containerizado

---

## 📌 Conclusão

O projeto foi desenvolvido com foco em:

* Confiabilidade das respostas
* Organização arquitetural
* Escalabilidade
* Simulação de cenários reais de atendimento

---

## 👨‍💻 Autor

William Jesus
