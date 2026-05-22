import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github
import io
import time

# ==========================================
# CONFIGURAÇÕES GERAIS E CREDENCIAIS
# ==========================================
st.set_page_config(page_title="Sistema Operacional 360", page_icon="🎯", layout="wide")

GESTOR_EMAIL = "gestor"
GESTOR_SENHA = "admin"
SENHA_PADRAO_AGENTE = "1234" 

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
ANOS = ["2026", "2027", "2028", "2029", "2030"]

st.markdown("""
    <style>
        .kpi-card {
            background-color: #f8f9fa;
            border-left: 5px solid #007bff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
            text-align: center;
            margin-bottom: 15px;
        }
        .kpi-title {
            font-size: 14px;
            color: #6c757d;
            text-transform: uppercase;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .kpi-value {
            font-size: 28px;
            color: #212529;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GESTÃO DE SESSÃO NATIVA
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
# FUNÇÕES DE LEITURA E GRAVAÇÃO VIA API GITHUB
# ==========================================
def ler_csv_via_api_github(nome_arquivo):
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["GITHUB_REPO"])
    arquivo_git = repo.get_contents(nome_arquivo)
    conteudo_texto = arquivo_git.decoded_content.decode('utf-8')
    return pd.read_csv(io.StringIO(conteudo_texto))

def enviar_para_github(nome_arquivo_git, conteudo):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        
        if hasattr(conteudo, 'getvalue'):
            conteudo_final = conteudo.getvalue()
        else:
            conteudo_final = conteudo.encode('utf-8')
            
        try:
            arquivo_existente = repo.get_contents(nome_arquivo_git)
            repo.update_file(arquivo_existente.path, f"Atualização via Streamlit: {nome_arquivo_git}", conteudo_final, arquivo_existente.sha)
            return True, f"{nome_arquivo_git} atualizado!"
        except Exception:
            repo.create_file(nome_arquivo_git, f"Criação via Streamlit: {nome_arquivo_git}", conteudo_final)
            return True, f"{nome_arquivo_git} criado!"
    except Exception as e:
        return False, f"Erro no GitHub: {e}"

def limpar_porcentagem(valor):
    if pd.isna(valor): return 0.0
    try:
        val = float(valor)
        if val <= 1.0 and val > 0:
            return val * 100
        return val
    except ValueError:
        valor_str = str(valor).replace('%', '').replace(',', '.')
        if valor_str.lower() == 'nan': return 0.0
        return float(valor_str)

def ms_para_minutos(ms):
    if pd.isna(ms): return 0.0
    return ms / 1000 / 60

@st.cache_data(ttl=5)
def carregar_dados_mestre_seguro():
    df = ler_csv_via_api_github("dados_consolidados_master.csv")
    df['text_ano'] = df['Ano'].astype(str).str.strip()
    df['text_mes'] = df['Mês'].astype(str).str.strip().str.title()
    return df

# ==========================================
# TELA DE LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso ao Sistema Operacional 360</h1>", unsafe_allow_html=True)
    
    col_vazia1, col_login, col_vazia2 = st.columns([1, 2, 1])
    
    with col_login:
        with st.form("form_login"):
            st.markdown("### Por favor, insira as suas credenciais")
            email_input = st.text_input("E-mail corporativo")
            senha_input = st.text_input("Senha", type="password")
            submit_login = st.form_submit_button("Entrar", use_container_width=True)
        
        if submit_login:
            email_limpo = email_input.strip().lower()
            senha_limpa = senha_input.strip()
            
            if email_limpo == GESTOR_EMAIL.lower() and senha_limpa == GESTOR_SENHA:
                st.session_state.logged_in = True
                st.session_state.perfil = "Gestor"
                st.session_state.user_nome = "Gestor"
                st.success("Login efetuado com sucesso!")
                time.sleep(0.5)
                st.rerun() 
            else:
                try:
                    df_users_login = ler_csv_via_api_github("dados_usuarios.csv")
                    lista_emails = df_users_login['E-mail'].dropna().str.strip().str.lower().tolist()
                    
                    if email_limpo in lista_emails and senha_limpa == SENHA_PADRAO_AGENTE:
                        dados_usr = df_users_login[df_users_login['E-mail'].str.strip().str.lower() == email_limpo].iloc[0]
                        st.session_state.logged_in = True
                        st.session_state.perfil = "Agente"
                        st.session_state.user_email = email_limpo
                        st.session_state.user_nome = str(dados_usr['Nome']).title()
                        st.success("Login efetuado com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ E-mail não encontrado ou senha incorreta.")
                except Exception:
                    st.warning("⚠️ Base de dados de utilizadores indisponível no repositório.")

# ==========================================
# SISTEMA LOGADO
# ==========================================
else:
    st.sidebar.title("Opções")
    st.sidebar.success(f"Logado como: **{st.session_state.user_nome}**")
    
    st.sidebar.markdown("### 📅 Filtro de Período")
    mes_view = st.sidebar.selectbox("Selecione o Mês:", MESES, index=4) 
    ano_view = st.sidebar.selectbox("Selecione o Ano:", ANOS)
    
    if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
        fazer_logout()
        st.rerun()
        
    st.sidebar.markdown("---")

    base_mestre_existe = True
    erro_dados = ""
    
    try:
        df_completo = carregar_dados_mestre_seguro()
        df_periodo = df_completo[(df_completo['text_mes'].str.lower() == mes_view.lower()) & (df_completo['text_ano'] == str(ano_view))]
        
        if df_periodo.empty:
            dados_carregados = False
            erro_dados = f"Ainda não existem registos consolidados para {mes_view} de {ano_view}."
        else:
            dados_carregados = True
    except Exception as e:
        base_mestre_existe = False
        dados_carregados = False
        erro_dados = str(e)

    # ==========================================
    # VISÃO DO GESTOR
    # ==========================================
    if st.session_state.perfil == "Gestor":
        aba_dashboard, aba_upload, aba_equipe = st.tabs(["📊 Dashboard de Indicadores", "⚙️ Consolidação (Mensal)", "👥 Gestão da Equipe"])
        
        # ABA 1: GESTÃO DA EQUIPE
        with aba_equipe:
            st.header("👥 Gestão de Usuários e Acessos")
            st.info("💡 **Dica de Gestão:** Use a coluna **Status** para definir quem está `Ativo`, `Férias` ou `Afastado`. Quem não estiver 'Ativo' sumirá dos cálculos gerais automaticamente para não quebrar suas médias!")
            try:
                df_users_atual = ler_csv_via_api_github("dados_usuarios.csv")
                
                # Se a coluna Status não existir no arquivo do Git, nós injetamos ela como 'Ativo' para prevenção
                if 'Status' not in df_users_atual.columns:
                    df_users_atual['Status'] = 'Ativo'
                    
                df_users_editado = st.data_editor(df_users_atual, num_rows="dynamic", use_container_width=True)
                
                if st.button("💾 Salvar Alterações da Equipe no GitHub", type="primary"):
                    with st.spinner("Salvando as alterações no GitHub..."):
                        csv_usr = df_users_editado.to_csv(index=False)
                        suc, msg = enviar_para_github("dados_usuarios.csv", csv_usr)
                        if suc:
                            st.success("Lista de usuários e status atualizados com sucesso!")
                            st.cache_data.clear()
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(msg)
            except Exception:
                st.warning("O arquivo base de usuários ainda não existe no seu repositório Git.")
                up_us_inicial = st.file_uploader("Upload inicial de Usuários (CSV)", type=["csv"])
                if up_us_inicial and st.button("Criar Base Inicial de Usuários"):
                    suc, msg = enviar_para_github("dados_usuarios.csv", up_us_inicial)
                    if suc:
                        st.success("Criado com sucesso!")
                        st.cache_data.clear()
                        time.sleep(0.5)
                        st.rerun()

        # ABA 2: ADMINISTRAÇÃO E CONSOLIDAÇÃO
        with aba_upload:
            st.header("⚙️ Atualizar Base Histórica (Master)")
            col_m, col_a = st.columns(2)
            mes_up = col_m.selectbox("Mês dos dados:", MESES, index=4)
            ano_up = col_a.selectbox("Ano dos dados:", ANOS)
            
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            with c1:
                up_ad = st.file_uploader("1. Aderência", type=["csv"])
                up_pq = st.file_uploader("2. Pesquisa (CSAT/IR)", type=["csv"])
            with c2:
                up_ch = st.file_uploader("3. Chat", type=["csv"])
                up_vz = st.file_uploader("4. Voz", type=["csv"])
            with c3:
                up_rt = st.file_uploader("5. Retenção (Use o Relatório Estratégico)", type=["csv"])
                
            st.markdown("---")
            
            if st.button("🚀 Processar e Atualizar Base Mestre", type="primary", use_container_width=True):
                if up_ad and up_pq and up_ch and up_vz and up_rt:
                    with st.spinner(f"Processando e consolidando os dados para {mes_up}/{ano_up}..."):
                        try:
                            df_perf = pd.read_csv(up_ad)
                            df_ret = pd.read_csv(up_rt)
                            df_chat = pd.read_csv(up_ch)
                            df_voz = pd.read_csv(up_vz)
                            df_pesq = pd.read_csv(up_pq)
                            df_users = ler_csv_via_api_github("dados_usuarios.csv")
                            
                            df_perf['Aderência (%)'] = df_perf['Aderência (%)'].apply(limpar_porcentagem)
                            df_perf['Conformidade (%)'] = df_perf['Conformidade (%)'].apply(limpar_porcentagem)
                            df_perf['Chave_Nome'] = df_perf['Agente'].astype(str).str.strip().str.upper()
                            df_users['Chave_Nome'] = df_users['Nome'].astype(str).str.strip().str.upper()
                            
                            df_ret['Chave_Nome'] = df_ret['responsavel'].astype(str).str.strip().str.upper()
                            df_ret['Taxa_Retencao_Original'] = df_ret['% de retenção'].apply(limpar_porcentagem)
                            df_ret['RT geral valido'] = pd.to_numeric(df_ret['RT geral valido'], errors='coerce').fillna(0)
                            
                            df_ret['RT geral calculado'] = df_ret.apply(
                                lambda row: (row['RT geral valido'] / (row['Taxa_Retencao_Original'] / 100)) if row['Taxa_Retencao_Original'] > 0 else row['RT geral valido'],
                                axis=1
                            ).fillna(0)
                            
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
                            df_pesq['CSAT_Num'] = pd.to_numeric(df_pesq['CSAT'], errors='coerce')
                            
                            df_pesq_agg = df_pesq.groupby('Chave_Nome').agg(
                                Total_Pesq_CSAT=('CSAT_Num', 'count'),
                                Boas_Pesq_CSAT=('CSAT_Num', lambda x: (x >= 4).sum()),
                                Total_Pesq_IR=('IR', 'count'),
                                Sim_Pesq_IR=('IR', lambda x: (x.astype(str).str.strip().str.upper() == 'SIM').sum())
                            ).reset_index()

                            df_novo = pd.merge(df_users, df_perf, on='Chave_Nome', how='left')
                            df_novo = pd.merge(df_novo, df_ret[['Chave_Nome', 'RT geral valido', 'RT geral calculated', 'Taxa_Retencao_Original']], on='Chave_Nome', how='left')
                            df_novo = pd.merge(df_novo, df_chat_agg, on='Chave_Nome', how='left')
                            df_novo = pd.merge(df_novo, df_voz_agg, on='Chave_Nome', how='left')
                            df_novo = pd.merge(df_novo, df_pesq_agg, on='Chave_Nome', how='left')
                            df_novo['Nome Exibição'] = df_novo['Chave_Nome'].str.title()
                            
                            df_novo['Mês'] = mes_up
                            df_novo['Ano'] = str(ano_up)
                            
                            try:
                                df_master = ler_csv_via_api_github("dados_consolidados_master.csv")
                                df_master['Ano'] = df_master['Ano'].astype(str)
                                df_master = df_master[~((df_master['Mês'].str.lower() == mes_up.lower()) & (df_master['Ano'] == str(ano_up)))]
                                df_final = pd.concat([df_master, df_novo], ignore_index=True)
                            except Exception:
                                df_final = df_novo
                            
                            csv_final = df_final.to_csv(index=False)
                            suc_mega, msg_mega = enviar_para_github("dados_consolidados_master.csv", csv_final)
                            
                            if suc_mega:
                                st.cache_data.clear()
                                st.success(f"Sucesso! Base Mestre consolidada para {mes_up}/{ano_up}!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.warning("Erro ao salvar no GitHub.")
                        except Exception as e:
                            st.error(f"Erro no processamento técnico: {e}")
                else:
                    st.error("⚠️ Por favor, adicione todos os 5 relatórios obrigatórios.")
                    
        # ABA 3: DASHBOARD GESTOR
        with aba_dashboard:
            if not base_mestre_existe:
                st.info("👋 **Bem-vindo ao Sistema!**")
                st.warning("📢 A base mestre ainda não foi integrada ou o ficheiro está inacessível.")
            elif not dados_carregados:
                st.warning(f"⚠️ {erro_dados}")
            else:
                st.title(f"📈 Dashboard Operacional ({mes_view}/{ano_view})")
                
                agentes = ["Todos"] + list(df_periodo['Nome Exibição'].dropna().unique())
                filtro_agente = st.selectbox("Filtrar visualização por Agente:", agentes)
                
                df_view = df_periodo[df_periodo['Nome Exibição'] == filtro_agente] if filtro_agente != "Todos" else df_periodo.copy()

                # --- 🚨 FILTRO FILTRAGEM INTELIGENTE DE STATUS (O PULO DO GATO) 🚨 ---
                # Criamos um dataframe exclusivo para os cards do topo que ignora 'Férias' e 'Afastado'
                if 'Status' in df_view.columns and filtro_agente == "Todos":
                    df_ativos_cards = df_view[df_view['Status'].fillna('Ativo').str.strip().str.title() == 'Ativo']
                    total_ativos = len(df_ativos_cards)
                    sub_status_text = f"Filtro: {total_ativos} ativos"
                else:
                    df_ativos_cards = df_view.copy()
                    sub_status_text = "Filtro Individual"

                tem_colunas_novas = 'Total_Pesq_CSAT' in df_ativos_cards.columns
                tem_coluna_ret_original = 'Taxa_Retencao_Original' in df_ativos_cards.columns
                
                # CSAT e IR calculados usando apenas a base de operadores Ativos
                if tem_colunas_novas:
                    pesquisas_csat_totais = df_ativos_cards['Total_Pesq_CSAT'].sum()
                    pesquisas_csat_boas = df_ativos_cards['Boas_Pesq_CSAT'].sum()
                    v_csat = (pesquisas_csat_boas / pesquisas_csat_totais * 100) if pesquisas_csat_totais > 0 else 0.0

                    pesquisas_ir_totais = df_ativos_cards['Total_Pesq_IR'].sum()
                    pesquisas_ir_sim = df_ativos_cards['Sim_Pesq_IR'].sum()
                    v_ir = (pesquisas_ir_sim / pesquisas_ir_totais * 100) if pesquisas_ir_totais > 0 else 0.0
                    sub_legenda_csat = f"Ativos: {int(pesquisas_csat_totais)} pesq."
                    sub_legenda_ir = f"Ativos: {int(pesquisas_ir_totais)} pesq."
                else:
                    v_csat = df_ativos_cards['CSAT_Media'].mean() if 'CSAT_Media' in df_ativos_cards.columns else 0.0
                    v_ir = df_ativos_cards['IR_Percentual'].mean() if 'IR_Percentual' in df_ativos_cards.columns else 0.0
                    sub_legenda_csat = "Re-upload pendente"
                    sub_legenda_ir = "Re-upload pendente"

                # Aderência e Conformidade aplicadas apenas para os ativos (0% por falta conta, mas 0% por férias some!)
                v_ade = df_ativos_cards['Aderência (%)'].mean() if not df_ativos_cards.empty else 0.0
                v_conf = df_ativos_cards['Conformidade (%)'].mean() if not df_ativos_cards.empty else 0.0
                
                # Retenção dos Ativos
                total_rt_valido = df_ativos_cards['RT geral valido'].sum() if 'RT geral valido' in df_ativos_cards.columns else 0
                if tem_coluna_ret_original:
                    if filtro_agente == "Todos":
                        col_total_nome = 'RT geral calculado' if 'RT geral calculado' in df_ativos_cards.columns else 'RT geral calculated'
                        total_calculado_equipe = df_ativos_cards[col_total_nome].sum()
                        v_retencao = (total_rt_valido / total_calculado_equipe * 100) if total_calculado_equipe > 0 else 0.0
                        sub_legenda_ret = f"Ativos: {int(total_rt_valido):,} retidos"
                    else:
                        v_retencao = df_ativos_cards['Taxa_Retencao_Original'].iloc[0]
                        sub_legenda_ret = f"Total Individual: {int(total_rt_valido)} retidos"
                else:
                    v_retencao = 0.0
                    sub_legenda_ret = "⚠️ Atualize as planilhas"
                
                v_cancelamento = 100 - v_retencao if v_retencao > 0 else 0.0

                total_vol_chat = df_ativos_cards['Vol. Chat'].sum()
                tma_chat_medio = df_ativos_cards['TMA Chat (Min)'].mean()
                total_vol_voz = df_ativos_cards['Vol. Voz'].sum()
                tma_voz_medio = df_ativos_cards['TMA Voz (Min)'].mean()

                # === FILEIRA 1 DE CARDS ===
                st.subheader("🎯 Principais KPIs de Qualidade (Apenas Equipe Ativa)")
                c1, c2, c3, c4, c5 = st.columns(5)
                
                with c1:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>⭐ CSAT Ponderado</div><div class='kpi-value'>{v_csat:.1f}%</div><div style='font-size:11px;color:#6c757d;'>{sub_legenda_csat}</div></div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🎯 Índice IR</div><div class='kpi-value'>{v_ir:.1f}%</div><div style='font-size:11px;color:#6c757d;'>{sub_legenda_ir}</div></div>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>📈 Taxa Retenção</div><div class='kpi-value'>{v_retencao:.2f}%</div><div style='font-size:11px;color:#6c757d;'>{sub_legenda_ret}</div></div>", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #dc3545;'><div class='kpi-title'>📉 Taxa Cancelamento</div><div class='kpi-value'>{v_cancelamento:.2f}%</div><div style='font-size:11px;color:#dc3545;'>Complemento Real</div></div>", unsafe_allow_html=True)
                with c5:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ba55d3;'><div class='kpi-title'>⏱️ Aderência Geral</div><div class='kpi-value'>{v_ade:.1f}%</div><div style='font-size:11px;color:#6c757d;'>{sub_status_text}</div></div>", unsafe_allow_html=True)

                # === FILEIRA 2 DE CARDS ===
                st.subheader("📊 Volumetria e Tempo de Atendimento (TMA)")
                cx1, cx2, cx3, cx4 = st.columns(4)
                
                with cx1:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>💬 Vol. Total Chat</div><div class='kpi-value'>{int(total_vol_chat):,}</div></div>", unsafe_allow_html=True)
                with cx2:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>⏳ TMA Médio Chat</div><div class='kpi-value'>{tma_chat_medio:.1f} min</div></div>", unsafe_allow_html=True)
                with cx3:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>📞 Vol. Total Voz</div><div class='kpi-value'>{int(total_vol_voz):,}</div></div>", unsafe_allow_html=True)
                with cx4:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>⏳ TMA Médio Voz</div><div class='kpi-value'>{tma_voz_medio:.1f} min</div></div>", unsafe_allow_html=True)

                st.markdown("---")
                
                # Visão detalhada (Tabela mantém todo mundo para você ver o histórico completo)
                st.subheader("👥 Visão Detalhada por Agente (Histórico Nominal)")
                df_tabela = df_view.copy()
                
                if tem_colunas_novas:
                    df_tabela['CSAT_Agente (%)'] = (df_tabela['Boas_Pesq_CSAT'] / df_tabela['Total_Pesq_CSAT'] * 100).fillna(0)
                    df_tabela['IR_Agente (%)'] = (df_tabela['Sim_Pesq_IR'] / df_tabela['Total_Pesq_IR'] * 100).fillna(0)
                else:
                    df_tabela['CSAT_Agente (%)'] = df_tabela['CSAT_Media'].fillna(0)
                    df_tabela['IR_Agente (%)'] = df_tabela['IR_Percentual'].fillna(0)
                    
                df_tabela['% Retenção'] = df_tabela['Taxa_Retencao_Original'].fillna(0) if tem_coluna_ret_original else 0.0
                df_tabela['% Cancelamento'] = df_tabela.apply(lambda row: 100 - row['% Retenção'] if row['% Retenção'] > 0 else 0.0, axis=1)
                
                # Adiciona a coluna de Status visível na tabela de baixo
                colunas_tabela = ['Nome Exibição', 'Status' if 'Status' in df_tabela.columns else 'Nome Exibição', 'CSAT_Agente (%)', 'IR_Agente (%)', 'Aderência (%)', 'Conformidade (%)', 'Vol. Chat', 'TMA Chat (Min)', 'Vol. Voz', 'TMA Voz (Min)', 'RT geral valido', '% Retenção', '% Cancelamento']
                # Remoção de duplicações na chamada de colunas
                colunas_tabela = list(dict.fromkeys(colunas_tabela))
                
                st.dataframe(df_tabela[colunas_tabela].style.format({
                    'CSAT_Agente (%)': '{:.1f}%', 
                    'IR_Agente (%)': '{:.1f}%', 
                    'Aderência (%)': '{:.1f}%', 
                    'Conformidade (%)': '{:.1f}%', 
                    '% Retenção': '{:.2f}%', 
                    '% Cancelamento': '{:.2f}%', 
                    'Vol. Chat': '{:,.0f}',
                    'TMA Chat (Min)': '{:.1f}m', 
                    'Vol. Voz': '{:,.0f}',
                    'TMA Voz (Min)': '{:.1f}m',
                    'RT geral valido': '{:,.0f}'
                }), use_container_width=True)

    # ==========================================
    # VISÃO DO AGENTE
    # ==========================================
    elif st.session_state.perfil == "Agente":
        if not base_mestre_existe:
            st.error("⚠️ O sistema está sendo configurado. Tente mais tarde.")
        elif not dados_carregados:
            st.warning(f"⚠️ {erro_dados}")
        else:
            st.title(f"👤 Meu Painel ({mes_view}/{ano_view})")
            meus_dados = df_periodo[df_periodo['E-mail'] == st.session_state.user_email]
            
            if not meus_dados.empty:
                dados = meus_dados.iloc[0]
                
                tem_colunas_novas = 'Total_Pesq_CSAT' in df_periodo.columns
                tem_coluna_ret_original = 'Taxa_Retencao_Original' in df_periodo.columns
                
                if tem_colunas_novas:
                    my_csat = (dados['Boas_Pesq_CSAT'] / dados['Total_Pesq_CSAT'] * 100) if dados['Total_Pesq_CSAT'] > 0 else 0.0
                    my_ir = (dados['Sim_Pesq_IR'] / dados['Total_Pesq_IR'] * 100) if dados['Total_Pesq_IR'] > 0 else 0.0
                    sub_ag_csat = f"{int(dados['Total_Pesq_CSAT'])} avaliações"
                    sub_ag_ir = f"{int(dados['Total_Pesq_IR'])} pesquisas"
                else:
                    my_csat = dados['CSAT_Media'] if 'CSAT_Media' in df_periodo.columns else 0.0
                    my_ir = dados['IR_Percentual'] if 'IR_Percentual' in df_periodo.columns else 0.0
                    sub_ag_csat = "Pendente"
                    sub_ag_ir = "Pendente"
                    
                my_tx_ret = dados['Taxa_Retencao_Original'] if tem_coluna_ret_original else 0.0
                my_tx_canc = 100 - my_tx_ret if my_tx_ret > 0 else 0.0
                
                st.markdown("### ⭐ Minha Performance")
                ca1, ca2, ca3, ca4 = st.columns(4)
                with ca1:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Meu CSAT</div><div class='kpi-value'>{my_csat:.1f}%</div><div style='font-size:11px;color:#6c757d;'>{sub_ag_csat}</div></div>", unsafe_allow_html=True)
                with ca2:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Meu IR</div><div class='kpi-value'>{my_ir:.1f}%</div><div style='font-size:11px;color:#6c757d;'>{sub_ag_ir}</div></div>", unsafe_allow_html=True)
                with ca3:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Minha Aderência</div><div class='kpi-value'>{dados['Aderência (%)']:.1f}%</div></div>", unsafe_allow_html=True)
                with ca4:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Minha Conformidade</div><div class='kpi-value'>{dados['Conformidade (%)']:.1f}%</div></div>", unsafe_allow_html=True)

                st.markdown("### 🎧 Meus Volumes e Atendimento")
                co1, co2, co3, co4 = st.columns(4)
                with co1:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Chats Atendidos</div><div class='kpi-value'>{int(dados['Vol. Chat']) if pd.notna(dados['Vol. Chat']) else 0}</div></div>", unsafe_allow_html=True)
                with co2:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Meu TMA Chat</div><div class='kpi-value'>{dados['TMA Chat (Min)']:.1f} m</div></div>", unsafe_allow_html=True)
                with co3:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Chamadas Voz</div><div class='kpi-value'>{int(dados['Vol. Voz']) if pd.notna(dados['Vol. Voz']) else 0}</div></div>", unsafe_allow_html=True)
                with co4:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Taxa de Retenção</div><div class='kpi-value'>{my_tx_ret:.2f}%</div><div style='font-size:11px;color:#6c757d;'>Retidos: {int(dados['RT geral valido'])} | Cancelados: {my_tx_canc:.1f}%</div></div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum dado operacional associado ao seu perfil.")
