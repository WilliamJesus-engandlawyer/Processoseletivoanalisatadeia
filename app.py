import os
import glob
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# ─────────────────────────────────────────────
# 1. BASE DE CONHECIMENTO
# ─────────────────────────────────────────────
def get_jogos_context() -> str:
    """Carrega os jogos disponíveis direto do banco de dados."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT nome, genero, preco, estoque FROM jogos ORDER BY genero, nome")
            )
            jogos = result.fetchall()
        if not jogos:
            return "⚠️ Nenhum jogo disponível no estoque no momento."
        ctx = "🎮 JOGOS DISPONÍVEIS NA GAMEVAULT:\n"
        for jogo in jogos:
            status = "✅ Disponível" if jogo.estoque > 0 else "❌ Esgotado"
            ctx += f"- {jogo.nome} | Gênero: {jogo.genero} | R${jogo.preco:.2f} | {status} (Qtd: {jogo.estoque})\n"
        return ctx
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return "Erro ao carregar estoque de jogos."

BASE_ESTATICA = """
HORÁRIO DE FUNCIONAMENTO: Segunda a sexta-feira, das 09h às 18h.
PRAZO DE ENTREGA: Até 5 dias úteis após confirmação do pedido.
POLÍTICA DE TROCA: 7 dias corridos após o recebimento do produto, mediante produto lacrado.
FORMAS DE PAGAMENTO: Cartão de crédito (até 12x), débito e Pix.
SUPORTE: atendimento@gamevault.com.br | (11) 4002-8922.
"""

# ─────────────────────────────────────────────
# 2. RAG LOCAL (pasta /data)
# ─────────────────────────────────────────────
def load_rag_knowledge(data_dir: str = "data") -> str:
    """Lê documentos .txt e .md da pasta /data para enriquecer a base de conhecimento."""
    docs: list[str] = []
    for pattern in ["**/*.txt", "**/*.md"]:
        for filepath in glob.glob(os.path.join(data_dir, pattern), recursive=True):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                    if content:
                        filename = os.path.relpath(filepath, data_dir)
                        docs.append(f"[Documento: {filename}]\n{content}")
            except Exception as e:
                print(f"[RAG ERROR] {filepath}: {e}")
    return "\n\n---\n\n".join(docs)[:30_000] if docs else "(Nenhum documento adicional encontrado.)"

# ─────────────────────────────────────────────
# 3. TOOLS (Ferramentas do Agente)
# ─────────────────────────────────────────────
@tool
def consultar_estoque_jogos(pergunta: str) -> str:
    """
    Use esta ferramenta SEMPRE que o cliente perguntar sobre:
    jogos disponíveis, gêneros, preços, estoque, recomendações de jogos ou catálogo.
    """
    jogos_ctx = get_jogos_context()
    rag = load_rag_knowledge()

    llm_rag = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    query = f"""
Você é um assistente de loja de games. Responda APENAS com base nos dados abaixo.
NUNCA invente informações, preços ou jogos que não estão listados.

ESTOQUE ATUAL:
{jogos_ctx}

DOCUMENTOS ADICIONAIS:
{rag}

PERGUNTA DO CLIENTE: {pergunta}

Responda de forma objetiva, amigável e em português do Brasil.
Se o jogo não estiver na lista, informe que não temos esse título disponível.
"""
    try:
        return llm_rag.invoke(query).content
    except Exception as e:
        return f"Não foi possível consultar o estoque agora: {e}"


@tool
def disparar_automacao_escalonamento(motivo: str) -> str:
    """
    Use esta ferramenta IMEDIATAMENTE quando:
    - O cliente usar linguagem agressiva, grosseira ou xingamentos.
    - O cliente pedir explicitamente para falar com um humano ou atendente.
    - O cliente relatar um problema grave (produto errado, fraude, cobrança indevida).
    Passe como argumento uma descrição resumida do motivo do escalonamento.
    """
    print(f"\n>> [WEBHOOK → n8n] ESCALONAMENTO ATIVADO: {motivo}\n")
    return (
        "Entendido. Já acionei nossa equipe de atendimento humano. "
        "Um atendente da GameVault entrará em contato em breve pelo canal que você preferir. "
        "Pedimos desculpas por qualquer inconveniente!"
    )

tools = [consultar_estoque_jogos, disparar_automacao_escalonamento]

# ─────────────────────────────────────────────
# 4. SYSTEM PROMPT — Coração do Agente
# ─────────────────────────────────────────────
SYSTEM_PROMPT = f"""
Você é a **Maya**, atendente virtual da **GameVault — Loja de Videogames**.
Seu objetivo é oferecer um atendimento excepcional, sempre educado, objetivo e prestativo.

