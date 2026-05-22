import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github
import io
import time

# ==========================================
# CONFIGURAÇÕES GERAIS E PARÂMETROS DE METAS
# ==========================================
st.set_page_config(page_title="Sistema Operacional 360", page_icon="🎯", layout="wide")

GESTOR_EMAIL = "gestor"
GESTOR_SENHA = "admin"
SENHA_PADRAO_AGENTE = "1234" 

# METAS OFICIAIS DA OPERAÇÃO BRISANET
META_CSAT = 92.0
META_IR = 88.0
META_RETENCAO = 65.0
META_ADERENCIA = 92.0
META_CONFORMIDADE = 92.0

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
        .detractor-box {
            background-color: #fff5f5;
            border: 1px solid #feb2b2;
            padding: 12px;
            border-radius: 6px;
            color: #c53030;
            margin-bottom: 8px;
            font-size: 13px;
            line-height: 1.4;
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
        
        # ABA GESTÃO DA EQUIPE
        with aba_equipe:
            st.header("👥 Gestão de Usuários e Acessos")
            try:
                df_users_atual = ler_csv_via_api_github("dados_usuarios.csv")
                if 'Status' not in df_users_atual.columns:
                    df_users_atual['Status'] = 'Ativo'
                    
                df_users_editado = st.data_editor(df_users_atual, num_rows="dynamic", use_container_width=True)
                
                if st.button("💾 Salvar Alterações da Equipe no GitHub", type="primary"):
                    with st.spinner("Salvando as alterações no GitHub..."):
                        csv_usr = df_users_editado.to_csv(index=False)
                        enviar_para_github("dados_usuarios.csv", csv_usr)
                        st.cache_data.clear()
                        st.success("Status salvos com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
            except Exception:
                st.warning("O arquivo base de usuários ainda não existe.")

        # ABA UPLOAD
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
                    with st.spinner(f"Processando e consolidando..."):
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
                            
                            csv_final = df_novo.to_csv(index=False)
                            enviar_para_github("dados_consolidados_master.csv", csv_final)
                            st.cache_data.clear()
                            st.success("Base Mestre atualizada!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")

        # ABA DASHBOARD
        with aba_dashboard:
            if not base_mestre_existe:
                st.warning("📢 Base mestre indisponível.")
            elif not dados_carregados:
                st.warning(f"⚠️ {erro_dados}")
            else:
                st.title(f"📊 Painel Analítico de Controle Operacional ({mes_view}/{ano_view})")
                
                modo_visao = st.radio("Filtro de Status de Equipe:", ["Mostrar Apenas Ativos", "Mostrar Todos (Incluir Férias/Afastados)"], horizontal=True)
                
                if 'Status' in df_periodo.columns and modo_visao == "Mostrar Apenas Ativos":
                    df_filtrado_status = df_periodo[df_periodo['Status'].fillna('Ativo').str.strip().str.title() == 'Ativo']
                else:
                    df_filtrado_status = df_periodo.copy()

                df_calculado = df_filtrado_status.copy()
                if 'Total_Pesq_CSAT' in df_calculado.columns:
                    df_calculado['CSAT_Agente (%)'] = (df_calculado['Boas_Pesq_CSAT'] / df_calculado['Total_Pesq_CSAT'] * 100).fillna(0)
                    df_calculado['IR_Agente (%)'] = (df_calculado['Sim_Pesq_IR'] / df_calculado['Total_Pesq_IR'] * 100).fillna(0)
                else:
                    df_calculado['CSAT_Agente (%)'] = df_calculado['CSAT_Media'].fillna(0)
                    df_calculado['IR_Agente (%)'] = df_calculado['IR_Percentual'].fillna(0)
                
                df_calculado['% Retenção'] = df_calculado['Taxa_Retencao_Original'].fillna(0) if 'Taxa_Retencao_Original' in df_calculado.columns else 0.0
                df_calculado['% Cancelamento'] = df_calculado.apply(lambda r: 100 - r['% Retenção'] if r['% Retenção'] > 0 else 0.0, axis=1)

                # ==========================================
                # 🚨 CORREÇÃO CIRÚRGICA DOS ALERTAS (SEPARADOS POR INDICADOR)
                # ==========================================
                st.subheader("🚨 Auditoria de Desvios de Metas (Quadro Ativo)")
                df_ativos_alertas = df_calculado[df_calculado['Status'].fillna('Ativo').str.strip().str.title() == 'Ativo'] if 'Status' in df_calculado.columns else df_calculado.copy()
                
                # Listas isoladas para não misturar aprovações e reprovações
                lista_detratores_csat = df_ativos_alertas[df_ativos_alertas['CSAT_Agente (%)'] < META_CSAT]
                lista_detratores_ir = df_ativos_alertas[df_ativos_alertas['IR_Agente (%)'] < META_IR]
                detratores_retencao = df_ativos_alertas[df_ativos_alertas['% Retenção'] < META_RETENCAO]
                lista_detratores_ade = df_ativos_alertas[df_ativos_alertas['Aderência (%)'] < META_ADERENCIA]
                lista_detratores_conf = df_ativos_alertas[df_ativos_alertas['Conformidade (%)'] < META_CONFORMIDADE]
                
                total_desvios_qualidade = len(lista_detratores_csat) + len(lista_detratores_ir)
                total_desvios_processo = len(lista_detratores_ade) + len(lista_detratores_conf)

                col_alerta_1, col_alerta_2, col_alerta_3 = st.columns(3)
                
                with col_alerta_1:
                    label_q = f"🔻 Qualidade: {total_desvios_qualidade} desvios encontrados" if total_desvios_qualidade > 0 else "✅ Qualidade: 100% na meta"
                    with st.expander(label_q, expanded=False):
                        if total_desvios_qualidade == 0:
                            st.write("Toda a equipe ativa cumpre as metas de CSAT e IR.")
                        else:
                            # Mostra estritamente quem está abaixo da meta do indicador individual
                            for _, row in lista_detratores_csat.iterrows():
                                st.markdown(f"<div class='detractor-box'>⭐ <b>{row['Nome Exibição']}</b> | CSAT abaixo da meta: <b>{row['CSAT_Agente (%)']:.1f}%</b> (Meta: {META_CSAT}%)</div>", unsafe_allow_html=True)
                            for _, row in lista_detratores_ir.iterrows():
                                st.markdown(f"<div class='detractor-box'>🎯 <b>{row['Nome Exibição']}</b> | Índice IR abaixo da meta: <b>{row['IR_Agente (%)']:.1f}%</b> (Meta: {META_IR}%)</div>", unsafe_allow_html=True)

                with col_alerta_2:
                    label_r = f"📉 Retenção: {len(detratores_retencao)} abaixo da meta" if not detratores_retencao.empty else "✅ Retenção: 100% na meta"
                    with st.expander(label_r, expanded=False):
                        if detratores_retencao.empty:
                            st.write("Toda a equipe ativa está cumprindo a meta de Retenção.")
                        else:
                            for _, row in detratores_retencao.iterrows():
                                st.markdown(f"<div class='detractor-box' style='background-color:#fffaf0;border-color:#fbd38d;color:#dd6b20;'>📉 <b>{row['Nome Exibição']}</b> | Retenção: <b>{row['% Retenção']:.2f}%</b> (Meta: {META_RETENCAO}%)</div>", unsafe_allow_html=True)

                with col_alerta_3:
                    label_p = f"⏱️ Processos: {total_desvios_processo} desvios encontrados" if total_desvios_processo > 0 else "✅ Processos: 100% na meta"
                    with st.expander(label_p, expanded=False):
                        if total_desvios_processo == 0:
                            st.write("Toda a equipe ativa cumpre os prazos de Aderência e Conformidade.")
                        else:
                            for _, row in lista_detratores_ade.iterrows():
                                st.markdown(f"<div class='detractor-box' style='background-color:#fffaf5;border-color:#feb2b2;color:#c53030;'>⏱️ <b>{row['Nome Exibição']}</b> | Aderência abaixo da meta: <b>{row['Aderência (%)']:.1f}%</b> (Meta: {META_ADERENCIA}%)</div>", unsafe_allow_html=True)
                            for _, row in lista_detratores_conf.iterrows():
                                st.markdown(f"<div class='detractor-box' style='background-color:#fffaf5;border-color:#feb2b2;color:#c53030;'>🛡️ <b>{row['Nome Exibição']}</b> | Conformidade abaixo da meta: <b>{row['Conformidade (%)']:.1f}%</b> (Meta: {META_CONFORMIDADE}%)</div>", unsafe_allow_html=True)

                st.markdown("---")

                # FILTROS DE FOCO INDIVIDUAL
                agentes_lista = ["Todos"] + list(df_calculado['Nome Exibição'].dropna().unique())
                filtro_agente = st.selectbox("Mudar foco do Dashboard para um Operador:", agentes_lista)
                df_view = df_calculado[df_calculado['Nome Exibição'] == filtro_agente] if filtro_agente != "Todos" else df_calculado.copy()

                # --- CARDS GERAIS ---
                if 'Total_Pesq_CSAT' in df_view.columns:
                    tot_csat = df_view['Total_Pesq_CSAT'].sum()
                    boas_csat = df_view['Boas_Pesq_CSAT'].sum()
                    v_csat = (boas_csat / tot_csat * 100) if tot_csat > 0 else 0.0
                    tot_ir = df_view['Total_Pesq_IR'].sum()
                    sim_ir = df_view['Sim_Pesq_IR'].sum()
                    v_ir = (sim_ir / tot_ir * 100) if tot_ir > 0 else 0.0
                    sub_csat = f"Base: {int(tot_csat)} pesq."
                    sub_ir = f"Base: {int(tot_ir)} pesq."
                else:
                    v_csat = df_view['CSAT_Media'].mean()
                    v_ir = df_view['IR_Percentual'].mean()
                    sub_csat = "Amostra Antiga"
                    sub_ir = "Amostra Antiga"

                v_ade = df_view['Aderência (%)'].mean()
                v_conf = df_view['Conformidade (%)'].mean()
                
                total_rt_valido = df_view['RT geral valido'].sum()
                if 'Taxa_Retencao_Original' in df_view.columns:
                    if filtro_agente == "Todos":
                        col_total_nome = 'RT geral calculated' if 'RT geral calculated' in df_view.columns else 'RT geral calculado'
                        total_calculado_equipe = df_view[col_total_nome].sum()
                        v_retencao = (total_rt_valido / total_calculado_equipe * 100) if total_calculado_equipe > 0 else 0.0
                    else:
                        v_retencao = df_view['Taxa_Retencao_Original'].iloc[0]
                    sub_ret = f"Válidas: {int(total_rt_valido)} retidos"
                else:
                    v_retencao = 0.0
                    sub_ret = "Sem histórico"

                v_cancelamento = 100 - v_retencao if v_retencao > 0 else 0.0
                total_vol_chat = df_view['Vol. Chat'].sum()
                tma_chat_medio = df_view['TMA Chat (Min)'].mean()
                total_vol_voz = df_view['Vol. Voz'].sum()
                tma_voz_medio = df_view['TMA Voz (Min)'].mean()

                # CARDS
                st.subheader(f"🎯 Métricas Consolidadas ({filtro_agente})")
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>⭐ CSAT Ponderado</div><div class='kpi-value'>{v_csat:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_CSAT:.0f}%</div></div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🎯 Índice IR</div><div class='kpi-value'>{v_ir:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_IR:.0f}%</div></div>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>📈 Taxa Retenção</div><div class='kpi-value'>{v_retencao:.2f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_RETENCAO:.0f}%</div></div>", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #dc3545;'><div class='kpi-title'>📉 Taxa Cancelamento</div><div class='kpi-value'>{v_cancelamento:.2f}%</div><div style='font-size:11px;color:#dc3545;'>Complementar</div></div>", unsafe_allow_html=True)
                with c5:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #9932cc;'><div class='kpi-title'>🛡️ Conformidade</div><div class='kpi-value'>{v_conf:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_CONFORMIDADE:.0f}%</div></div>", unsafe_allow_html=True)

                cx0, cx1, cx2, cx3, cx4 = st.columns(5)
                with cx0:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ba55d3;'><div class='kpi-title'>⏱️ Aderência Geral</div><div class='kpi-value'>{v_ade:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_ADERENCIA:.0f}%</div></div>", unsafe_allow_html=True)
                with cx1:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>💬 Vol. Total Chat</div><div class='kpi-value'>{int(total_vol_chat):,}</div></div>", unsafe_allow_html=True)
                with cx2:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>⏳ TMA Chat</div><div class='kpi-value'>{tma_chat_medio:.1f} min</div></div>", unsafe_allow_html=True)
                with cx3:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>📞 Vol. Total Voz</div><div class='kpi-value'>{int(total_vol_voz):,}</div></div>", unsafe_allow_html=True)
                with cx4:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>⏳ TMA Voz</div><div class='kpi-value'>{tma_voz_medio:.1f} min</div></div>", unsafe_allow_html=True)

                st.markdown("---")

                # AUDITORIA GRÁFICA DINÂMICA
                if filtro_agente == "Todos":
                    st.subheader("📊 Motor de Auditoria Gráfica - Foco nos Detratores e Gargalos")
                    indicador_grafico = st.selectbox("Selecione o Indicador para Analisar o Ranking de Oportunidades:", 
                                                    ["CSAT", "Índice IR", "Taxa de Retenção", "Aderência", "Conformidade", "TMA Chat", "TMA Voz"])
                    
                    df_chart_base = df_view.dropna(subset=['Nome Exibição'])
                    
                    if indicador_grafico == "CSAT":
                        df_chart = df_chart_base.sort_values(by='CSAT_Agente (%)', ascending=True).head(12)
                        fig = px.bar(df_chart, x='CSAT_Agente (%)', y='Nome Exibição', orientation='h',
                                     title=f"⭐ Ranking Crescente CSAT (Meta Contratual: {META_CSAT:.0f}%)",
                                     labels={'CSAT_Agente (%)': 'CSAT (%)', 'Nome Exibição': 'Operador'},
                                     color='CSAT_Agente (%)', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_CSAT, line_dash="dash", line_color="green", annotation_text=f"Meta {META_CSAT:.0f}%", annotation_position="top right")
                    
                    elif indicador_grafico == "Índice IR":
                        df_chart = df_chart_base.sort_values(by='IR_Agente (%)', ascending=True).head(12)
                        fig = px.bar(df_chart, x='IR_Agente (%)', y='Nome Exibição', orientation='h',
                                     title=f"🎯 Ranking Crescente IR (Meta Contratual: {META_IR:.0f}%)",
                                     labels={'IR_Agente (%)': 'Índice IR (%)', 'Nome Exibição': 'Operador'},
                                     color='IR_Agente (%)', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_IR, line_dash="dash", line_color="green", annotation_text=f"Meta {META_IR:.0f}%", annotation_position="top right")
                    
                    elif indicador_grafico == "Taxa de Retenção":
                        df_chart = df_chart_base.sort_values(by='% Retenção', ascending=True).head(12)
                        fig = px.bar(df_chart, x='% Retenção', y='Nome Exibição', orientation='h',
                                     title=f"📈 Ranking Crescente de Retenção (Meta Contratual: {META_RETENCAO:.0f}%)",
                                     labels={'% Retenção': 'Taxa de Retenção (%)', 'Nome Exibição': 'Operador'},
                                     color='% Retenção', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_RETENCAO, line_dash="dash", line_color="green", annotation_text=f"Meta {META_RETENCAO:.0f}%", annotation_position="top right")
                    
                    elif indicador_grafico == "Aderência":
                        df_chart = df_chart_base.sort_values(by='Aderência (%)', ascending=True).head(12)
                        fig = px.bar(df_chart, x='Aderência (%)', y='Nome Exibição', orientation='h',
                                     title=f"⏱️ Ranking Crescente de Aderência (Meta Contratual: {META_ADERENCIA:.0f}%)",
                                     labels={'Aderência (%)': 'Aderência (%)', 'Nome Exibição': 'Operador'},
                                     color='Aderência (%)', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_ADERENCIA, line_dash="dash", line_color="green", annotation_text=f"Meta {META_ADERENCIA:.0f}%", annotation_position="top right")
                    
                    elif indicador_grafico == "Conformidade":
                        df_chart = df_chart_base.sort_values(by='Conformidade (%)', ascending=True).head(12)
                        fig = px.bar(df_chart, x='Conformidade (%)', y='Nome Exibição', orientation='h',
                                     title=f"🛡️ Ranking Crescente de Conformidade (Meta Contratual: {META_CONFORMIDADE:.0f}%)",
                                     labels={'Conformidade (%)': 'Conformidade (%)', 'Nome Exibição': 'Operador'},
                                     color='Conformidade (%)', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_CONFORMIDADE, line_dash="dash", line_color="green", annotation_text=f"Meta {META_CONFORMIDADE:.0f}%", annotation_position="top right")
                    
                    elif indicador_grafico == "TMA Chat":
                        df_chart = df_chart_base.sort_values(by='TMA Chat (Min)', ascending=False).head(12)
                        fig = px.bar(df_chart, x='TMA Chat (Min)', y='Nome Exibição', orientation='h',
                                     title="⏳ Maiores TMAs Chat - Gargalos de Tempo",
                                     labels={'TMA Chat (Min)': 'Minutos', 'Nome Exibição': 'Operador'},
                                     color='TMA Chat (Min)', color_continuous_scale='Oranges')
                    
                    elif indicador_grafico == "TMA Voz":
                        df_chart = df_chart_base.sort_values(by='TMA Voz (Min)', ascending=False).head(12)
                        fig = px.bar(df_chart, x='TMA Voz (Min)', y='Nome Exibição', orientation='h',
                                     title="⏳ Maiores TMAs Voz - Gargalos de Tempo",
                                     labels={'TMA Voz (Min)': 'Minutos', 'Nome Exibição': 'Operador'},
                                     color='TMA Voz (Min)', color_continuous_scale='Oranges')
                    
                    fig.update_layout(yaxis={'categoryorder': 'total ascending' if indicador_grafico not in ["TMA Chat", "TMA Voz"] else 'total descending'}, coloraxis_showscale=False)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown("---")

                # TABELA NOMINAL
                st.subheader("👥 Detalhamento Operacional por Colaborador")
                colunas_tabela = ['Nome Exibição', 'Status' if 'Status' in df_view.columns else 'Nome Exibição', 'CSAT_Agente (%)', 'IR_Agente (%)', 'Aderência (%)', 'Conformidade (%)', 'Vol. Chat', 'TMA Chat (Min)', 'Vol. Voz', 'TMA Voz (Min)', 'RT geral valido', '% Retenção', '% Cancelamento']
                colunas_tabela = list(dict.fromkeys(colunas_tabela))
                
                def estilizar_linhas_status(row):
                    status_val = str(row['Status']).strip().lower() if 'Status' in row else 'ativo'
                    if status_val != 'ativo':
                        return ['background-color: #f1f3f5; color: #adb5bd; font-style: italic;'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    df_view[colunas_tabela].style.apply(estilizar_linhas_status, axis=1).format({
                        'CSAT_Agente (%)': '{:.1f}%', 'IR_Agente (%)': '{:.1f}%', 'Aderência (%)': '{:.1f}%',
                        'Conformidade (%)': '{:.1f}%', '% Retenção': '{:.2f}%', '% Cancelamento': '{:.2f}%',
                        'Vol. Chat': '{:,.0f}', 'TMA Chat (Min)': '{:.1f}m', 'Vol. Voz': '{:,.0f}',
                        'TMA Voz (Min)': '{:.1f}m', 'RT geral valido': '{:,.0f}'
                    }), use_container_width=True
                )

    # ==========================================
    # VISÃO DO AGENTE
    # ==========================================
    elif st.session_state.perfil == "Agente":
        if not base_mestre_existe:
            st.error("⚠️ O sistema está sendo configurado pelo Gestor.")
        elif not dados_carregados:
            st.warning(f"⚠️ {erro_dados}")
        else:
            st.title(f"👤 Meu Painel de Metas ({mes_view}/{ano_view})")
            meus_dados = df_periodo[df_periodo['E-mail'] == st.session_state.user_email]
            
            if not meus_dados.empty:
                dados = meus_dados.iloc[0]
                tem_colunas_novas = 'Total_Pesq_CSAT' in df_periodo.columns
                tem_coluna_ret_original = 'Taxa_Retencao_Original' in df_periodo.columns
                
                my_csat = (dados['Boas_Pesq_CSAT'] / dados['Total_Pesq_CSAT'] * 100) if tem_colunas_novas and dados['Total_Pesq_CSAT'] > 0 else 0.0
                my_ir = (dados['Sim_Pesq_IR'] / dados['Total_Pesq_IR'] * 100) if tem_colunas_novas and dados['Total_Pesq_IR'] > 0 else 0.0
                my_tx_ret = dados['Taxa_Retencao_Original'] if tem_coluna_ret_original else 0.0
                my_tx_canc = 100 - my_tx_ret if my_tx_ret > 0 else 0.0
                
                st.markdown("### ⭐ Minha Performance vs Metas Contratuais")
                ca1, ca2, ca3, ca4 = st.columns(4)
                with ca1:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Meu CSAT</div><div class='kpi-value'>{my_csat:.1f}%</div><div style='font-size:11px;color:#6c757d;'>Meta: {META_CSAT:.0f}%</div></div>", unsafe_allow_html=True)
                with ca2:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Meu IR</div><div class='kpi-value'>{my_ir:.1f}%</div><div style='font-size:11px;color:#6c757d;'>Meta: {META_IR:.0f}%</div></div>", unsafe_allow_html=True)
                with ca3:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Minha Aderência</div><div class='kpi-value'>{dados['Aderência (%)']:.1f}%</div><div style='font-size:11px;color:#6c757d;'>Meta: {META_ADERENCIA:.0f}%</div></div>", unsafe_allow_html=True)
                with ca4:
                    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Minha Conformidade</div><div class='kpi-value'>{dados['Conformidade (%)']:.1f}%</div><div style='font-size:11px;color:#6c757d;'>Meta: {META_CONFORMIDADE:.0f}%</div></div>", unsafe_allow_html=True)

                st.markdown("### 🎧 Meus Volumes e Atendimento")
                co1, co2, co3, co4 = st.columns(4)
                with co1:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Chats Atendidos</div><div class='kpi-value'>{int(dados['Vol. Chat']) if pd.notna(dados['Vol. Chat']) else 0}</div></div>", unsafe_allow_html=True)
                with co2:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Meu TMA Chat</div><div class='kpi-value'>{dados['TMA Chat (Min)']:.1f} m</div></div>", unsafe_allow_html=True)
                with co3:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Chamadas Voz</div><div class='kpi-value'>{int(dados['Vol. Voz']) if pd.notna(dados['Vol. Voz']) else 0}</div></div>", unsafe_allow_html=True)
                with co4:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Taxa de Retenção</div><div class='kpi-value'>{my_tx_ret:.2f}%</div><div style='font-size:11px;color:#6c757d;'>Meta: {META_RETENCAO:.0f}% | Cancelamento: {my_tx_canc:.1f}%</div></div>", unsafe_allow_html=True)
