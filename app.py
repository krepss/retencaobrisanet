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

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
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
    qtd_sim = (validos.astype(str).str.strip().str.upper() == 'SIM').sum()
    return (qtd_sim / len(validos)) * 100

def ms_para_minutos(ms):
    if pd.isna(ms): return 0.0
    return ms / 1000 / 60

def enviar_para_github(nome_arquivo_git, conteudo):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        
        # Verifica se é um ficheiro de upload direto ou texto processado
        if hasattr(conteudo, 'getvalue'):
            conteudo_final = conteudo.getvalue()
        else:
            conteudo_final = conteudo.encode('utf-8')
            
        try:
            arquivo_existente = repo.get_contents(nome_arquivo_git)
            repo.update_file(arquivo_existente.path, f"Atualização via Streamlit: {nome_arquivo_git}", conteudo_final, arquivo_existente.sha)
            st.cache_data.clear() 
            return True, f"{nome_arquivo_git} atualizado!"
        except Exception:
            repo.create_file(nome_arquivo_git, f"Criação via Streamlit: {nome_arquivo_git}", conteudo_final)
            st.cache_data.clear()
            return True, f"{nome_arquivo_git} criado!"
    except Exception as e:
        return False, f"Erro no GitHub: {e}"

@st.cache_data(ttl=600)
def carregar_dados_mestre():
    # Carrega a base de dados consolidada única
    url_dados = f"{BASE_URL}dados_consolidados_master.csv"
    df_completo = pd.read_csv(url_dados)
    # Garante que o Ano é tratado como string para facilitar os filtros
    df_completo['Ano'] = df_completo['Ano'].astype(str)
    return df_completo

# ==========================================
# TELA DE LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso ao Sistema</h1>", unsafe_allow_html=True)
    
    col_vazia1, col_login, col_vazia2 = st.columns([1, 2, 1])
    
    with col_login:
        st.markdown("### Por favor, insira as suas credenciais")
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
                    # Tenta ler a base mestre para ver os acessos. Se falhar, procura o ficheiro isolado
                    try:
                        df_users_login = pd.read_csv(f"{BASE_URL}dados_consolidados_master.csv")
                    except Exception:
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
                    st.warning("Base de acessos indisponível. Apenas o Gestor pode aceder para realizar a primeira configuração.")