═══════════════════════════════════════════════════════
REGRAS ABSOLUTAS (NUNCA quebre nenhuma delas):
═══════════════════════════════════════════════════════

1. **APENAS FALE O QUE VOCÊ SABE:**
   Só responda usando as informações da base de conhecimento abaixo ou das ferramentas disponíveis.
   Se não tiver a informação, responda EXATAMENTE:
   "Desculpe, não tenho essa informação no momento. Vou encaminhar seu contato para um atendente humano."
   Depois, use a ferramenta `disparar_automacao_escalonamento`.

2. **NUNCA INVENTE:**
   Não crie jogos, preços, prazos ou políticas que não estejam na base.
   Não opine sobre jogos que não estão no catálogo.
   Não compare com outras lojas.

3. **ESCALONAMENTO IMEDIATO:**
   Se o usuário:
   - Usar linguagem agressiva, grosseira ou xingamentos → use `disparar_automacao_escalonamento`
   - Pedir explicitamente um humano ou atendente → use `disparar_automacao_escalonamento`
   - Relatar problema grave (fraude, cobrança errada) → use `disparar_automacao_escalonamento`

4. **CONSULTA AO ESTOQUE:**
   Para qualquer dúvida sobre jogos, preços, gêneros ou disponibilidade → use `consultar_estoque_jogos`

5. **FOCO NO ATENDIMENTO:**
   Você é atendente de loja de games. Não responda sobre outros assuntos.
   Se tentarem te desviar do tema (política, receitas, código, etc.), redirecione educadamente:
   "Sou especialista em videogames! Posso te ajudar com nosso catálogo, entregas ou trocas. 😊"

6. **IDIOMA:** Sempre responda em português do Brasil, com tom amigável e levemente informal.

═══════════════════════════════════════════════════════
BASE DE CONHECIMENTO:
═══════════════════════════════════════════════════════
{BASE_ESTATICA}

{get_jogos_context()}
═══════════════════════════════════════════════════════
"""

MENSAGEM_BOAS_VINDAS = """👾 **Olá! Eu sou a Maya, sua assistente virtual da GameVault!** 🎮

Estou aqui para te ajudar com tudo sobre nossa loja:

🕹️ **Catálogo de jogos** — veja o que temos disponível  
💰 **Preços e promoções** — consulte valores do nosso estoque  
🚚 **Entrega** — prazo e condições de envio  
🔄 **Trocas e devoluções** — nossa política simplificada  
📞 **Falar com humano** — é só pedir!  

Como posso te ajudar hoje? 😊"""

# ─────────────────────────────────────────────
# 5. STREAMLIT — Interface
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="GameVault — Atendimento",
    page_icon="🎮",
    layout="centered",
)

# CSS customizado para visual gamer
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; }
    .stChatInputContainer { border-top: 2px solid #7c3aed; }
    h1 { color: #7c3aed; }
</style>
""", unsafe_allow_html=True)

st.title("🎮 GameVault — Atendimento Virtual")
st.caption("Maya | Assistente de IA • Online agora")
st.divider()

# Inicializa histórico e exibe boas-vindas
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": MENSAGEM_BOAS_VINDAS
    })

# Inicializa o agente
if "agent_executor" not in st.session_state:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,  # leve criatividade no tom, sem alucinar fatos
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    agent = create_tool_calling_agent(llm, tools, prompt)
    st.session_state.agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=8,
        return_intermediate_steps=False,
    )

# Renderiza histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
if user_input := st.chat_input("Digite sua mensagem para a Maya..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Maya está digitando..."):
            # Monta histórico para contexto do agente
            history = []
            for m in st.session_state.messages[:-1]:
                if m["role"] == "user":
                    history.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    history.append(AIMessage(content=m["content"]))

            try:
                response = st.session_state.agent_executor.invoke({
                    "input": user_input,
                    "chat_history": history,
                })
                full_response = response["output"]
            except Exception as e:
                full_response = (
                    "Ops! Encontrei um problema técnico agora. "
                    "Por favor, tente novamente em instantes. 🙏"
                )
                print(f"[AGENT ERROR] {e}")

        st.markdown(full_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })