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
arquivo_pesquisa = st.sidebar.file_uploader("6. Pesquisa CSAT / IR", type=["csv"])

# Verifica se os principais arquivos estão presentes
if arquivo_aderencia and arquivo_retencao and arquivo_usuarios and arquivo_chat and arquivo_voz and arquivo_pesquisa:
    try:
        # Lendo todos os arquivos
        df_perf = pd.read_csv(arquivo_aderencia)
        df_ret = pd.read_csv(arquivo_retencao)
        df_users = pd.read_csv(arquivo_usuarios)
        df_chat = pd.read_csv(arquivo_chat)
        df_voz = pd.read_csv(arquivo_voz)
        df_pesq = pd.read_csv(arquivo_pesquisa)
        
        # ------------------------------------------
        # TRATAMENTO DE DADOS (PREPARAÇÃO)
        # ------------------------------------------
        # Aderência
        df_perf['Aderência (%)'] = df_perf['Aderência (%)'].apply(limpar_porcentagem)
        df_perf['Conformidade (%)'] = df_perf['Conformidade (%)'].apply(limpar_porcentagem)
        df_perf['Chave_Nome'] = df_perf['Agente'].astype(str).str.strip().str.upper()
        
        # Retenção
        df_ret['Chave_Nome'] = df_ret['responsavel'].astype(str).str.strip().str.upper()
        
        # Usuários
        df_users['Chave_Nome'] = df_users['Nome'].astype(str).str.strip().str.upper()
        
        # Chat
        df_chat['Chave_Nome'] = df_chat['Nome do agente'].astype(str).str.strip().str.upper()
        df_chat_agg = df_chat.groupby('Chave_Nome').agg({
            'Atendidas': 'sum',
            'Tratamento médio': 'mean',
            'Espera média': 'mean'
        }).reset_index()
        df_chat_agg.rename(columns={'Atendidas': 'Vol. Chat', 'Tratamento médio': 'TMA Chat (ms)', 'Espera média': 'TME Chat (ms)'}, inplace=True)
        df_chat_agg['TMA Chat (Min)'] = df_chat_agg['TMA Chat (ms)'].apply(ms_para_minutos)
        df_chat_agg['TME Chat (Min)'] = df_chat_agg['TME Chat (ms)'].apply(ms_para_minutos)
        
        # Voz
        df_voz['Chave_Nome'] = df_voz['Nome do agente'].astype(str).str.strip().str.upper()
        df_voz_agg = df_voz.groupby('Chave_Nome').agg({
            'Atendidas': 'sum',
            'Tratamento médio': 'mean',
            'Espera média': 'mean'
        }).reset_index()
        df_voz_agg.rename(columns={'Atendidas': 'Vol. Voz', 'Tratamento médio': 'TMA Voz (ms)', 'Espera média': 'TME Voz (ms)'}, inplace=True)
        df_voz_agg['TMA Voz (Min)'] = df_voz_agg['TMA Voz (ms)'].apply(ms_para_minutos)
        df_voz_agg['TME Voz (Min)'] = df_voz_agg['TME Voz (ms)'].apply(ms_para_minutos)
        
        # Pesquisa de Satisfação (CSAT e IR)
        df_pesq['Chave_Nome'] = df_pesq['Atendente'].astype(str).str.strip().str.upper()
        df_pesq['CSAT'] = pd.to_numeric(df_pesq['CSAT'], errors='coerce')
        df_pesq_agg = df_pesq.groupby('Chave_Nome').agg(
            CSAT_Media=('CSAT', 'mean'),
            IR_Percentual=('IR', calcular_ir)
        ).reset_index()

        # ------------------------------------------
        # MESCLANDO TUDO (MEGA TABELA)
        # ------------------------------------------
        df_completo = pd.merge(df_users, df_perf, on='Chave_Nome', how='left')
        df_completo = pd.merge(df_completo, df_ret, on='Chave_Nome', how='left')
        df_completo = pd.merge(df_completo, df_chat_agg, on='Chave_Nome', how='left')
        df_completo = pd.merge(df_completo, df_voz_agg, on='Chave_Nome', how='left')
        df_completo = pd.merge(df_completo, df_pesq_agg, on='Chave_Nome', how='left')
        
        df_completo['Nome Exibição'] = df_completo['Chave_Nome'].str.title()

        # ==========================================
        # VISÃO DO GESTOR
        # ==========================================
        if perfil == "Gestor":
            st.title("📈 Dashboard Operacional 360 - Gestor")
            
            # Filtro de Agente
            agentes = ["Todos"] + list(df_completo['Nome Exibição'].dropna().unique())
            filtro_agente = st.selectbox("Filtrar visualização por Agente:", agentes)
            
            if filtro_agente != "Todos":
                df_view = df_completo[df_completo['Nome Exibição'] == filtro_agente]
            else:
                df_view = df_completo.copy()

            # Resumo Geral
            st.subheader("🎯 KPIs Globais")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Média CSAT", f"{df_view['CSAT_Media'].mean():.2f}")
            col2.metric("Média IR", f"{df_view['IR_Percentual'].mean():.2f}%")
            col3.metric("Média Aderência", f"{df_view['Aderência (%)'].mean():.2f}%")
            col4.metric("Média Conformidade", f"{df_view['Conformidade (%)'].mean():.2f}%")
            
            st.markdown("---")
            
            st.subheader("🎧 Volume e Tempos de Atendimento (Médias)")
            c_op1, c_op2, c_op3, c_op4 = st.columns(4)
            c_op1.metric("Total Vol. Chat", int(df_view['Vol. Chat'].sum()))
            c_op2.metric("TMA Médio Chat", f"{df_view['TMA Chat (Min)'].mean():.1f} min")
            c_op3.metric("Total Vol. Voz", int(df_view['Vol. Voz'].sum()))
            c_op4.metric("TMA Médio Voz", f"{df_view['TMA Voz (Min)'].mean():.1f} min")

            st.markdown("---")
            
            st.subheader("👥 Visão Consolidada por Agente")
            # Preparando a tabela do Gestor
            colunas_exibicao = [
                'Nome Exibição', 'CSAT_Media', 'IR_Percentual', 'Aderência (%)', 'Conformidade (%)',
                'Vol. Chat', 'TMA Chat (Min)', 'Vol. Voz', 'TMA Voz (Min)', 'RT geral', 'RT geral valido'
            ]
            
            df_tabela = df_view[colunas_exibicao].copy()
            df_tabela['% Retenção'] = (df_tabela['RT geral valido'] / df_tabela['RT geral']) * 100
            
            st.dataframe(df_tabela.style.format({
                'CSAT_Media': '{:.2f}', 'IR_Percent