# ==========================================
# SISTEMA LOGADO
# ==========================================
else:
    # --- BARRA LATERAL (COMUM A TODOS) ---
    st.sidebar.title("Opções")
    st.sidebar.success(f"Logado como: **{st.session_state.user_nome}**")
    
    st.sidebar.markdown("### 📅 Filtro de Período")
    mes_view = st.sidebar.selectbox("Selecione o Mês:", MESES)
    ano_view = st.sidebar.selectbox("Selecione o Ano:", ANOS)
    
    if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
        fazer_logout()
        st.rerun()
        
    st.sidebar.markdown("---")

    # --- CARREGAR DADOS ---
    try:
        df_completo = carregar_dados_mestre()
        # Filtra os dados em memória de acordo com o mês/ano selecionado na barra lateral
        df_periodo = df_completo[(df_completo['Mês'] == mes_view) & (df_completo['Ano'] == str(ano_view))]
        
        if df_periodo.empty:
            dados_carregados = False
            erro_dados = f"Ainda não existem registos para {mes_view} de {ano_view}."
        else:
            dados_carregados = True
    except urllib.error.HTTPError:
        dados_carregados = False
        erro_dados = "A base mestre ainda não foi criada no GitHub."
    except Exception as e:
        dados_carregados = False
        erro_dados = str(e)

    # ==========================================
    # VISÃO DO GESTOR
    # ==========================================
    if st.session_state.perfil == "Gestor":
        aba_dashboard, aba_upload = st.tabs(["📊 Dashboard de Indicadores", "⚙️ Consolidação e Envio"])
        
        # ABA: ADMINISTRAÇÃO E CONSOLIDAÇÃO
        with aba_upload:
            st.header("⚙️ Atualizar Base Histórica (Master)")
            
            st.info("👇 **Passo 1:** Indique qual Mês/Ano estes ficheiros representam.")
            col_m, col_a = st.columns(2)
            mes_up = col_m.selectbox("Mês dos dados:", MESES)
            ano_up = col_a.selectbox("Ano dos dados:", ANOS)
            
            st.markdown("---")
            st.write("👇 **Passo 2:** Envie os relatórios atuais nas caixas abaixo.")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                up_ad = st.file_uploader("1. Aderência", type=["csv"])
                up_pq = st.file_uploader("2. Pesquisa (CSAT/IR)", type=["csv"])
            with c2:
                up_ch = st.file_uploader("3. Chat", type=["csv"])
                up_vz = st.file_uploader("4. Voz", type=["csv"])
            with c3:
                up_rt = st.file_uploader("5. Retenção", type=["csv"])
                up_us = st.file_uploader("6. Lista de Utilizadores", type=["csv"])
                
            st.markdown("---")
            
            # BOTÃO ÚNICO DE PROCESSAMENTO
            if st.button("🚀 Processar e Atualizar Base Mestre", type="primary", use_container_width=True):
                if up_ad and up_pq and up_ch and up_vz and up_rt and up_us:
                    with st.spinner(f"A atualizar base com os dados de {mes_up}/{ano_up}... Aguarde!"):
                        try:
                            # 1. Lê ficheiros atuais
                            df_perf = pd.read_csv(up_ad)
                            df_ret = pd.read_csv(up_rt)
                            df_users = pd.read_csv(up_us)
                            df_chat = pd.read_csv(up_ch)
                            df_voz = pd.read_csv(up_vz)
                            df_pesq = pd.read_csv(up_pq)
                            
                            # 2. Tratamentos
                            df_perf['Aderência (%)'] = df_perf['Aderência (%)'].apply(limpar_porcentagem)
                            df_perf['Conformidade (%)'] = df_perf['Conformidade (%)'].apply(limpar_porcentagem)
                            df_perf['Chave_Nome'] = df_perf['Agente'].astype(str).str.strip().str.upper()
                            df_ret['Chave_Nome'] = df_ret['responsavel'].astype(str).str.strip().str.upper()
                            df_users['Chave_Nome'] = df_users['Nome'].astype(str).str.strip().str.upper()
                            
                            # 3. Agrupamentos
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

                            # 4. Cruzamento do Mês
                            df_novo = pd.merge(df_users, df_perf, on='Chave_Nome', how='left')
                            df_novo = pd.merge(df_novo, df_ret, on='Chave_Nome', how='left')
                            df_novo = pd.merge(df_novo, df_chat_agg, on='Chave_Nome', how='left')
                            df_novo = pd.merge(df_novo, df_voz_agg, on='Chave_Nome', how='left')
                            df_novo = pd.merge(df_novo, df_pesq_agg, on='Chave_Nome', how='left')
                            df_novo['Nome Exibição'] = df_novo['Chave_Nome'].str.title()
                            
                            # Adiciona as colunas de identificação de período
                            df_novo['Mês'] = mes_up
                            df_novo['Ano'] = str(ano_up)
                            
                            # 5. Lógica de INCREMENTO DA BASE MESTRE
                            url_master = f"{BASE_URL}dados_consolidados_master.csv"
                            try:
                                df_master = pd.read_csv(url_master)
                                df_master['Ano'] = df_master['Ano'].astype(str)
                                # Remove os dados antigos do mesmo mês/ano para não duplicar se você estiver atualizando o mesmo dia/mês
                                df_master = df_master[~((df_master['Mês'] == mes_up) & (df_master['Ano'] == str(ano_up)))]
                                # Junta tudo (dados passados + novos dados deste mês)
                                df_final = pd.concat([df_master, df_novo], ignore_index=True)
                            except Exception:
                                # Se a base mestre não existe (primeiro upload de sempre), ela será igual à nova
                                df_final = df_novo
                            
                            # 6. Guardar no GitHub
                            csv_final = df_final.to_csv(index=False)
                            suc_mega, msg_mega = enviar_para_github("dados_consolidados_master.csv", csv_final)
                            enviar_para_github("dados_usuarios.csv", up_us) # Backup dos utilizadores
                            
                            if suc_mega:
                                st.success(f"Tudo pronto! Base Mestre atualizada com sucesso para o período {mes_up}/{ano_up}.")
                            else:
                                st.warning("Houve um erro ao atualizar o repositório. Verifique as suas credenciais.")
                                
                        except Exception as e:
                            st.error(f"Erro durante o processamento dos dados: {e}")
                else:
                    st.error("⚠️ Estão a faltar ficheiros! Por favor, coloque os 6 relatórios nas caixas.")
                    
        # ABA: DASHBOARD GESTOR
        with aba_dashboard:
            if not dados_carregados:
                st.warning(f"⚠️ {erro_dados}")
            else:
                st.title(f"📈 Dashboard Operacional ({mes_view}/{ano_view})")
                agentes = ["Todos"] + list(df_periodo['Nome Exibição'].dropna().unique())
                filtro_agente = st.selectbox("Filtrar visualização por Agente:", agentes)
                
                df_view = df_periodo[df_periodo['Nome Exibição'] == filtro_agente] if filtro_agente != "Todos" else df_periodo.copy()

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
            st.warning(f"⚠️ {erro_dados}")
        else:
            st.title(f"👤 O Meu Painel ({mes_view}/{ano_view})")
            
            meus_dados = df_periodo[df_periodo['E-mail'] == st.session_state.user_email]
            
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
                cr3.metric("A Minha Taxa", f"{minha_tx_ret:.2f}%")
            else:
                st.info("Ainda não tem métricas registadas para si neste período. Vá acompanhando as próximas atualizações!")
