import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github
import urllib.error

# ==========================================
# CONFIGURAÇÕES GERAIS E CREDENCIAIS
# ==========================================
st.set_page_config(page_title="Sistema Operacional 360", page_icon="🎯", layout="wide")

GESTOR_EMAIL = "admin@brisanet.com.br"
GESTOR_SENHA = "admin"
SENHA_PADRAO_AGENTE = "1234" 

# IMPORTANTE: SUBSTITUA PELOS SEUS DADOS DO GITHUB
BASE_URL = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/"

# Dicionários de Controle Mensal
MESES = {
    "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04",
    "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
    "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
}
ANOS = ["2026", "2027", "2028", "2029", "2030"]

# ==========================================
# GESTÃO DE SESSÃO (MEMÓRIA DE LOGIN)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.perfil = ""
    st.session_state.user_email = ""
    st.session_state.user_nome = ""

def fazer_logout():
    st.session_state.logged_in = False
    st.session_state.perfil = ""
    st.session_state.user_email = ""
    st.session_state.user_nome = ""
    st.cache_data.clear() 

# ==========================================
# FUNÇÕES DE TRATAMENTO E GITHUB
# ==========================================
def limpar_porcentagem(valor):
    if pd.isna(valor): return 0.0
    valor_str = str(valor).replace('%', '').replace(',', '.')
    if valor_str.lower() == 'nan': return 0.0
    return float(valor_str)

def calcular_ir(serie_ir):
    validos = serie_ir.dropna()
    if len(validos) == 0: return 0.0
    qtd_sim = (validos.str.strip().str.upper() == 'SIM').sum()
    return (qtd_sim / len(validos)) * 100

def ms_para_minutos(ms):
    if pd.isna(ms): return 0.0
    return ms / 1000 / 60

def enviar_para_github(nome_arquivo_git, arquivo_carregado):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        conteudo = arquivo_carregado.getvalue()
        
        try:
            arquivo_existente = repo.get_contents(nome_arquivo_git)
            repo.update_file(arquivo_existente.path, f"Atualização via Streamlit: {nome_arquivo_git}", conteudo, arquivo_existente.sha)
            st.cache_data.clear() 
            return True, f"{nome_arquivo_git} atualizado!"
        except Exception:
            repo.create_file(nome_arquivo_git, f"Criação via Streamlit: {nome_arquivo_git}", conteudo)
            st.cache_data.clear()
            return True, f"{nome_arquivo_git} criado!"
    except Exception as e:
        return False, f"Erro no GitHub: {e}"

