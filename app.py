import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github
import base64

st.set_page_config(page_title="Sistema Operacional", page_icon="🎯", layout="wide")

# ==========================================
# INTEGRAÇÃO COM GITHUB
# ==========================================
def enviar_para_github(nome_arquivo_git, arquivo_carregado):
    try:
        # Puxa as credenciais seguras do Streamlit Secrets
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        
        # Lê o conteúdo do arquivo que você fez upload
        conteudo = arquivo_carregado.getvalue()
        
        try:
            # Tenta achar o arquivo no Git para ATUALIZAR
            arquivo_existente = repo.get_contents(nome_arquivo_git)
            repo.update_file(
                arquivo_existente.path,
                f"Atualização automática via Streamlit: {nome_arquivo_git}",
                conteudo,
                arquivo_existente.sha
            )
            return True, "Arquivo atualizado com sucesso no GitHub!"
        except Exception:
            # Se não existir, CRIA um novo
            repo.create_file(
                nome_arquivo_git,
                f"Criação automática via Streamlit: {nome_arquivo_git}",
                conteudo
            )
            return True, "Arquivo criado com sucesso no GitHub!"
            
    except Exception as e:
        return False, f"Erro na conexão com GitHub: {e}"

# ==========================================
# MENU DE NAVEGAÇÃO SUPERIOR
# ==========================================
# Usamos abas para criar o Menu do sistema
aba_dashboard, aba_upload = st.tabs(["📊 Dashboard de Indicadores", "⚙️ Envio de Arquivos (Admin)"])

# ==========================================
# ABA 1: ENVIO DE ARQUIVOS (ADMIN)
# ==========================================
with aba_upload:
    st.header("⚙️ Atualização da Base de Dados")
    st.markdown("Os ficheiros enviados aqui substituirão os dados oficiais armazenados no GitHub e alimentarão o Dashboard.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Substituir Base de Qualidade")
        up_aderencia = st.file_uploader("Envie o novo CSV de Aderência", type=["csv"], key="up_ad")
        if up_aderencia and st.button("Salvar Aderência no GitHub"):
            with st.spinner("Enviando para o GitHub..."):
                # Ele vai salvar com este nome fixo lá no seu repositório
                sucesso, msg = enviar_para_github("dados_aderencia.csv", up_aderencia)
                if sucesso: st.success(msg) else: st.error(msg)
                
        up_retencao = st.file_uploader("Envie o novo CSV de Retenção", type=["csv"], key="up_ret")
        if up_retencao and st.button("Salvar Retenção no GitHub"):
            with st.spinner("Enviando para o GitHub..."):
                sucesso, msg = enviar_para_github("dados_retencao.csv", up_retencao)
                if sucesso: st.success(msg) else: st.error(msg)

    with col2:
        st.subheader("Substituir Base Operacional")
        up_chat = st.file_uploader("Envie o novo CSV de Chat", type=["csv"], key="up_ch")
        if up_chat and st.button("Salvar Chat no GitHub"):
            with st.spinner("Enviando para o GitHub..."):
                sucesso, msg = enviar_para_github("dados_chat.csv", up_chat)
                if sucesso: st.success(msg) else: st.error(msg)
                
        # Você pode adicionar botões para Voz, Usuários e CSAT seguindo a mesma lógica...

# ==========================================
# ABA 2: DASHBOARD (LEITURA)
# ==========================================
with aba_dashboard:
    # --- INSIRA AQUI AS SUAS URLs RAW DO GITHUB ---
    # Atenção: O nome dos arquivos na URL deve bater com os nomes que você salvou na aba de Envio!
    URL_ADERENCIA = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/dados_aderencia.csv"
    URL_RETENCAO = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/dados_retencao.csv"
    
    st.sidebar.title("Navegação")
    perfil = st.sidebar.radio("Selecione o seu perfil:", ["Gestor", "Agente"])
    
    try:
        # Em vez de ler do file_uploader, agora o sistema lê direto do link do GitHub!
        df_perf = pd.read_csv(URL_ADERENCIA)
        df_ret = pd.read_csv(URL_RETENCAO)
        
        st.success("Bases de dados lidas diretamente do GitHub com sucesso!")
        
        # AQUI ENTRA O RESTANTE DO CÓDIGO DO DASHBOARD QUE JÁ CRIAMOS...
        if perfil == "Gestor":
            st.title("Dashboard do Gestor")
            st.dataframe(df_perf.head()) # Apenas um exemplo visual
            
    except Exception as e:
        st.warning("Aguardando o envio dos arquivos na aba 'Envio de Arquivos'.")
        st.error(f"Detalhe: {e}")
