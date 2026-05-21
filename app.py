import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Operacional 360", page_icon="🎯", layout="wide")

# ==========================================
# FUNÇÕES DE LIMPEZA E TRATAMENTO
# ==========================================
def limpar_porcentagem(valor):
    if pd.isna(valor):
        return 0.0
    valor_str = str(valor).replace('%', '').replace(',', '.')
    if valor_str.lower() == 'nan':
        return 0.0
    return float(valor_str)

def calcular_ir(serie_ir):
    # Calcula a % de 'Sim' no total de respostas válidas de IR
    validos = serie_ir.dropna()
    if len(validos) == 0:
        return 0.0
    qtd_sim = (validos.str.strip().str.upper() == 'SIM').sum()
    return (qtd_sim / len(validos)) * 100

def ms_para_minutos(ms):
    if pd.isna(ms):
        return 0.0
    return ms / 1000 / 60

# ==========================================
# 1. BARRA LATERAL - NAVEGAÇÃO E UPLOAD
# ==========================================
st.sidebar.title("Navegação")
perfil = st.sidebar.radio("Selecione o seu perfil:", ["Gestor", "Agente"])
st.sidebar.markdown("---")

st.sidebar.subheader("📥 Upload de Relatórios")
arquivo_aderencia = st.sidebar.file_uploader("1. Aderência e Conformidade", type=["csv"])
arquivo_retencao = st.sidebar.file_uploader("2. Relatório de Retenção", type=["csv"])
arquivo_usuarios = st.sidebar.file_uploader("3. Lista de Usuários", type=["csv"])
arquivo_chat = st.sidebar.file_uploader("4. Relatório de Chat", type=["csv"])
arquivo_voz = st.sidebar.file_uploader("5. Relatório de Voz", type=["csv"])
arquivo_pesquisa = st.sidebar.file_uploader("