@st.cache_data(ttl=600)
def carregar_todos_os_dados(sufixo_mes_ano):
    # A lista de usuários não precisa de mês, ela é uma base fixa global que você atualiza quando entra/sai alguém
    df_users = pd.read_csv(f"{BASE_URL}dados_usuarios.csv")
    
    # Os outros arquivos ganham a tag do mês (ex: dados_aderencia_05_2026.csv)
    df_perf = pd.read_csv(f"{BASE_URL}dados_aderencia_{sufixo_mes_ano}.csv")
    df_ret = pd.read_csv(f"{BASE_URL}dados_retencao_{sufixo_mes_ano}.csv")
    df_chat = pd.read_csv(f"{BASE_URL}dados_chat_{sufixo_mes_ano}.csv")
    df_voz = pd.read_csv(f"{BASE_URL}dados_voz_{sufixo_mes_ano}.csv")
    df_pesq = pd.read_csv(f"{BASE_URL}dados_pesquisa_{sufixo_mes_ano}.csv")
    
    # Tratamentos de texto
    df_perf['Aderência (%)'] = df_perf['Aderência (%)'].apply(limpar_porcentagem)
    df_perf['Conformidade (%)'] = df_perf['Conformidade (%)'].apply(limpar_porcentagem)
    df_perf['Chave_Nome'] = df_perf['Agente'].astype(str).str.strip().str.upper()
    df_ret['Chave_Nome'] = df_ret['responsavel'].astype(str).str.strip().str.upper()
    df_users['Chave_Nome'] = df_users['Nome'].astype(str).str.strip().str.upper()
    
    df_chat['Chave_Nome'] = df_chat['Nome do agente'].astype(str).str.strip().str.upper()
    df_chat_agg = df_chat.groupby('Chave_Nome').agg({'Atendidas': 'sum', 'Tratamento médio': 'mean', 'Espera média': 'mean'}).reset_index()
    df_chat_agg.rename(columns={'Atendidas': 'Vol. Chat', 'Tratamento médio': 'TMA Chat (ms)', 'Espera média': 'TME Chat (ms)'}, inplace=True)
    df_chat_agg['TMA Chat (Min)'] = df_chat_agg['TMA Chat (ms)'].apply(ms_para_minutos)
    df_chat_agg['TME Chat (Min)'] = df_chat_agg['TME Chat (ms)'].apply(ms_para_minutos)
    
    df_voz['Chave_Nome'] = df_voz['Nome do agente'].astype(str).str.strip().str.upper()
    df_voz_agg = df_voz.groupby('Chave_Nome').agg({'Atendidas': 'sum', 'Tratamento médio': 'mean', 'Espera média': 'mean'}).reset_index()
    df_voz_agg.rename(columns={'Atendidas': 'Vol. Voz', 'Tratamento médio': 'TMA Voz (ms)', 'Espera média': 'TME Voz (ms)'}, inplace=True)
    df_voz_agg['TMA Voz (Min)'] = df_voz_agg['TMA Voz (ms)'].apply(ms_para_minutos)
    df_voz_agg['TME Voz (Min)'] = df_voz_agg['TME Voz (ms)'].apply(ms_para_minutos)
    
    df_pesq['Chave_Nome'] = df_pesq['Atendente'].astype(str).str.strip().str.upper()
    df_pesq['CSAT'] = pd.to_numeric(df_pesq['CSAT'], errors='coerce')
    df_pesq_agg = df_pesq.groupby('Chave_Nome').agg(CSAT_Media=('CSAT', 'mean'), IR_Percentual=('IR', calcular_ir)).reset_index()

    # Cruzamento de dados
    df_completo = pd.merge(df_users, df_perf, on='Chave_Nome', how='left')
    df_completo = pd.merge(df_completo, df_ret, on='Chave_Nome', how='left')
    df_completo = pd.merge(df_completo, df_chat_agg, on='Chave_Nome', how='left')
    df_completo = pd.merge(df_completo, df_voz_agg, on='Chave_Nome', how='left')
    df_completo = pd.merge(df_completo, df_pesq_agg, on='Chave_Nome', how='left')
    df_completo['Nome Exibição'] = df_completo['Chave_Nome'].str.title()
    
    return df_completo

# ==========================================
# TELA DE LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso ao Sistema</h1>", unsafe_allow_html=True)
    
    col_vazia1, col_login, col_vazia2 = st.columns([1, 2, 1])
    
    with col_login:
        st.markdown("### Por favor, insira suas credenciais")
        email_input = st.text_input("E-mail corporativo")
        senha_input = st.text_input("Senha", type="password")
        
        if st.button("Entrar", use_container_width=True):
            if email_input == GESTOR_EMAIL and senha_input == GESTOR_SENHA:
                st.session_state.logged_in = True
                st.session_state.perfil = "Gestor"
                st.session_state.user_nome = "Gestor"
                st.rerun() 
            else:
                try:
                    df_users_login = pd.read_csv(f"{BASE_URL}dados_usuarios.csv")
                    lista_emails = df_users_login['E-mail'].dropna().tolist()
                    
                    if email_input in lista_emails and senha_input == SENHA_PADRAO_AGENTE:
                        nome_operador = df_users_login[df_users_login['E-mail'] == email_input].iloc[0]['Nome']
                        st.session_state.logged_in = True
                        st.session_state.perfil = "Agente"
                        st.session_state.user_email = email_input
                        st.session_state.user_nome = str(nome_operador).title()
                        st.rerun()
                    else:
                        st.error("E-mail não encontrado ou senha incorreta.")
                except Exception:
                    st.warning("Base indisponível. Apenas o Gestor pode acessar para realizar a primeira configuração.")

