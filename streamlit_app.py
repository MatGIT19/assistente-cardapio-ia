"""Interface de chat. Rode com: streamlit run streamlit_app.py"""

import os

import streamlit as st

st.set_page_config(page_title="Assistente de Cardápio", page_icon="🍕")

# No Streamlit Community Cloud a chave fica em Settings -> Secrets
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    pass

from app.agent import criar_agente  # noqa: E402  (precisa da chave já definida)


@st.cache_resource
def carregar_agente():
    return criar_agente()


st.title("🍕 Assistente da Cantina Vila Nova")
st.caption(
    "Pergunte sobre o cardápio, alérgenos e preços, peça uma sugestão dentro do seu orçamento "
    "ou consulte um pedido (teste os números 1001 a 1012). Restaurante e dados fictícios."
)

try:
    agente = carregar_agente()
except RuntimeError as erro:
    st.error(str(erro))
    st.stop()

if "historico" not in st.session_state:
    st.session_state.historico = []
    st.session_state.detalhes = []

with st.sidebar:
    st.subheader("Experimente")
    for exemplo in (
        "Quais pratos são veganos?",
        "A pizza de calabresa tem lactose?",
        "Cadê meu pedido 1006?",
        "Tenho R$ 100 para duas pessoas, o que peço?",
        "Vocês têm sushi?",
    ):
        if st.button(exemplo, use_container_width=True):
            st.session_state.pergunta_exemplo = exemplo
    st.divider()
    st.subheader("Como cheguei na última resposta")
    if st.session_state.detalhes:
        ultimo = st.session_state.detalhes[-1]
        st.markdown("**Itens buscados no cardápio (RAG)**")
        for item in ultimo.itens_recuperados:
            st.write(f"{item['nome']} · similaridade {item['similaridade']}")
        st.markdown("**Ferramentas chamadas**")
        if ultimo.ferramentas:
            for f in ultimo.ferramentas:
                with st.expander(f"{f['nome']}({f['argumentos']})"):
                    st.json(f["resultado"])
        else:
            st.write("Nenhuma.")

for m in st.session_state.historico:
    with st.chat_message("user" if m["papel"] == "usuario" else "assistant"):
        st.markdown(m["texto"])

pergunta = st.chat_input("Digite sua pergunta") or st.session_state.pop("pergunta_exemplo", None)
if pergunta:
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Consultando o cardápio..."):
            resposta = agente.responder(pergunta, st.session_state.historico[-10:])
        st.markdown(resposta.texto)
    st.session_state.historico += [
        {"papel": "usuario", "texto": pergunta},
        {"papel": "assistente", "texto": resposta.texto},
    ]
    st.session_state.detalhes.append(resposta)
    st.rerun()  # atualiza a barra lateral com os detalhes desta resposta
