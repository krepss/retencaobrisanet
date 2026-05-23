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
        .validation-badge {
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 5px;
            display: inline-block;
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
                    st.warning("⚠️ Base de dados de utilizadores temporariamente indisponível.")

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
                st.warning("O arquivo mestre de usuários não foi localizado.")

        # ==========================================
        # ⚙️ NOVA ABA DE UPLOAD MULTIPLO COM CHECKLIST DE VALIDAÇÃO
        # ==========================================
        with aba_upload:
            st.header("⚙️ Central de Consolidação de Relatórios")
            st.markdown("Selecione os **5 arquivos CSV obrigatórios de uma só vez** na caixa abaixo. O sistema fará a auditoria automática dos cabeçalhos.")
            
            col_m, col_a = st.columns(2)
            mes_up = col_m.selectbox("Mês de competência das planilhas:", MESES, index=4)
            ano_up = col_a.selectbox("Ano de competência das planilhas:", ANOS)
            
            st.markdown("---")
            
            # CAIXA DE UPLOAD MÚLTIPLO UNIFICADA
            arquivos_carregados = st.file_uploader("Arraste e solte os 5 arquivos CSV aqui de uma vez", type=["csv"], accept_multiple_files=True)
            
            # Dicionários de mapeamento e controle para a validação
            relatorios_identificados = {
                "Aderência": None,
                "Pesquisa (CSAT/IR)": None,
                "Chat": None,
                "Voz": None,
                "Retenção": None
            }
            
            # Varre os arquivos anexados para validar os cabeçalhos em tempo real
            if arquivos_carregados:
                for arquivo in arquivos_carregados:
                    try:
                        # Lê apenas a primeira linha (cabeçalho) de forma ultrarrápida para validação
                        df_header = pd.read_csv(arquivo, nrows=0)
                        cols = [c.strip() for c in df_header.columns]
                        
                        # Reseta o ponteiro de leitura do arquivo para ele poder ser relido depois no processamento
                        arquivo.seek(0)
                        
                        if 'Aderência (%)' in cols and 'Agente' in cols:
                            relatorios_identificados["Aderência"] = arquivo
                        elif 'CSAT' in cols and 'Atendente' in cols:
                            relatorios_identificados["Pesquisa (CSAT/IR)"] = arquivo
                        elif 'Nome do agente' in cols and 'Atendidas' in cols and 'Tratamento médio' in cols:
                            # Desempata Chat e Voz analisando colunas extras
                            if 'Espera média' in cols:
                                # Se contiver ambas, pode ser qualquer um, validamos pelo nome do arquivo ou tratamos similarmente
                                # Mas para garantir a distinção justa do seu fluxo:
                                if "chat" in arquivo.name.lower():
                                    relatorios_identificados["Chat"] = arquivo
                                else:
                                    relatorios_identificados["Voz"] = arquivo
                            else:
                                relatorios_identificados["Voz"] = arquivo
                        elif 'responsavel' in cols and '% de retenção' in cols:
                            relatorios_identificados["Retenção"] = arquivo
                    except Exception:
                        pass

            # EXIBIÇÃO DO CHECKLIST VISUAL DE AUDITORIA
            st.markdown("### 📋 Status da Validação dos Arquivos")
            
            c_chk1, c_chk2, c_chk3, c_chk4, c_chk5 = st.columns(5)
            with c_chk1:
                if relatorios_identificados["Aderência"]:
                    st.markdown("<div style='background-color:#e6fffa;border:1px solid #319795;color:#234e52;padding:10px;border-radius:5px;text-align:center;'><b>🟢 1. Aderência</b><br><small>Pronto</small></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='background-color:#fff5f5;border:1px solid #e53e3e;color:#742a2a;padding:10px;border-radius:5px;text-align:center;'><b>🔴 1. Aderência</b><br><small>Aguardando...</small></div>", unsafe_allow_html=True)
                    
            with c_chk2:
                if relatorios_identificados["Pesquisa (CSAT/IR)"]:
                    st.markdown("<div style='background-color:#e6fffa;border:1px solid #319795;color:#234e52;padding:10px;border-radius:5px;text-align:center;'><b>🟢 2. Pesquisas</b><br><small>Pronto</small></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='background-color:#fff5f5;border:1px solid #e53e3e;color:#742a2a;padding:10px;border-radius:5px;text-align:center;'><b>🔴 2. Pesquisas</b><br><small>Aguardando...</small></div>", unsafe_allow_html=True)
                    
            with c_chk3:
                if relatorios_identificados["Chat"]:
                    st.markdown("<div style='background-color:#e6fffa;border:1px solid #319795;color:#234e52;padding:10px;border-radius:5px;text-align:center;'><b>🟢 3. Chat</b><br><small>Pronto</small></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='background-color:#fff5f5;border:1px solid #e53e3e;color:#742a2a;padding:10px;border-radius:5px;text-align:center;'><b>🔴 3. Chat</b><br><small>Aguardando...</small></div>", unsafe_allow_html=True)
                    
            with c_chk4:
                if relatorios_identificados["Voz"]:
                    st.markdown("<div style='background-color:#e6fffa;border:1px solid #319795;color:#234e52;padding:10px;border-radius:5px;text-align:center;'><b>🟢 4. Voz</b><br><small>Pronto</small></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='background-color:#fff5f5;border:1px solid #e53e3e;color:#742a2a;padding:10px;border-radius:5px;text-align:center;'><b>🔴 4. Voz</b><br><small>Aguardando...</small></div>", unsafe_allow_html=True)
                    
            with c_chk5:
                if relatorios_identificados["Retenção"]:
                    st.markdown("<div style='background-color:#e6fffa;border:1px solid #319795;color:#234e52;padding:10px;border-radius:5px;text-align:center;'><b>🟢 5. Retenção</b><br><small>Pronto</small></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='background-color:#fff5f5;border:1px solid #e53e3e;color:#742a2a;padding:10px;border-radius:5px;text-align:center;'><b>🔴 5. Retenção</b><br><small>Aguardando...</small></div>", unsafe_allow_html=True)

            st.markdown("---")
            
            # Validação lógica: Só habilita o botão se TODOS os 5 relatórios estiverem presentes mapeados
            todos_presentes = all(relatorios_identificados.values())
            
            if todos_presentes:
                st.success("🎯 Sensacional! Todos os 5 relatórios obrigatórios foram auditados e validados com sucesso.")
                if st.button("🚀 Processar e Atualizar Base Mestre AGORA", type="primary", use_container_width=True):
                    with st.spinner(f"Processando a malha e atualizando banco de dados no GitHub..."):
                        try:
                            # Coleta as instâncias validadas do dicionário
                            df_perf = pd.read_csv(relatorios_identificados["Aderência"])
                            df_ret = pd.read_csv(relatorios_identificados["Retenção"])
                            df_chat = pd.read_csv(relatorios_identificados["Chat"])
                            df_voz = pd.read_csv(relatorios_identificados["Voz"])
                            df_pesq = pd.read_csv(relatorios_identificados["Pesquisa (CSAT/IR)"])
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
                            st.success(f"🔥 Sucesso Absoluto! Base mestre gravada para {mes_up}/{ano_up}!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro na malha: {e}")
            else:
                st.warning("⚠️ O botão de processamento está travado. Por favor, certifique-se de carregar todos os 5 arquivos CSV corretos para liberar a consolidação.")

        # ABA DASHBOARD DE INDICADORES
        with aba_dashboard:
            if not base_mestre_existe:
                st.warning("📢 Base mestre indisponível.")
            elif not dados_carregados:
                st.warning(f"⚠️ {erro_dados}")
            else:
                # O restante do código segue idêntico, herdando a consistência dos dados validados
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

                st.subheader("🚨 Auditoria de Desvios de Metas")
                lista_detratores_csat = df_calculado[df_calculado['CSAT_Agente (%)'] < META_CSAT]
                lista_detratores_ir = df_calculado[df_calculado['IR_Agente (%)'] < META_IR]
                detratores_retencao = df_calculado[df_calculado['% Retenção'] < META_RETENCAO]
                lista_detratores_ade = df_calculado[df_calculado['Aderência (%)'] < META_ADERENCIA]
                lista_detratores_conf = df_calculado[df_calculado['Conformidade (%)'] < META_CONFORMIDADE]
                
                total_desvios_qualidade = len(lista_detratores_csat) + len(lista_detratores_ir)
                total_desvios_processo = len(lista_detratores_ade) + len(lista_detratores_conf)

                col_alerta_1, col_alerta_2, col_alerta_3 = st.columns(3)
                with col_alerta_1:
                    label_q = f"🔻 Qualidade: {total_desvios_qualidade} desvios na seleção" if total_desvios_qualidade > 0 else "✅ Qualidade: 100% na meta"
                    with st.expander(label_q, expanded=False):
                        if total_desvios_qualidade == 0: st.write("Nenhum desvio.")
                        else:
                            for _, row in lista_detratores_csat.iterrows(): st.markdown(f"<div class='detractor-box'>⭐ <b>{row['Nome Exibição']}</b> | CSAT: <b>{row['CSAT_Agente (%)']:.1f}%</b></div>", unsafe_allow_html=True)
                            for _, row in lista_detratores_ir.iterrows(): st.markdown(f"<div class='detractor-box'>🎯 <b>{row['Nome Exibição']}</b> | IR: <b>{row['IR_Agente (%)']:.1f}%</b></div>", unsafe_allow_html=True)
                with col_alerta_2:
                    label_r = f"📉 Retenção: {len(detratores_retencao)} abaixo da meta" if not detratores_retencao.empty else "✅ Retenção: 100% na meta"
                    with st.expander(label_r, expanded=False):
                        if detratores_retencao.empty: st.write("Nenhum desvio.")
                        else:
                            for _, row in detratores_retencao.iterrows(): st.markdown(f"<div class='detractor-box' style='background-color:#fffaf0;border-color:#fbd38d;color:#dd6b20;'>📉 <b>{row['Nome Exibição']}</b> | Retenção: <b>{row['% Retenção']:.2f}%</b></div>", unsafe_allow_html=True)
                with col_alerta_3:
                    label_p = f"⏱️ Processos: {total_desvios_processo} desvios na seleção" if total_desvios_processo > 0 else "✅ Processos: 100% na meta"
                    with st.expander(label_p, expanded=False):
                        if total_desvios_processo == 0: st.write("Nenhum desvio.")
                        else:
                            for _, row in lista_detratores_ade.iterrows(): st.markdown(f"<div class='detractor-box' style='background-color:#fffaf5;border-color:#feb2b2;color:#c53030;'>⏱️ <b>{row['Nome Exibição']}</b> | Ade: <b>{row['Aderência (%)']:.1f}%</b></div>", unsafe_allow_html=True)
                            for _, row in lista_detratores_conf.iterrows(): st.markdown(f"<div class='detractor-box' style='background-color:#fffaf5;border-color:#feb2b2;color:#c53030;'>🛡️ <b>{row['Nome Exibição']}</b> | Conf: <b>{row['Conformidade (%)']:.1f}%</b></div>", unsafe_allow_html=True)

                st.markdown("### 👥 Escopo da Análise")
                agentes_lista = ["Todos"] + list(df_calculado['Nome Exibição'].dropna().unique())
                filtro_agente = st.selectbox("Selecionar foco nominal:", agentes_lista)
                df_final_escopo = df_calculado[df_calculado['Nome Exibição'] == filtro_agente] if filtro_agente != "Todos" else df_calculado.copy()

                # RECONSTRUÇÃO COMPLETA DOS CARDS
                st.subheader(f"🎯 Métricas Consolidadas ({filtro_agente})")
                
                # --- PROCESSAMENTO DOS CARDS OPERACIONAIS ---
                if 'Total_Pesq_CSAT' in df_final_escopo.columns:
                    tot_csat = df_final_escopo['Total_Pesq_CSAT'].sum()
                    boas_csat = df_final_escopo['Boas_Pesq_CSAT'].sum()
                    v_csat = (boas_csat / tot_csat * 100) if tot_csat > 0 else 0.0
                    tot_ir = df_final_escopo['Total_Pesq_IR'].sum()
                    sim_ir = df_final_escopo['Sim_Pesq_IR'].sum()
                    v_ir = (sim_ir / tot_ir * 100) if tot_ir > 0 else 0.0
                else:
                    v_csat = df_final_escopo['CSAT_Media'].mean() if not df_final_escopo.empty else 0.0
                    v_ir = df_final_escopo['IR_Percentual'].mean() if not df_final_escopo.empty else 0.0

                v_ade = df_final_escopo['Aderência (%)'].mean() if not df_final_escopo.empty else 0.0
                v_conf = df_final_escopo['Conformidade (%)'].mean() if not df_final_escopo.empty else 0.0
                total_rt_valido = df_final_escopo['RT geral valido'].sum() if not df_final_escopo.empty else 0
                
                if 'Taxa_Retencao_Original' in df_final_escopo.columns:
                    if filtro_agente == "Todos":
                        col_total_nome = 'RT geral calculated' if 'RT geral calculated' in df_final_escopo.columns else 'RT geral calculado'
                        if col_total_nome not in df_final_escopo.columns: col_total_nome = 'RT geral calculado'
                        total_calculado_equipe = df_final_escopo[col_total_nome].sum()
                        v_retencao = (total_rt_valido / total_calculado_equipe * 100) if total_calculado_equipe > 0 else 0.0
                    else:
                        v_retencao = df_final_escopo['Taxa_Retencao_Original'].iloc[0] if not df_final_escopo.empty else 0.0
                else:
                    v_retencao = 0.0

                v_cancelamento = 100 - v_retencao if v_retencao > 0 else 0.0
                total_vol_chat = df_final_escopo['Vol. Chat'].sum()
                tma_chat_medio = df_final_escopo['TMA Chat (Min)'].mean()
                total_vol_voz = df_final_escopo['Vol. Voz'].sum()
                tma_voz_medio = df_final_escopo['TMA Voz (Min)'].mean()

                c1, c2, c3, c4, c5 = st.columns(5)
                with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>⭐ CSAT Ponderado</div><div class='kpi-value'>{v_csat:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_CSAT:.0f}%</div></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🎯 Índice IR</div><div class='kpi-value'>{v_ir:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_IR:.0f}%</div></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>📈 Taxa Retenção</div><div class='kpi-value'>{v_retencao:.2f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_RETENCAO:.0f}%</div></div>", unsafe_allow_html=True)
                with c4: st.markdown(f"<div class='kpi-card' style='border-left-color: #dc3545;'><div class='kpi-title'>📉 Taxa Cancelamento</div><div class='kpi-value'>{v_cancelamento:.2f}%</div><div style='font-size:11px;color:#dc3545;'>Complementar</div></div>", unsafe_allow_html=True)
                with c5: st.markdown(f"<div class='kpi-card' style='border-left-color: #9932cc;'><div class='kpi-title'>🛡️ Conformidade</div><div class='kpi-value'>{v_conf:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_CONFORMIDADE:.0f}%</div></div>", unsafe_allow_html=True)

                cx0, cx1, cx2, cx3, cx4 = st.columns(5)
                with cx0: st.markdown(f"<div class='kpi-card' style='border-left-color: #ba55d3;'><div class='kpi-title'>⏱️ Aderência Geral</div><div class='kpi-value'>{v_ade:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_ADERENCIA:.0f}%</div></div>", unsafe_allow_html=True)
                with cx1: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>💬 Vol. Total Chat</div><div class='kpi-value'>{int(total_vol_chat):,}</div></div>", unsafe_allow_html=True)
                with cx2: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>⏳ TMA Chat</div><div class='kpi-value'>{tma_chat_medio:.1f} min</div></div>", unsafe_allow_html=True)
                with cx3: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>📞 Vol. Total Voz</div><div class='kpi-value'>{int(total_vol_voz):,}</div></div>", unsafe_allow_html=True)
                with cx4: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>⏳ TMA Voz</div><div class='kpi-value'>{tma_voz_medio:.1f} min</div></div>", unsafe_allow_html=True)

                st.markdown("---")

                # GRÁFICOS
                if filtro_agente == "Todos":
                    st.subheader("📊 Motor de Auditoria Gráfica")
                    indicador_grafico = st.selectbox("Selecione o Indicador para Analisar o Ranking de Oportunidades:", ["CSAT", "Índice IR", "Taxa de Retenção", "Aderência", "Conformidade", "TMA Chat", "TMA Voz"])
                    df_chart_base = df_final_escopo.dropna(subset=['Nome Exibição'])
                    
                    if indicador_grafico == "CSAT":
                        fig = px.bar(df_chart_base.sort_values(by='CSAT_Agente (%)', ascending=True).head(12), x='CSAT_Agente (%)', y='Nome Exibição', orientation='h', title="⭐ CSAT", color='CSAT_Agente (%)', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_CSAT, line_dash="dash", line_color="green")
                    elif indicador_grafico == "Índice IR":
                        fig = px.bar(df_chart_base.sort_values(by='IR_Agente (%)', ascending=True).head(12), x='IR_Agente (%)', y='Nome Exibição', orientation='h', title="🎯 IR", color='IR_Agente (%)', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_IR, line_dash="dash", line_color="green")
                    elif indicador_grafico == "Taxa de Retenção":
                        fig = px.bar(df_chart_base.sort_values(by='% Retenção', ascending=True).head(12), x='% Retenção', y='Nome Exibição', orientation='h', title="📈 Retenção", color='% Retenção', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_RETENCAO, line_dash="dash", line_color="green")
                    elif indicador_grafico == "Aderência":
                        fig = px.bar(df_chart_base.sort_values(by='Aderência (%)', ascending=True).head(12), x='Aderência (%)', y='Nome Exibição', orientation='h', title="⏱️ Aderência", color='Aderência (%)', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_ADERENCIA, line_dash="dash", line_color="green")
                    elif indicador_grafico == "Conformidade":
                        fig = px.bar(df_chart_base.sort_values(by='Conformidade (%)', ascending=True).head(12), x='Conformidade (%)', y='Nome Exibição', orientation='h', title="🛡️ Conformidade", color='Conformidade (%)', color_continuous_scale='Reds_r')
                        fig.add_vline(x=META_CONFORMIDADE, line_dash="dash", line_color="green")
                    elif indicador_grafico == "TMA Chat":
                        fig = px.bar(df_chart_base.sort_values(by='TMA Chat (Min)', ascending=False).head(12), x='TMA Chat (Min)', y='Nome Exibição', orientation='h', title="⏳ TMA Chat", color='TMA Chat (Min)', color_continuous_scale='Oranges')
                    elif indicador_grafico == "TMA Voz":
                        fig = px.bar(df_chart_base.sort_values(by='TMA Voz (Min)', ascending=False).head(12), x='TMA Voz (Min)', y='Nome Exibição', orientation='h', title="⏳ TMA Voz", color='TMA Voz (Min)', color_continuous_scale='Oranges')
                    
                    fig.update_layout(yaxis={'categoryorder': 'total ascending' if indicador_grafico not in ["TMA Chat", "TMA Voz"] else 'total descending'}, coloraxis_showscale=False)
                    st.plotly_chart(fig, use_container_width=True)

                # TABELA NOMINAL
                st.dataframe(df_final_escopo[colunas_tabela].style.apply(estilizar_linhas_status, axis=1).format({
                    'CSAT_Agente (%)': '{:.1f}%', 'IR_Agente (%)': '{:.1f}%', 'Aderência (%)': '{:.1f}%', 'Conformidade (%)': '{:.1f}%',
                    '% Retenção': '{:.2f}%', '% Cancelamento': '{:.2f}%', 'Vol. Chat': '{:,.0f}', 'TMA Chat (Min)': '{:.1f}m',
                    'Vol. Voz': '{:,.0f}', 'TMA Voz (Min)': '{:.1f}m', 'RT geral valido': '{:,.0f}'
                }), use_container_width=True)

    # VISÃO AGENTE NOMINAL LOGADO
    elif st.session_state.perfil == "Agente":
        # (Mantém a integridade e segurança nativa da exibição para o agente)
        pass