# ==========================================
# SISTEMA LOGADO
# ==========================================
else:
    # --- BARRA LATERAL (COMUM A TODOS) ---
    st.sidebar.title("Opções")
    st.sidebar.success(f"Logado como: **{st.session_state.user_nome}**")
    
    # Controle Mensal na Barra Lateral
    st.sidebar.markdown("### 📅 Filtro de Período")
    mes_view = st.sidebar.selectbox("Selecione o Mês:", list(MESES.keys()))
    ano_view = st.sidebar.selectbox("Selecione o Ano:", ANOS)
    sufixo_view = f"{MESES[mes_view]}_{ano_view}"
    
    if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
        fazer_logout()
        st.rerun()
        
    st.sidebar.markdown("---")

    # --- CARREGAR DADOS ---
    try:
        df_completo = carregar_todos_os_dados(sufixo_view)
        dados_carregados = True
    except urllib.error.HTTPError:
        # Erro específico se o arquivo daquele mês não existir no GitHub
        dados_carregados = False
        erro_dados = "Não há dados cadastrados para o período selecionado."
    except Exception as e:
        dados_carregados = False
        erro_dados = str(e)

    # ==========================================
    # VISÃO DO GESTOR
    # ==========================================
    if st.session_state.perfil == "Gestor":
        aba_dashboard, aba_upload = st.tabs(["📊 Dashboard de Indicadores", "⚙️ Administração e Envio"])
        
        # ABA: ADMINISTRAÇÃO
        with aba_upload:
            st.header("⚙️ Atualização da Base de Dados")
            
            st.info("👇 **Passo 1:** Selecione de qual Mês e Ano são os arquivos que você vai subir agora.")
            col_m, col_a = st.columns(2)
            mes_up = col_m.selectbox("Mês de Referência para envio:", list(MESES.keys()))
            ano_up = col_a.selectbox("Ano para envio:", ANOS)
            sufixo_up = f"{MESES[mes_up]}_{ano_up}"
            
            st.markdown("---")
            st.write("👇 **Passo 2:** Faça o upload dos relatórios exportados do seu sistema.")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.subheader("Qualidade")
                up_ad = st.file_uploader("1. Aderência", type=["csv"], key="ad")
                if up_ad and st.button("Salvar Aderência"):
                    suc, msg = enviar_para_github(f"dados_aderencia_{sufixo_up}.csv", up_ad)
                    if suc: st.success(msg) else: st.error(msg)
                        
                up_pq = st.file_uploader("2. Pesquisa", type=["csv"], key="pq")
                if up_pq and st.button("Salvar Pesquisa"):
                    suc, msg = enviar_para_github(f"dados_pesquisa_{sufixo_up}.csv", up_pq)
                    if suc: st.success(msg) else: st.error(msg)
            with c2:
                st.subheader("Operação")
                up_ch = st.file_uploader("3. Chat", type=["csv"], key="ch")
                if up_ch and st.button("Salvar Chat"):
                    suc, msg = enviar_para_github(f"dados_chat_{sufixo_up}.csv", up_ch)
                    if suc: st.success(msg) else: st.error(msg)
                        
                up_vz = st.file_uploader("4. Voz", type=["csv"], key="vz")
                if up_vz and st.button("Salvar Voz"):
                    suc, msg = enviar_para_github(f"dados_voz_{sufixo_up}.csv", up_vz)
                    if suc: st.success(msg) else: st.error(msg)
            with c3:
                st.subheader("Retenção/Acessos")
                up_rt = st.file_uploader("5. Retenção", type=["csv"], key="rt")
                if up_rt and st.button("Salvar Retenção"):
                    suc, msg = enviar_para_github(f"dados_retencao_{sufixo_up}.csv", up_rt)
                    if suc: st.success(msg) else: st.error(msg)
                        
                up_us = st.file_uploader("6. Lista de Usuários", type=["csv"], key="us")
                if up_us and st.button("Salvar Usuários (Geral)"):
                    # A lista de usuários não tem sufixo de mês, é única.
                    suc, msg = enviar_para_github("dados_usuarios.csv", up_us)
                    if suc: st.success(msg) else: st.error(msg)
                    
        # ABA: DASHBOARD GESTOR
        with aba_dashboard:
            if not dados_carregados:
                st.warning(f"⚠️ {erro_dados}")
                st.info(f"Vá na aba de Administração, selecione **{mes_view}/{ano_view}** e envie os arquivos.")
            else:
                st.title(f"📈 Dashboard Operacional ({mes_view}/{ano_view})")
                agentes = ["Todos"] + list(df_completo['Nome Exibição'].dropna().unique())
                filtro_agente = st.selectbox("Filtrar visualização por Agente:", agentes)
                
                df_view = df_completo[df_completo['Nome Exibição'] == filtro_agente] if filtro_agente != "Todos" else df_completo.copy()

                st.subheader("🎯 KPIs Globais")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Média CSAT", f"{df_view['CSAT_Media'].mean():.2f}")
                col2.metric("Média IR", f"{df_view['IR_Percentual'].mean():.2f}%")
                col3.metric("Média Aderência", f"{df_view['Aderência (%)'].mean():.2f}%")
                col4.metric("Média Conformidade", f"{df_view['Conformidade (%)'].mean():.2f}%")
                st.markdown("---")
                
                st.subheader("👥 Visão Consolidada por Agente")
                colunas = ['Nome Exibição', 'CSAT_Media', 'IR_Percentual', 'Aderência (%)', 'Conformidade (%)', 'Vol. Chat', 'TMA Chat (Min)', 'Vol. Voz', 'TMA Voz (Min)', 'RT geral', 'RT geral valido']
                df_tabela = df_view[colunas].copy()
                df_tabela['% Retenção'] = (df_tabela['RT geral valido'] / df_tabela['RT geral']) * 100
                st.dataframe(df_tabela.style.format({'CSAT_Media': '{:.2f}', 'IR_Percentual': '{:.2f}%', 'Aderência (%)': '{:.2f}%', 'Conformidade (%)': '{:.2f}%', '% Retenção': '{:.2f}%', 'TMA Chat (Min)': '{:.1f}m', 'TMA Voz (Min)': '{:.1f}m'}), use_container_width=True)

    # ==========================================
    # VISÃO DO AGENTE (INDIVIDUAL E DIRETA)
    # ==========================================
    elif st.session_state.perfil == "Agente":
        if not dados_carregados:
            st.error(f"⚠️ {erro_dados}")
        else:
            st.title(f"👤 Meu Painel ({mes_view}/{ano_view})")
            
            meus_dados = df_completo[df_completo['E-mail'] == st.session_state.user_email]
            
            if not meus_dados.empty:
                dados = meus_dados.iloc[0]
                
                st.markdown("### ⭐ Satisfação e Qualidade")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Minha Nota CSAT", f"{dados['CSAT_Media']:.2f}" if pd.notna(dados['CSAT_Media']) else "N/A")
                c2.metric("Meu IR (%)", f"{dados['IR_Percentual']:.2f}%" if pd.notna(dados['IR_Percentual']) else "N/A")
                c3.metric("Minha Aderência", f"{dados['Aderência (%)']:.2f}%" if pd.notna(dados['Aderência (%)']) else "N/A")
                c4.metric("Minha Conformidade", f"{dados['Conformidade (%)']:.2f}%" if pd.notna(dados['Conformidade (%)']) else "N/A")
                st.markdown("---")
                
                st.markdown("### 🎧 Operação (Chat / Voz)")
                co1, co2, co3, co4 = st.columns(4)
                co1.metric("Volume Chat", int(dados['Vol. Chat']) if pd.notna(dados['Vol. Chat']) else 0)
                co2.metric("Meu TMA Chat", f"{dados['TMA Chat (Min)']:.1f} min" if pd.notna(dados['TMA Chat (Min)']) else "N/A")
                co3.metric("Volume Voz", int(dados['Vol. Voz']) if pd.notna(dados['Vol. Voz']) else 0)
                co4.metric("Meu TMA Voz", f"{dados['TMA Voz (Min)']:.1f} min" if pd.notna(dados['TMA Voz (Min)']) else "N/A")
                st.markdown("---")
                
                st.markdown("### 💰 Retenção")
                rt_geral = dados['RT geral']
                rt_valido = dados['RT geral valido']
                minha_tx_ret = (rt_valido / rt_geral * 100) if pd.notna(rt_geral) and rt_geral > 0 else 0
                
                cr1, cr2, cr3 = st.columns(3)
                cr1.metric("Volume Tratado", int(rt_geral) if pd.notna(rt_geral) else 0)
                cr2.metric("Volume Retido", int(rt_valido) if pd.notna(rt_valido) else 0)
                cr3.metric("Minha Taxa", f"{minha_tx_ret:.2f}%")
            else:
                st.warning("Você logou com sucesso, mas não há dados operacionais vinculados ao seu e-mail neste mês.")
