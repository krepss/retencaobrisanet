import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github
import io
import time
import base64
import json
from datetime import datetime, timedelta

# ==========================================
# CONFIGURAÇÕES GERAIS E PARÂMETROS DE METAS
# ==========================================
st.set_page_config(page_title="Sistema Operacional 360", page_icon="🎯", layout="wide")

GESTOR_EMAIL = "gestor"
GESTOR_SENHA = "admin"

# METAS OFICIAIS DA OPERAÇÃO BRISANET
META_CSAT = 92.0
META_IR = 88.0
META_RETENCAO = 65.0
META_ADERENCIA = 92.0
META_CONFORMIDADE = 92.0
META_TPC = 15.0  # Meta de Trabalho Pós-Chamada em Segundos

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
ANOS = ["2026", "2027", "2028", "2029", "2030"]

st.markdown("""
    <style>
        .kpi-card {
            background-color: #ffffff;
            border-left: 5px solid #007bff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
            text-align: center;
            margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-5px);
        }
        .kpi-title {
            font-size: 13px;
            color: #6c757d;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }
        .kpi-value {
            font-size: 28px;
            color: #212529;
            font-weight: 900;
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
        .info-card {
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            padding: 15px;
            border-radius: 8px;
            color: #495057;
            margin-bottom: 15px;
            text-align: center;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.02);
        }
        .info-title {
            font-size: 12px;
            color: #adb5bd;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .info-data {
            font-size: 16px;
            color: #343a40;
            font-weight: bold;
        }
        .ferias-card {
            background-color: #e3f2fd;
            border-left: 5px solid #1e88e5;
            padding: 15px;
            border-radius: 6px;
            color: #0d47a1;
            margin-bottom: 15px;
            font-weight: bold;
        }
        .banner-ferias {
            background: linear-gradient(135deg, #1e88e5 0%, #005cb2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 12px;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 20px;
            box-shadow: 0px 8px 15px rgba(30, 136, 229, 0.3);
        }
        .banner-ferias h2 {
            color: white !important;
            font-weight: 900;
            margin-top: 10px;
            font-size: 36px;
        }
        .btn-wiki {
            display: inline-block;
            background-color: #007bff;
            color: white !important;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: 16px;
            margin-top: 10px;
            transition: background-color 0.3s;
        }
        .btn-wiki:hover {
            background-color: #0056b3;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GESTÃO DE SESSÃO COM PERSISTÊNCIA (URL SAFE)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.perfil = ""
    st.session_state.user_email = ""
    st.session_state.user_nome = ""

def salvar_sessao(email, perfil, nome):
    dados = {"email": email, "perfil": perfil, "nome": nome}
    token = base64.urlsafe_b64encode(json.dumps(dados).encode('utf-8')).decode('utf-8')
    st.query_params["session"] = token

def restaurar_sessao():
    if "session" in st.query_params:
        try:
            token = st.query_params["session"]
            token += "=" * ((4 - len(token) % 4) % 4)
            dados = json.loads(base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8'))
            st.session_state.logged_in = True
            st.session_state.user_email = dados.get("email", "")
            st.session_state.perfil = dados.get("perfil", "")
            st.session_state.user_nome = dados.get("nome", "")
        except Exception:
            pass

def fazer_logout():
    st.session_state.logged_in = False
    st.session_state.perfil = ""
    st.session_state.user_email = ""
    st.session_state.user_nome = ""
    st.query_params.clear()
    st.cache_data.clear() 

if not st.session_state.logged_in:
    restaurar_sessao()

# ==========================================
# FUNÇÕES DE LEITURA E GRAVAÇÃO VIA API GITHUB E UTILITÁRIAS
# ==========================================
def ler_csv_upload_seguro(arquivo, nrows=None):
    try:
        arquivo.seek(0)
        return pd.read_csv(arquivo, nrows=nrows, sep=None, engine='python', encoding='utf-8')
    except Exception:
        arquivo.seek(0)
        return pd.read_csv(arquivo, nrows=nrows, sep=None, engine='python', encoding='latin1')

def ler_csv_via_api_github(nome_arquivo):
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["GITHUB_REPO"])
    arquivo_git = repo.get_contents(nome_arquivo)
    conteudo_texto = arquivo_git.decoded_content.decode('utf-8')
    return pd.read_csv(io.StringIO(conteudo_texto), sep=None, engine='python')

def enviar_para_github(nome_arquivo_git, conteudo):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        if hasattr(conteudo, 'getvalue'): conteudo_final = conteudo.getvalue()
        else: conteudo_final = conteudo.encode('utf-8')
        try:
            arquivo_existente = repo.get_contents(nome_arquivo_git)
            repo.update_file(arquivo_existente.path, f"Atualização: {nome_arquivo_git}", conteudo_final, arquivo_existente.sha)
            return True, f"{nome_arquivo_git} atualizado!"
        except Exception:
            repo.create_file(nome_arquivo_git, f"Criação: {nome_arquivo_git}", conteudo_final)
            return True, f"{nome_arquivo_git} criado!"
    except Exception as e: return False, f"Erro: {e}"

def limpar_porcentagem(valor):
    if pd.isna(valor): return 0.0
    try:
        val = float(valor)
        if val <= 1.0 and val > 0: return val * 100
        return val
    except ValueError:
        valor_str = str(valor).replace('%', '').replace(',', '.')
        if valor_str.lower() == 'nan': return 0.0
        return float(valor_str)

def ms_para_minutos(ms):
    if pd.isna(ms): return 0.0
    return ms / 1000 / 60

def ms_para_segundos(ms):
    if pd.isna(ms): return 0.0
    return ms / 1000

def limpar_nome_duplo(nome):
    if pd.isna(nome): return ""
    # Remove espaços extras duplos e coloca no formato Title Case correto
    return " ".join(str(nome).strip().split()).title()

def calcular_tempo_empresa(data_str):
    if pd.isna(data_str) or str(data_str).strip() == "": return "Não informada"
    try:
        data_admissao = datetime.strptime(str(data_str).strip(), "%d/%m/%Y")
        hoje = datetime.now()
        dias = (hoje - data_admissao).days
        if dias < 0: return "Inicia no futuro"
        anos = dias // 365
        meses = (dias % 365) // 30
        
        if anos > 0 and meses > 0: return f"{anos} ano(s) e {meses} mês(es)"
        elif anos > 0: return f"{anos} ano(s)"
        elif meses > 0: return f"{meses} mês(es)"
        else: return f"{dias} dia(s)"
    except Exception:
        return "Formato inválido"

@st.cache_data(ttl=60)
def obter_ultima_atualizacao():
    """Busca no GitHub a data e hora do último commit da Base Mestre e converte para Horário de Brasília"""
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        commits = repo.get_commits(path="dados_consolidados_master.csv")
        if commits.totalCount > 0:
            data_utc = commits[0].commit.author.date
            # Converte UTC para Horário de Brasília (UTC-3)
            data_br = data_utc - timedelta(hours=3)
            return data_br.strftime("%d/%m/%Y às %H:%M:%S")
        return "Sem registros"
    except Exception:
        return "Indisponível"

# ==========================================
# MOTOR DE CÁLCULO DE COMISSÃO + GAMIFICAÇÃO
# ==========================================
def calcular_comissao_rv(taxa_ret, vol_fibra, vol_adic, diamantes):
    """Calcula a RV combinando volume de retenção, tabela de percentual corrigida e bônus de gamificação (Diamantes)"""
    taxa_ret = float(taxa_ret) if pd.notna(taxa_ret) else 0.0
    vol_fibra = float(vol_fibra) if pd.notna(vol_fibra) else 0.0
    vol_adic = float(vol_adic) if pd.notna(vol_adic) else 0.0
    diamantes = int(diamantes) if pd.notna(diamantes) else 0
    
    vol_total = vol_fibra + vol_adic
    atingiu_gatilho = vol_total >= 176
    
    valor_diamantes = diamantes * 0.50
    
    if atingiu_gatilho:
        multiplicador = 0.0
        if taxa_ret >= 65.00:
            multiplicador = 7.50
        elif taxa_ret >= 60.00:
            multiplicador = 6.00
        elif taxa_ret >= 55.00:
            multiplicador = 4.80
        elif taxa_ret >= 50.00:
            multiplicador = 3.60
        elif taxa_ret >= 46.00:
            multiplicador = 2.40
        else:
            multiplicador = 0.00
            
        comissao_retencao = (vol_fibra * multiplicador) + (vol_adic * 1.50)
        comissao_total = comissao_retencao + valor_diamantes
    else:
        comissao_total = valor_diamantes * 0.50
        
    return comissao_total

@st.cache_data(ttl=5)
def carregar_dados_mestre_seguro():
    try:
        df = ler_csv_via_api_github("dados_consolidados_master.csv")
        if df.empty: return df
        df['text_ano'] = df['Ano'].astype(str).str.strip()
        df['text_mes'] = df['Mês'].astype(str).str.strip().str.title()
        df['Periodo_Competencia'] = df['text_mes'] + "/" + df['text_ano']
        
        if 'Nome Exibição' in df.columns:
            df['Nome Exibição'] = df['Nome Exibição'].apply(limpar_nome_duplo)
            
        # FILTRO ANTI-DUPLICIDADE GLOBAL: Garante que exista apenas 1 linha por operador por mês
        if 'Nome Exibição' in df.columns and 'text_mes' in df.columns and 'text_ano' in df.columns:
            df = df.drop_duplicates(subset=['Nome Exibição', 'text_mes', 'text_ano'], keep='first')
            
        return df
    except Exception:
        return pd.DataFrame()

def obter_dados_historicos(df, agente="Todos"):
    """Filtra e consolida a base de dados de todos os meses para criar o gráfico histórico"""
    df_hist = df.copy()
    
    if agente != "Todos":
        if 'Nome Exibição' not in df_hist.columns:
            df_hist['Nome Exibição'] = df_hist['Chave_Nome'].apply(limpar_nome_duplo) if 'Chave_Nome' in df_hist.columns else "Desconhecido"
        df_hist = df_hist[df_hist['Nome Exibição'] == agente]
    
    if df_hist.empty:
        return pd.DataFrame()
        
    def get_status_hist(row):
        if str(row.get('STATUS', 'ATIVO')).strip().upper() == 'AFASTADO': return 'Afastado'
        mes_ferias = str(row.get('FÉRIAS 2026', '')).strip().upper()
        if mes_ferias == str(row.get('text_mes', '')).strip().upper(): return 'Férias'
        return 'Ativo'
    
    df_hist['Status_Dinamico_Hist'] = df_hist.apply(get_status_hist, axis=1)
    if 'Faltas' in df_hist.columns:
        df_hist['Faltas'] = df_hist.apply(lambda r: r['Faltas'] if r['Status_Dinamico_Hist'] == 'Ativo' else 0, axis=1)
        
    meses_map = {m: i for i, m in enumerate(MESES, 1)}
    df_hist['Mes_Num'] = df_hist['text_mes'].map(meses_map)
    df_hist = df_hist.dropna(subset=['Mes_Num'])
    df_hist['Periodo_Ordem'] = df_hist['text_ano'].astype(str) + "-" + df_hist['Mes_Num'].astype(int).astype(str).str.zfill(2)
    
    cols_sum = ['Total_Pesq_CSAT', 'Boas_Pesq_CSAT', 'Total_Pesq_IR', 'Sim_Pesq_IR', 'RT geral valido', 'RT geral calculado', 'Faltas']
    cols_mean = ['Aderência (%)', 'Conformidade (%)', 'Taxa_Retencao_Original']
    
    for c in cols_sum + cols_mean:
        if c not in df_hist.columns:
            df_hist[c] = 0.0
            
    df_hist[cols_sum] = df_hist[cols_sum].apply(pd.to_numeric, errors='coerce').fillna(0)
    df_hist[cols_mean] = df_hist[cols_mean].apply(pd.to_numeric, errors='coerce').fillna(0)
    
    grp = df_hist.groupby(['Periodo_Ordem', 'text_mes', 'text_ano']).agg({
        'Total_Pesq_CSAT': 'sum', 'Boas_Pesq_CSAT': 'sum',
        'Total_Pesq_IR': 'sum', 'Sim_Pesq_IR': 'sum',
        'RT geral valido': 'sum', 'RT geral calculado': 'sum',
        'Faltas': 'sum',
        'Aderência (%)': 'mean', 'Conformidade (%)': 'mean',
        'Taxa_Retencao_Original': 'mean'
    }).reset_index()
    
    grp['CSAT Ponderado (%)'] = grp.apply(lambda r: (r['Boas_Pesq_CSAT']/r['Total_Pesq_CSAT']*100) if r['Total_Pesq_CSAT']>0 else 0, axis=1)
    grp['Índice IR (%)'] = grp.apply(lambda r: (r['Sim_Pesq_IR']/r['Total_Pesq_IR']*100) if r['Total_Pesq_IR']>0 else 0, axis=1)
    grp['Taxa Retenção (%)'] = grp.apply(lambda r: (r['RT geral valido']/r['RT geral calculado']*100) if r['RT geral calculado']>0 else r['Taxa_Retencao_Original'], axis=1)
    
    grp = grp.sort_values('Periodo_Ordem')
    grp['Mês/Ano'] = grp['text_mes'].str[:3] + "/" + grp['text_ano'].str[-2:]
    return grp

# ==========================================
# TELA DE LOGIN APRIMORADA E INTUITIVA
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #007bff; margin-bottom: 0px;'>🎯 Operacional 360</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6c757d; margin-bottom: 40px;'>Portal de Gestão de Qualidade e Performance</p>", unsafe_allow_html=True)
    
    col_vazia1, col_login, col_vazia2 = st.columns([1, 2, 1])
    
    with col_login:
        aba_login, aba_novo = st.tabs(["🔐 Acessar Sistema", "🆕 Primeiro Acesso (Criar Senha)"])
        
        with aba_login:
            with st.form("form_login"):
                st.markdown("#### Entrar")
                email_input = st.text_input("E-mail corporativo", placeholder="seu.nome@grupobrisanet.com.br")
                senha_input = st.text_input("Senha", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Acessar Painel", use_container_width=True)
            
            if submit_login:
                email_limpo = email_input.strip().lower()
                senha_limpa = senha_input.strip()
                
                if email_limpo == GESTOR_EMAIL.lower() and senha_limpa == GESTOR_SENHA:
                    st.session_state.logged_in = True
                    st.session_state.perfil = "Gestor"
                    st.session_state.user_nome = "Gestor"
                    salvar_sessao(email_limpo, "Gestor", "Gestor")
                    st.success("Login efetuado!")
                    time.sleep(0.5)
                    st.rerun() 
                else:
                    try:
                        df_users_login = ler_csv_via_api_github("dados_usuarios.csv")
                        col_email = 'E-MAIL' if 'E-MAIL' in df_users_login.columns else 'E-mail'
                        
                        df_users_login[col_email] = df_users_login[col_email].astype(str)
                        mask_login = df_users_login[col_email].str.strip().str.lower() == email_limpo
                        
                        if mask_login.any():
                            dados_usr = df_users_login[mask_login].iloc[0]
                            senha_correta = str(dados_usr.get('SENHA', '')).strip()
                            
                            if senha_correta == "" or senha_correta.lower() == "nan":
                                st.warning("⚠️ **Atenção:** Você ainda não possui uma senha cadastrada. Por favor, clique na aba **'Primeiro Acesso'** ao lado para criar a sua.")
                            elif senha_limpa == senha_correta:
                                st.session_state.logged_in = True
                                st.session_state.perfil = "Agente"
                                st.session_state.user_email = email_limpo
                                col_nome = 'COLABORADOR' if 'COLABORADOR' in dados_usr else 'Nome'
                                st.session_state.user_nome = limpar_nome_duplo(dados_usr[col_nome])
                                salvar_sessao(email_limpo, "Agente", st.session_state.user_nome)
                                st.success("Login efetuado!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ E-mail ou senha incorreta.")
                        else: st.error("❌ E-mail não encontrado na base de dados. Procure a gestão.")
                    except Exception: st.error("❌ Banco de dados de usuários não localizado.")
        
        with aba_novo:
            with st.form("form_novo_acesso"):
                st.markdown("#### Criar minha senha")
                st.info("Insira o seu e-mail corporativo e escolha uma senha forte para acessar o sistema.")
                email_novo = st.text_input("Seu E-mail corporativo")
                senha_nova = st.text_input("Crie uma Senha", type="password")
                senha_confirma = st.text_input("Confirme a Senha", type="password")
                submit_novo = st.form_submit_button("Cadastrar Senha", use_container_width=True)

            if submit_novo:
                email_novo_limpo = email_novo.strip().lower()
                if len(senha_nova) < 4:
                    st.error("A senha deve ter pelo menos 4 caracteres.")
                elif senha_nova != senha_confirma:
                    st.error("As senhas não coincidem. Tente novamente.")
                else:
                    try:
                        df_users_update = ler_csv_via_api_github("dados_usuarios.csv")
                        col_email_up = 'E-MAIL' if 'E-MAIL' in df_users_update.columns else 'E-mail'
                        
                        df_users_update[col_email_up] = df_users_update[col_email_up].astype(str)
                        if 'SENHA' not in df_users_update.columns:
                            df_users_update['SENHA'] = ""
                        df_users_update['SENHA'] = df_users_update['SENHA'].astype(str)
                        
                        mask = df_users_update[col_email_up].str.strip().str.lower() == email_novo_limpo
                        
                        if mask.any():
                            senha_atual = str(df_users_update.loc[mask, 'SENHA'].iloc[0]).strip()
                            if senha_atual != "" and senha_atual.lower() != "nan":
                                st.warning("⚠️ **Aviso:** Este e-mail já tem uma senha cadastrada. Vá para a aba 'Acessar Sistema' e faça o login.")
                            else:
                                df_users_update.loc[mask, 'SENHA'] = senha_nova
                                enviar_para_github("dados_usuarios.csv", df_users_update.to_csv(index=False))
                                st.cache_data.clear()
                                st.success("✅ **Senha cadastrada com sucesso!** Vá para a aba 'Acessar Sistema' para iniciar sessão.")
                        else:
                            st.error("❌ E-mail não localizado na base. Verifique se digitou corretamente.")
                    except Exception as e:
                        st.error(f"Erro ao conectar à base de dados: {e}")

# ==========================================
# SISTEMA LOGADO
# ==========================================
else:
    st.sidebar.title("Opções")
    st.sidebar.success(f"Logado como: **{st.session_state.user_nome}**")
    
    st.sidebar.markdown("### 📅 Filtro de Período")
    mes_view = st.sidebar.selectbox("Mês de Análise:", MESES, index=4) 
    ano_view = st.sidebar.selectbox("Ano de Análise:", ANOS)
    
    st.sidebar.markdown("---")
    info_atualizacao = obter_ultima_atualizacao()
    st.sidebar.info(f"🔄 **Base atualizada em:**\n{info_atualizacao} (BRT)")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair do Sistema (Logout)", use_container_width=True):
        fazer_logout()
        st.rerun()

    base_mestre_existe = True
    erro_dados = ""
    
    try:
        df_completo = carregar_dados_mestre_seguro()
        df_periodo = df_completo[(df_completo['text_mes'].str.lower() == mes_view.lower()) & (df_completo['text_ano'] == str(ano_view))]
        dados_carregados = not df_periodo.empty
        if df_periodo.empty: erro_dados = f"Sem dados consolidados para {mes_view}/{ano_view}."
    except Exception as e:
        base_mestre_existe, dados_carregados, erro_dados = False, False, str(e)

    # ==========================================
    # VISÃO DO GESTOR
    # ==========================================
    if st.session_state.perfil == "Gestor":
        
        df_periodo_mapeado = df_periodo.copy()
        if not df_periodo_mapeado.empty:
            def identificar_status_unificado(row):
                if str(row.get('STATUS', 'ATIVO')).strip().upper() == 'AFASTADO': return 'Afastado'
                mes_ferias = str(row.get('FÉRIAS 2026', '')).strip().upper()
                if mes_ferias == mes_view.upper(): return 'Férias'
                return 'Ativo'
            df_periodo_mapeado['Status_Dinamico'] = df_periodo_mapeado.apply(identificar_status_unificado, axis=1)

        aba_dashboard, aba_retencao, aba_comissao, aba_ponto, aba_equipe, aba_ferias, aba_relatorio, aba_feedback, aba_upload = st.tabs([
            "📊 Dashboard", 
            "🎯 Retenção",
            "💰 Comissões",
            "⏰ B. Horas",
            "👥 Equipe",
            "🌴 Férias",
            "📑 Relatório Diretoria",
            "📈 Avaliação & Feedback",
            "⚙️ Upload"
        ])
        
        with aba_retencao:
            st.header("🎯 Inteligência e Qualidade de Retenção")
            if not base_mestre_existe or df_periodo_mapeado.empty:
                st.warning("Não há dados processados para gerar as análises de retenção neste mês.")
            else:
                df_ret_ativos = df_periodo_mapeado[df_periodo_mapeado['Status_Dinamico'] == 'Ativo'].copy()
                if 'Taxa_Retencao_Original' in df_ret_ativos.columns and 'RT geral calculado' in df_ret_ativos.columns:
                    df_ret_ativos = df_ret_ativos[df_ret_ativos['RT geral calculado'] > 0]
                    if df_ret_ativos.empty:
                        st.info("Nenhuma oportunidade de retenção registrada para os operadores ativos neste mês.")
                    else:
                        tot_oportunidades = df_ret_ativos['RT geral calculado'].sum()
                        tot_retidos = df_ret_ativos['RT geral valido'].sum()
                        tot_perdidos = tot_oportunidades - tot_retidos
                        taxa_global = (tot_retidos / tot_oportunidades * 100) if tot_oportunidades > 0 else 0
                        
                        c_ret1, c_ret2, c_ret3, c_ret4 = st.columns(4)
                        with c_ret1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total de Intenções</div><div class='kpi-value'>{int(tot_oportunidades):,}</div><div style='font-size:11px;color:#6c757d;'>Chamadas de Cancelamento</div></div>", unsafe_allow_html=True)
                        with c_ret2: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Clientes Salvos</div><div class='kpi-value' style='color:#28a745;'>{int(tot_retidos):,}</div><div style='font-size:11px;color:#28a745;'>Sucesso</div></div>", unsafe_allow_html=True)
                        with c_ret3: st.markdown(f"<div class='kpi-card' style='border-left-color: #dc3545;'><div class='kpi-title'>Clientes Perdidos</div><div class='kpi-value' style='color:#dc3545;'>{int(tot_perdidos):,}</div><div style='font-size:11px;color:#dc3545;'>Churn</div></div>", unsafe_allow_html=True)
                        with c_ret4: st.markdown(f"<div class='kpi-card' style='border-left-color: #9932cc;'><div class='kpi-title'>Retenção Global</div><div class='kpi-value'>{taxa_global:.1f}%</div><div style='font-size:11px;color:#6c757d;'>Meta: {META_RETENCAO}%</div></div>", unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.subheader("⚠️ Matriz de Risco Operacional")
                        st.markdown("Identifique quem recebe muitas chamadas de cancelamento e salva poucos clientes (Quadrante Inferior Direito = **Risco Alto**).")
                        
                        fig_scatter = px.scatter(df_ret_ativos, x='RT geral calculado', y='Taxa_Retencao_Original', size='RT geral calculado', color='Taxa_Retencao_Original', color_continuous_scale=['#dc3545', '#ffc107', '#28a745'], hover_name='Nome Exibição', labels={'RT geral calculado': 'Total de Oportunidades (Volume)', 'Taxa_Retencao_Original': 'Taxa de Retenção (%)'}, title="Impacto de Volume x Eficiência de Retenção")
                        fig_scatter.add_hline(y=META_RETENCAO, line_dash="dash", line_color="green", annotation_text=f"Meta ({META_RETENCAO}%)")
                        st.plotly_chart(fig_scatter, use_container_width=True)

                        st.markdown("---")
                        c_rank1, c_rank2 = st.columns(2)
                        df_ordenado = df_ret_ativos.sort_values(by='Taxa_Retencao_Original', ascending=False)
                        
                        with c_rank1:
                            st.markdown("#### 🏆 Top 3 - Excelência em Retenção")
                            top3 = df_ordenado.head(3)
                            for i, row in top3.reset_index().iterrows():
                                icone = "🥇" if i==0 else ("🥈" if i==1 else "🥉")
                                st.markdown(f"<div style='background-color:#f6ffed; border-left: 4px solid #28a745; padding: 10px; margin-bottom: 8px; border-radius: 4px;'><b>{icone} {row['Nome Exibição']}</b><br/>Taxa: <b>{row['Taxa_Retencao_Original']:.2f}%</b> (Salvou {int(row['RT geral valido'])} de {int(row['RT geral calculado'])})</div>", unsafe_allow_html=True)
                                
                        with c_rank2:
                            st.markdown("#### 🚨 Top 3 - Foco para Feedback (Ofensores)")
                            bottom3 = df_ordenado.tail(3).sort_values(by='Taxa_Retencao_Original', ascending=True)
                            for i, row in bottom3.reset_index().iterrows():
                                st.markdown(f"<div style='background-color:#fff5f5; border-left: 4px solid #dc3545; padding: 10px; margin-bottom: 8px; border-radius: 4px;'><b>📉 {row['Nome Exibição']}</b><br/>Taxa: <b>{row['Taxa_Retencao_Original']:.2f}%</b> (Perdeu {int(row['RT geral calculado'] - row['RT geral valido'])} clientes)</div>", unsafe_allow_html=True)
                else:
                    st.info("A base de dados atual não possui as colunas de retenção estruturadas corretamente.")

        with aba_comissao:
            st.header("💰 Gestão de Remuneração Variável (Comissões)")
            st.markdown("Acompanhe o atingimento do volume mínimo (176 peças) e a comissão gerada por cada operador no mês.")
            
            if not base_mestre_existe or df_periodo_mapeado.empty:
                st.warning("Não há dados processados para este mês.")
            else:
                df_com = df_periodo_mapeado[df_periodo_mapeado['Status_Dinamico'] == 'Ativo'].copy()
                
                if 'Taxa_Retencao_Original' not in df_com.columns: df_com['Taxa_Retencao_Original'] = 0.0
                if 'RT_Fibra_Validas' not in df_com.columns: df_com['RT_Fibra_Validas'] = 0.0
                if 'RT_Adicional_Validas' not in df_com.columns: df_com['RT_Adicional_Validas'] = 0.0
                if 'Diamantes' not in df_com.columns: df_com['Diamantes'] = 0
                
                df_com['Vol_Fibra'] = pd.to_numeric(df_com['RT_Fibra_Validas'], errors='coerce').fillna(0)
                df_com['Vol_Adic'] = pd.to_numeric(df_com['RT_Adicional_Validas'], errors='coerce').fillna(0)
                df_com['Total_Pecas'] = df_com['Vol_Fibra'] + df_com['Vol_Adic']
                df_com['Taxa_Ret'] = pd.to_numeric(df_com['Taxa_Retencao_Original'], errors='coerce').fillna(0)
                df_com['Diamantes_Val'] = pd.to_numeric(df_com['Diamantes'], errors='coerce').fillna(0)
                
                df_com['Comissão (R$)'] = df_com.apply(lambda r: calcular_comissao_rv(r['Taxa_Ret'], r['Vol_Fibra'], r['Vol_Adic'], r['Diamantes_Val']), axis=1)
                df_com['Atingiu Gatilho (176)?'] = df_com['Total_Pecas'].apply(lambda x: '✅ Sim' if x >= 176 else '❌ Não (50% Diamantes)')
                
                colunas_mostrar = ['Nome Exibição', 'Diamantes_Val', 'Vol_Fibra', 'Vol_Adic', 'Total_Pecas', 'Atingiu Gatilho (176)?', 'Taxa_Ret', 'Comissão (R$)']
                df_mostrar = df_com[colunas_mostrar].sort_values(by=['Comissão (R$)', 'Total_Pecas'], ascending=[False, False])
                
                df_mostrar.rename(columns={
                    'Nome Exibição': 'Operador', 
                    'Diamantes_Val': 'Diamantes',
                    'Vol_Fibra': 'Retenções (Fibra/5G)', 
                    'Vol_Adic': 'Retenções Adicionais', 
                    'Total_Pecas': 'Total Geral (Peças)', 
                    'Taxa_Ret': 'Taxa de Retenção (%)'
                }, inplace=True)
                
                tot_comissao = df_mostrar['Comissão (R$)'].sum()
                tot_elegiveis = len(df_mostrar[df_mostrar['Total Geral (Peças)'] >= 176])
                
                c_c1, c_c2 = st.columns(2)
                with c_c1:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Total de Comissão a Pagar</div><div class='kpi-value' style='color:#28a745;'>R$ {tot_comissao:,.2f}</div></div>", unsafe_allow_html=True)
                with c_c2:
                    st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>Atingiram a Meta Cheia (>176 peças)</div><div class='kpi-value'>{tot_elegiveis} de {len(df_mostrar)}</div></div>", unsafe_allow_html=True)
                
                st.markdown("#### 📋 Tabela Detalhada de Comissões e Gamificação")
                
                # Formatando os valores como string de forma nativa para evitar que erros de tipagem do Streamlit destruam a visualização
                df_mostrar_fmt = df_mostrar.copy()
                df_mostrar_fmt['Diamantes'] = df_mostrar_fmt['Diamantes'].apply(lambda x: f"{x:.0f}")
                df_mostrar_fmt['Retenções (Fibra/5G)'] = df_mostrar_fmt['Retenções (Fibra/5G)'].apply(lambda x: f"{x:.0f}")
                df_mostrar_fmt['Retenções Adicionais'] = df_mostrar_fmt['Retenções Adicionais'].apply(lambda x: f"{x:.0f}")
                df_mostrar_fmt['Total Geral (Peças)'] = df_mostrar_fmt['Total Geral (Peças)'].apply(lambda x: f"{x:.0f}")
                df_mostrar_fmt['Taxa de Retenção (%)'] = df_mostrar_fmt['Taxa de Retenção (%)'].apply(lambda x: f"{x:.2f}%")
                df_mostrar_fmt['Comissão (R$)'] = df_mostrar_fmt['Comissão (R$)'].apply(lambda x: f"R$ {x:,.2f}")
                
                st.dataframe(df_mostrar_fmt, use_container_width=True)

        with aba_ponto:
            st.header("⏰ Verificação de Banco de Horas")
            st.markdown("Faça o upload do arquivo de **Saldo de Horas** extraído do sistema para analisar os saldos da equipe.")
            arquivo_ponto = st.file_uploader("Arraste e solte o arquivo de Saldo de Horas aqui (CSV ou Excel)", type=["csv", "xlsx"])
            if arquivo_ponto:
                try:
                    if arquivo_ponto.name.endswith('.csv'): df_ponto = pd.read_csv(arquivo_ponto, skiprows=4, sep=None, engine='python')
                    else: df_ponto = pd.read_excel(arquivo_ponto, skiprows=4)
                    
                    if 'Nome' in df_ponto.columns and 'Total Banco' in df_ponto.columns:
                        def calcular_minutos_ponto(val):
                            if pd.isna(val): return 0
                            val_str = str(val).strip()
                            if not val_str or val_str == '00:00': return 0
                            multiplicador = -1 if '-' in val_str else 1
                            val_limpo = val_str.replace('+', '').replace('-', '')
                            try:
                                partes = val_limpo.split(':')
                                hh = int(partes[0])
                                mm = int(partes[1]) if len(partes) > 1 else 0
                                return (hh * 60 + mm) * multiplicador
                            except: return 0
                        
                        df_ponto['Minutos Saldo'] = df_ponto['Total Banco'].apply(calcular_minutos_ponto)
                        df_ponto['Status Saldo'] = df_ponto['Minutos Saldo'].apply(lambda x: 'Negativo' if x < 0 else ('Positivo' if x > 0 else 'Zerado'))
                        
                        tot_neg = len(df_ponto[df_ponto['Status Saldo'] == 'Negativo'])
                        tot_pos = len(df_ponto[df_ponto['Status Saldo'] == 'Positivo'])
                        tot_zer = len(df_ponto[df_ponto['Status Saldo'] == 'Zerado'])
                        
                        c1, c2, c3 = st.columns(3)
                        with c1: st.markdown(f"<div class='kpi-card' style='border-left-color: #dc3545;'><div class='kpi-title'>Saldos Negativos</div><div class='kpi-value' style='color:#dc3545;'>{tot_neg}</div></div>", unsafe_allow_html=True)
                        with c2: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Saldos Positivos</div><div class='kpi-value' style='color:#28a745;'>{tot_pos}</div></div>", unsafe_allow_html=True)
                        with c3: st.markdown(f"<div class='kpi-card' style='border-left-color: #6c757d;'><div class='kpi-title'>Saldos Zerados</div><div class='kpi-value' style='color:#6c757d;'>{tot_zer}</div></div>", unsafe_allow_html=True)
                        
                        st.markdown("---")
                        c_graf1, c_graf2 = st.columns(2)
                        with c_graf1:
                            df_negativos = df_ponto[df_ponto['Minutos Saldo'] < 0].sort_values('Minutos Saldo', ascending=True).head(15)
                            if not df_negativos.empty:
                                fig_neg = px.bar(df_negativos, x='Minutos Saldo', y='Nome', orientation='h', title="🚨 Maiores Saldos Negativos", text='Total Banco', color_discrete_sequence=['#dc3545'])
                                fig_neg.update_yaxes(autorange="reversed")
                                st.plotly_chart(fig_neg, use_container_width=True)
                            else: st.success("Nenhum saldo negativo na equipe!")
                                
                        with c_graf2:
                            df_positivos = df_ponto[df_ponto['Minutos Saldo'] > 0].sort_values('Minutos Saldo', ascending=False).head(15)
                            if not df_positivos.empty:
                                fig_pos = px.bar(df_positivos, x='Minutos Saldo', y='Nome', orientation='h', title="📈 Maiores Saldos Positivos", text='Total Banco', color_discrete_sequence=['#28a745'])
                                fig_pos.update_yaxes(autorange="reversed")
                                st.plotly_chart(fig_pos, use_container_width=True)
                            else: st.info("Nenhum saldo positivo na equipe.")
                                
                        st.subheader("📋 Detalhamento Completo de Banco de Horas")
                        def formatar_cores_ponto(row):
                            if row['Status Saldo'] == 'Negativo': return ['background-color: #fff5f5; color: #dc3545;'] * len(row)
                            elif row['Status Saldo'] == 'Positivo': return ['background-color: #f6ffed; color: #28a745;'] * len(row)
                            return ['color: #6c757d;'] * len(row)
                        colunas_visiveis = ['Nome', 'Cargo', 'Saldo Anterior', 'Saldo do Período', 'Total Banco', 'Status Saldo']
                        st.dataframe(df_ponto[colunas_visiveis].style.apply(formatar_cores_ponto, axis=1), use_container_width=True)
                    else: st.error("O arquivo carregado não tem as colunas corretas ('Nome' e 'Total Banco'). Verifique se é a extração correta.")
                except Exception as e: st.error(f"Ocorreu um erro na leitura do arquivo de ponto: {e}")

        with aba_equipe:
            st.header("👥 Cadastro Unificado da Equipe (Mestre)")
            st.info("💡 **Dica:** Esta é a sua Fonte Única de Verdades. O status e o mês de férias inseridos aqui serão lidos automaticamente por todo o Dashboard.")
            try:
                df_users_atual = ler_csv_via_api_github("dados_usuarios.csv")
                
                if 'Nome' in df_users_atual.columns:
                    if 'COLABORADOR' not in df_users_atual.columns: df_users_atual.rename(columns={'Nome': 'COLABORADOR'}, inplace=True)
                    else: df_users_atual.drop(columns=['Nome'], inplace=True)
                if 'E-mail' in df_users_atual.columns:
                    if 'E-MAIL' not in df_users_atual.columns: df_users_atual.rename(columns={'E-mail': 'E-MAIL'}, inplace=True)
                    else: df_users_atual.drop(columns=['E-mail'], inplace=True)

                colunas_esperadas = ['COLABORADOR', 'E-MAIL', 'FÉRIAS 2026', 'STATUS', 'SENHA', 'ADMISSÃO']
                for col in colunas_esperadas:
                    if col not in df_users_atual.columns: df_users_atual[col] = ""

                df_users_atual = df_users_atual[colunas_esperadas]
                df_users_editado = st.data_editor(df_users_atual, num_rows="dynamic", use_container_width=True, key="ed_usr")
                
                if st.button("💾 Salvar Base Mestre de Usuários", type="primary"):
                    enviar_para_github("dados_usuarios.csv", df_users_editado.to_csv(index=False))
                    st.cache_data.clear()
                    st.success("Equipe salva com sucesso!")
                    time.sleep(0.5)
                    st.rerun()
            except Exception: 
                st.warning("Faça o upload do seu CSV de usuários para começar.")
                up_arq = st.file_uploader("Upload Arquivo de Usuários", type=['csv'])
                if up_arq and st.button("Criar"):
                    enviar_para_github("dados_usuarios.csv", up_arq)
                    st.rerun()

        with aba_ferias:
            st.header("🌴 Gestão e Calendário de Férias")
            st.markdown("Tenha uma visão rápida de quem sai de folga em cada mês para não sobrecarregar a escala de atendimento.")
            try:
                df_ferias = ler_csv_via_api_github("dados_usuarios.csv")
                
                df_grafico_ferias = df_ferias.copy()
                df_grafico_ferias['FÉRIAS 2026'] = df_grafico_ferias['FÉRIAS 2026'].fillna('').astype(str).str.strip().str.title()
                df_grafico_ferias = df_grafico_ferias[df_grafico_ferias['FÉRIAS 2026'] != '']
                df_grafico_ferias = df_grafico_ferias[df_grafico_ferias['FÉRIAS 2026'] != 'Nan']
                
                if not df_grafico_ferias.empty:
                    resumo_mes = df_grafico_ferias.groupby('FÉRIAS 2026').size().reset_index(name='Operadores Ausentes')
                    ordem_meses = {mes: i for i, mes in enumerate(MESES)}
                    resumo_mes['Ordem'] = resumo_mes['FÉRIAS 2026'].map(ordem_meses)
                    resumo_mes = resumo_mes.sort_values('Ordem').drop('Ordem', axis=1)

                    fig_ferias = px.bar(resumo_mes, x='FÉRIAS 2026', y='Operadores Ausentes', text='Operadores Ausentes', title="📊 Distribuição de Férias Programadas (Por Mês)", color_discrete_sequence=['#1e88e5'])
                    fig_ferias.update_traces(textposition='auto', textfont_size=16, textfont_color="white")
                    st.plotly_chart(fig_ferias, use_container_width=True)
                else: st.info("Nenhuma programação de férias lançada até o momento.")
                
                st.markdown("---")
                st.markdown("#### ✏️ Lançamento Rápido de Férias")
                st.info("As alterações feitas nesta tabela atualizam automaticamente a base mestre (sem o risco de mexer nas senhas).")
                
                colunas_ferias = ['COLABORADOR', 'STATUS', 'FÉRIAS 2026']
                df_edicao_ferias = df_ferias[colunas_ferias].copy()
                df_ferias_salvo = st.data_editor(df_edicao_ferias, num_rows="dynamic", use_container_width=True, key="ed_ferias_rapida")
                
                if st.button("💾 Salvar Calendário de Férias", type="primary"):
                    df_ferias['STATUS'] = df_ferias_salvo['STATUS']
                    df_ferias['FÉRIAS 2026'] = df_ferias_salvo['FÉRIAS 2026']
                    enviar_para_github("dados_usuarios.csv", df_ferias.to_csv(index=False))
                    st.cache_data.clear()
                    st.success("Férias atualizadas com sucesso!")
                    time.sleep(0.5)
                    st.rerun()
            except Exception: st.warning("Base de usuários indisponível.")
            
        with aba_relatorio:
            st.header("📑 Relatório Executivo para a Diretoria")
            st.markdown("Visão consolidada da operação (Últimos 6 meses) com todos os indicadores solicitados e análise volumétrica.")
            
            if base_mestre_existe and not df_completo.empty:
                df_rel = df_completo.copy()
                
                def get_status_relatorio(row):
                    if str(row.get('STATUS', 'ATIVO')).strip().upper() == 'AFASTADO': return 'Afastado'
                    mes_ferias = str(row.get('FÉRIAS 2026', '')).strip().upper()
                    if mes_ferias == str(row.get('text_mes', '')).strip().upper(): return 'Férias'
                    return 'Ativo'
                
                df_rel['Status_Dinamico'] = df_rel.apply(get_status_relatorio, axis=1)
                
                cols_to_num = ['Total_Pesq_CSAT', 'Boas_Pesq_CSAT', 'Total_Pesq_IR', 'Sim_Pesq_IR', 'RT geral valido', 'RT geral calculado', 'Faltas', 'Aderência (%)', 'Conformidade (%)', 'Taxa_Retencao_Original']
                for c in cols_to_num:
                    if c in df_rel.columns:
                        df_rel[c] = pd.to_numeric(df_rel[c], errors='coerce').fillna(0)
                    else:
                        df_rel[c] = 0.0
                
                df_rel['Faltas'] = df_rel.apply(lambda r: r['Faltas'] if r['Status_Dinamico'] == 'Ativo' else 0, axis=1)
                
                meses_map = {m: i for i, m in enumerate(MESES, 1)}
                df_rel['Mes_Num'] = df_rel['Mês'].str.title().map(meses_map)
                df_rel = df_rel.dropna(subset=['Mes_Num'])
                df_rel['Ordem'] = df_rel['Ano'].astype(str) + "-" + df_rel['Mes_Num'].astype(int).astype(str).str.zfill(2)
                
                df_rel_agg = df_rel.groupby(['Ordem', 'Mês', 'Ano']).agg({
                    'RT geral valido': 'sum',
                    'RT geral calculado': 'sum',
                    'Faltas': 'sum',
                    'Total_Pesq_CSAT': 'sum',
                    'Boas_Pesq_CSAT': 'sum',
                    'Total_Pesq_IR': 'sum',
                    'Sim_Pesq_IR': 'sum',
                    'Aderência (%)': 'mean',
                    'Conformidade (%)': 'mean'
                }).reset_index().sort_values('Ordem').tail(6) 
                
                df_rel_agg['Taxa Retenção (%)'] = df_rel_agg.apply(lambda r: (r['RT geral valido'] / r['RT geral calculado'] * 100) if r['RT geral calculado'] > 0 else 0, axis=1)
                df_rel_agg['CSAT (%)'] = df_rel_agg.apply(lambda r: (r['Boas_Pesq_CSAT'] / r['Total_Pesq_CSAT'] * 100) if r['Total_Pesq_CSAT'] > 0 else 0, axis=1)
                df_rel_agg['Índice IR (%)'] = df_rel_agg.apply(lambda r: (r['Sim_Pesq_IR'] / r['Total_Pesq_IR'] * 100) if r['Total_Pesq_IR'] > 0 else 0, axis=1)
                
                df_final_rel = pd.DataFrame()
                df_final_rel['Período'] = df_rel_agg['Mês'].astype(str).str.title() + "/" + df_rel_agg['Ano'].astype(str)
                df_final_rel['Taxa de Retenção'] = df_rel_agg['Taxa Retenção (%)']
                df_final_rel['Total Oportunidades Retenção'] = df_rel_agg['RT geral calculado']
                df_final_rel['Retenções Realizadas (Vol)'] = df_rel_agg['RT geral valido']
                df_final_rel['Absenteísmo (Faltas)'] = df_rel_agg['Faltas']
                df_final_rel['Conformidade Média'] = df_rel_agg['Conformidade (%)']
                df_final_rel['Aderência Média'] = df_rel_agg['Aderência (%)']
                df_final_rel['CSAT Média'] = df_rel_agg['CSAT (%)']
                df_final_rel['Total Avaliações CSAT'] = df_rel_agg['Total_Pesq_CSAT']
                df_final_rel['Índice IR Média'] = df_rel_agg['Índice IR (%)']
                df_final_rel['Total Pesquisas IR'] = df_rel_agg['Total_Pesq_IR']
                
                st.dataframe(df_final_rel.style.format({
                    'Taxa de Retenção': '{:.2f}%',
                    'Total Oportunidades Retenção': '{:.0f}',
                    'Retenções Realizadas (Vol)': '{:.0f}',
                    'Absenteísmo (Faltas)': '{:.0f}',
                    'Conformidade Média': '{:.2f}%',
                    'Aderência Média': '{:.2f}%',
                    'CSAT Média': '{:.2f}%',
                    'Total Avaliações CSAT': '{:.0f}',
                    'Índice IR Média': '{:.2f}%',
                    'Total Pesquisas IR': '{:.0f}'
                }), use_container_width=True)
                
                st.markdown("---")
                st.subheader("📊 Painel de Visualização Gráfica")
                
                tab_g1, tab_g2, tab_g3 = st.tabs(["📉 Qualidade e Retenção (%)", "📉 Processos e Escala (%)", "📈 Volumetria Absoluta (Amostras)"])
                
                with tab_g1:
                    df_melt_pct1 = df_final_rel.melt(id_vars='Período', value_vars=['Taxa de Retenção', 'CSAT Média', 'Índice IR Média'], var_name='Indicador', value_name='Valor (%)')
                    fig_pct1 = px.line(df_melt_pct1, x='Período', y='Valor (%)', color='Indicador', markers=True, text='Valor (%)', title="Evolução de Qualidade e Retenção (%)")
                    fig_pct1.update_traces(textposition="top center", texttemplate='%{text:.1f}%')
                    fig_pct1.update_yaxes(range=[0, 105])
                    st.plotly_chart(fig_pct1, use_container_width=True)

                with tab_g2:
                    df_melt_pct2 = df_final_rel.melt(id_vars='Período', value_vars=['Conformidade Média', 'Aderência Média'], var_name='Indicador', value_name='Valor (%)')
                    fig_pct2 = px.line(df_melt_pct2, x='Período', y='Valor (%)', color='Indicador', markers=True, text='Valor (%)', title="Evolução de Processos (%)", color_discrete_sequence=['#9932cc', '#ba55d3'])
                    fig_pct2.update_traces(textposition="top center", texttemplate='%{text:.1f}%')
                    fig_pct2.update_yaxes(range=[0, 105])
                    st.plotly_chart(fig_pct2, use_container_width=True)

                with tab_g3:
                    df_melt_vol = df_final_rel.melt(id_vars='Período', value_vars=['Total Oportunidades Retenção', 'Retenções Realizadas (Vol)', 'Total Avaliações CSAT', 'Absenteísmo (Faltas)'], var_name='Métrica', value_name='Volume')
                    fig_vol = px.bar(df_melt_vol, x='Período', y='Volume', color='Métrica', barmode='group', text='Volume', title="Volumetria Absoluta da Operação", color_discrete_sequence=['#ffc107', '#28a745', '#17a2b8', '#dc3545'])
                    fig_vol.update_traces(textposition="outside", texttemplate='%{y:.0f}')
                    st.plotly_chart(fig_vol, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 📝 Resumo Rápido (Copiar e Colar)")
                st.info("Copie o texto abaixo e envie diretamente para a sua gerência/diretoria.")
                
                if not df_final_rel.empty:
                    texto_resumo = f"📊 *Análise Operacional Consolidada - Últimos {len(df_final_rel)} Meses:*\n\n"
                    for _, row in df_final_rel.iterrows():
                        texto_resumo += f"🔹 *{row['Período']}*\n"
                        texto_resumo += f"- Taxa de Retenção: {row['Taxa de Retenção']:.2f}% (Salvou {row['Retenções Realizadas (Vol)']:.0f} de {row['Total Oportunidades Retenção']:.0f} clientes)\n"
                        texto_resumo += f"- Absenteísmo: {row['Absenteísmo (Faltas)']:.0f} faltas registradas\n"
                        texto_resumo += f"- Qualidade (CSAT): {row['CSAT Média']:.1f}% (Baseado em {row['Total Avaliações CSAT']:.0f} avaliações)\n"
                        texto_resumo += f"- Índice de Resolução (IR): {row['Índice IR Média']:.1f}% (Baseado em {row['Total Pesquisas IR']:.0f} avaliações)\n"
                        texto_resumo += f"- Processos (Conf. / Aderência): {row['Conformidade Média']:.1f}% / {row['Aderência Média']:.1f}%\n\n"
                    
                    st.text_area("Texto do E-mail/Mensagem:", texto_resumo, height=250)
                
                csv_export = df_final_rel.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar Tabela em CSV (Excel)",
                    data=csv_export,
                    file_name="relatorio_gerencial_6_meses.csv",
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.info("Não há dados históricos suficientes para gerar o relatório consolidado.")

        with aba_feedback:
            st.header("📈 Avaliação de Desempenho e Feedback Contínuo")
            st.markdown("Mapeamento de calor para identificar operadores com desvios crônicos de performance ao longo do tempo selecionado.")
            
            if base_mestre_existe and not df_completo.empty:
                df_feed = df_completo.copy()
                
                if 'Periodo_Competencia' not in df_feed.columns:
                    df_feed['Periodo_Competencia'] = df_feed['text_mes'].str.title() + "/" + df_feed['text_ano']
                    
                meses_map_feed = {m: i for i, m in enumerate(MESES, 1)}
                df_feed['Mes_Num'] = df_feed['text_mes'].map(meses_map_feed)
                df_feed = df_feed.dropna(subset=['Mes_Num'])
                df_feed['Ordem_Feed'] = df_feed['text_ano'].astype(str) + "-" + df_feed['Mes_Num'].astype(int).astype(str).str.zfill(2)
                
                periodos_disponiveis = df_feed.sort_values('Ordem_Feed', ascending=False)['Periodo_Competencia'].unique().tolist()
                
                st.markdown("#### ⏳ Selecione o Período de Avaliação")
                periodos_selecionados = st.multiselect("Filtre um ou múltiplos meses para gerar a média consolidada (ex: Último Trimestre):", periodos_disponiveis, default=periodos_disponiveis[:3] if len(periodos_disponiveis) >= 3 else periodos_disponiveis)
                
                if not periodos_selecionados:
                    st.warning("Selecione pelo menos um mês para gerar o relatório.")
                else:
                    df_feed_filtrado = df_feed[df_feed['Periodo_Competencia'].isin(periodos_selecionados)].copy()
                    
                    # APLICA LIMPEZA DOS NOMES ANTES DO GROUPBY PARA EVITAR DUPLICADOS COMO "FRANCISCO EVERTON" e "FRANCISCO EVERTON "
                    df_feed_filtrado['Nome Exibição'] = df_feed_filtrado['Nome Exibição'].apply(limpar_nome_duplo)
                    
                    cols_to_num = ['Total_Pesq_CSAT', 'Boas_Pesq_CSAT', 'Total_Pesq_IR', 'Sim_Pesq_IR', 'RT geral valido', 'RT geral calculado', 'Faltas', 'Aderência (%)', 'Conformidade (%)']
                    for c in cols_to_num:
                        if c in df_feed_filtrado.columns:
                            df_feed_filtrado[c] = pd.to_numeric(df_feed_filtrado[c], errors='coerce').fillna(0)
                        else:
                            df_feed_filtrado[c] = 0.0
                            
                    df_feed_agg = df_feed_filtrado.groupby('Nome Exibição').agg({
                        'Total_Pesq_CSAT': 'sum',
                        'Boas_Pesq_CSAT': 'sum',
                        'Total_Pesq_IR': 'sum',
                        'Sim_Pesq_IR': 'sum',
                        'RT geral valido': 'sum',
                        'RT geral calculado': 'sum',
                        'Faltas': 'sum',
                        'Aderência (%)': 'mean',
                        'Conformidade (%)': 'mean'
                    }).reset_index()
                    
                    # FILTRO ANTI-FANTASMA: Remove quem está zerado em TODOS os indicadores vitais no período
                    mask_tem_dados = (df_feed_agg['RT geral calculado'] > 0) | (df_feed_agg['Aderência (%)'] > 0) | (df_feed_agg['Conformidade (%)'] > 0) | (df_feed_agg['Faltas'] > 0)
                    df_feed_agg = df_feed_agg[mask_tem_dados].copy()
                    
                    df_feed_agg['CSAT Média (%)'] = df_feed_agg.apply(lambda r: (r['Boas_Pesq_CSAT'] / r['Total_Pesq_CSAT'] * 100) if r['Total_Pesq_CSAT'] > 0 else 0, axis=1)
                    df_feed_agg['IR Média (%)'] = df_feed_agg.apply(lambda r: (r['Sim_Pesq_IR'] / r['Total_Pesq_IR'] * 100) if r['Total_Pesq_IR'] > 0 else 0, axis=1)
                    df_feed_agg['Retenção Média (%)'] = df_feed_agg.apply(lambda r: (r['RT geral valido'] / r['RT geral calculado'] * 100) if r['RT geral calculado'] > 0 else 0, axis=1)
                    
                    # Regras de Alerta (Onde a pessoa precisa melhorar?)
                    def checar_alertas(row):
                        alertas = []
                        if row['Total_Pesq_CSAT'] > 0 and row['CSAT Média (%)'] < META_CSAT: alertas.append("⭐ CSAT")
                        if row['Total_Pesq_IR'] > 0 and row['IR Média (%)'] < META_IR: alertas.append("🎯 IR")
                        if row['RT geral calculado'] > 0 and row['Retenção Média (%)'] < META_RETENCAO: alertas.append("📈 Retenção")
                        if row['Aderência (%)'] > 0 and row['Aderência (%)'] < META_ADERENCIA: alertas.append("⏱️ Aderência")
                        if row['Conformidade (%)'] > 0 and row['Conformidade (%)'] < META_CONFORMIDADE: alertas.append("📅 Conformidade")
                        if row['Faltas'] > 0: alertas.append("❌ Faltas")
                        
                        if len(alertas) == 0 and row['RT geral calculado'] == 0 and row['Aderência (%)'] == 0:
                            return "⚪ Sem Dados Relevantes"
                            
                        return ", ".join(alertas) if alertas else "✅ Dentro da Meta"
                        
                    def contar_alertas(row):
                        if row['Indicadores Críticos'] in ["✅ Dentro da Meta", "⚪ Sem Dados Relevantes"]: return 0
                        return len(row['Indicadores Críticos'].split(","))

                    df_feed_agg['Indicadores Críticos'] = df_feed_agg.apply(checar_alertas, axis=1)
                    df_feed_agg['Qtd. Alertas'] = df_feed_agg.apply(contar_alertas, axis=1)
                    
                    df_feed_agg = df_feed_agg.sort_values(by=['Qtd. Alertas', 'Retenção Média (%)'], ascending=[False, True])
                    
                    colunas_feed_mostrar = ['Nome Exibição', 'Qtd. Alertas', 'Indicadores Críticos', 'Retenção Média (%)', 'Faltas', 'CSAT Média (%)', 'IR Média (%)', 'Aderência (%)', 'Conformidade (%)']
                    df_feed_exibir = df_feed_agg[colunas_feed_mostrar].copy()
                    
                    def cor_alerta(val):
                        if val >= 3: return 'color: white; background-color: #dc3545; font-weight: bold;'
                        elif val >= 1: return 'color: #856404; background-color: #fff3cd; font-weight: bold;'
                        return 'color: #155724; background-color: #d4edda;'
                        
                    st.markdown("---")
                    
                    total_atencao = len(df_feed_exibir[df_feed_exibir['Qtd. Alertas'] >= 3])
                    total_ok = len(df_feed_exibir[df_feed_exibir['Indicadores Críticos'] == '✅ Dentro da Meta'])
                    
                    c_f1, c_f2 = st.columns(2)
                    with c_f1:
                        st.markdown(f"<div class='kpi-card' style='border-left-color: #dc3545;'><div class='kpi-title'>Zona de Risco (Feedback Urgente)</div><div class='kpi-value' style='color:#dc3545;'>{total_atencao} Operadores</div><div style='font-size:11px;color:#6c757d;'>Falhando em 3 ou mais indicadores na média do período</div></div>", unsafe_allow_html=True)
                    with c_f2:
                        st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Alta Performance (Constância)</div><div class='kpi-value' style='color:#28a745;'>{total_ok} Operadores</div><div style='font-size:11px;color:#6c757d;'>Batendo todas as metas dentro do período selecionado</div></div>", unsafe_allow_html=True)

                    st.markdown("#### 🚨 Mapeamento de Risco por Operador")
                    st.markdown("Esta tabela já está classificada para mostrar os operadores com maior quantidade de alertas no topo. Utilize os pontos apontados em **Indicadores Críticos** para criar um Plano de Ação Personalizado (PDI) ou justificar eventuais desligamentos.")
                    
                    st.dataframe(df_feed_exibir.style.map(cor_alerta, subset=['Qtd. Alertas']).format({
                        'Retenção Média (%)': '{:.2f}%',
                        'Faltas': '{:.0f}',
                        'CSAT Média (%)': '{:.1f}%',
                        'IR Média (%)': '{:.1f}%',
                        'Aderência (%)': '{:.1f}%',
                        'Conformidade (%)': '{:.1f}%'
                    }), use_container_width=True)
                    
                    csv_feed = df_feed_exibir.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Exportar Lista de Acompanhamento (CSV)",
                        data=csv_feed,
                        file_name="relatorio_feedbacks_desligamentos.csv",
                        mime="text/csv",
                        type="secondary"
                    )
            else:
                st.info("Nenhum dado consolidado encontrado para gerar as avaliações.")

        with aba_upload:
            st.header("⚙️ Central de Consolidação de Relatórios")
            
            col_m, col_a = st.columns(2)
            mes_up = col_m.selectbox("Mês de competência das planilhas:", MESES, index=4)
            ano_up = col_a.selectbox("Ano de competência das planilhas:", ANOS)
            st.markdown("---")
            
            arquivos_carregados = st.file_uploader("Arraste e solte os 7 arquivos CSV aqui de uma vez", type=["csv"], accept_multiple_files=True)
            relatorios_identificados = {"Aderência e Conformidade": None, "Faltas Diárias": None, "Pesquisa (CSAT/IR)": None, "Chat": None, "Voz": None, "Retenção": None, "Gamificação": None}
            if arquivos_carregados:
                for arquivo in arquivos_carregados:
                    try:
                        df_header = ler_csv_upload_seguro(arquivo, nrows=0)
                        cols_upper = [str(c).strip().upper() for c in df_header.columns]
                        
                        if any('ADER' in c for c in cols_upper) and any('CONFOR' in c for c in cols_upper) and not any('SINALIZADOR' in c for c in cols_upper):
                            relatorios_identificados["Aderência e Conformidade"] = arquivo
                        elif any('SINALIZADOR' in c for c in cols_upper) and any('DATA' in c for c in cols_upper):
                            relatorios_identificados["Faltas Diárias"] = arquivo
                        elif any('CSAT' in c for c in cols_upper) and any('ATENDENTE' in c for c in cols_upper):
                            relatorios_identificados["Pesquisa (CSAT/IR)"] = arquivo
                        elif any('ATENDIDAS' in c for c in cols_upper) and any('NOME DO AGENTE' in c for c in cols_upper):
                            if "CHAT" in arquivo.name.upper(): relatorios_identificados["Chat"] = arquivo
                            else: relatorios_identificados["Voz"] = arquivo
                        elif any('RESPONSAVEL' in c for c in cols_upper) and any('RETEN' in c for c in cols_upper):
                            relatorios_identificados["Retenção"] = arquivo
                        elif any('DIAMANTES' in c for c in cols_upper) and any('COLABORADOR' in c for c in cols_upper):
                            relatorios_identificados["Gamificação"] = arquivo
                    except Exception: pass

            st.markdown("### 📋 Status da Validação")
            c_chk1, c_chk2, c_chk3, c_chk4, c_chk5, c_chk6, c_chk7 = st.columns(7)
            with c_chk1: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Aderência e Conformidade'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>1. Ade & Conf</b></div>", unsafe_allow_html=True)
            with c_chk2: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Faltas Diárias'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>2. Faltas WFM</b></div>", unsafe_allow_html=True)
            with c_chk3: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Pesquisa (CSAT/IR)'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>3. Pesquisas</b></div>", unsafe_allow_html=True)
            with c_chk4: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Chat'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>4. Chat</b></div>", unsafe_allow_html=True)
            with c_chk5: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Voz'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>5. Voz</b></div>", unsafe_allow_html=True)
            with c_chk6: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Retenção'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>6. Retenção</b></div>", unsafe_allow_html=True)
            with c_chk7: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Gamificação'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>7. Gamificação</b></div>", unsafe_allow_html=True)

            if all(relatorios_identificados.values()) and st.button("🚀 Processar e Atualizar Base Mestre AGORA", type="primary", use_container_width=True):
                with st.spinner("Consolidando..."):
                    try:
                        df_perf = ler_csv_upload_seguro(relatorios_identificados["Aderência e Conformidade"])
                        df_faltas_diarias = ler_csv_upload_seguro(relatorios_identificados["Faltas Diárias"])
                        df_ret = ler_csv_upload_seguro(relatorios_identificados["Retenção"])
                        df_chat = ler_csv_upload_seguro(relatorios_identificados["Chat"])
                        df_voz = ler_csv_upload_seguro(relatorios_identificados["Voz"])
                        df_pesq = ler_csv_upload_seguro(relatorios_identificados["Pesquisa (CSAT/IR)"])
                        df_gam = ler_csv_upload_seguro(relatorios_identificados["Gamificação"])
                        df_users = ler_csv_via_api_github("dados_usuarios.csv")
                        
                        col_nome = 'COLABORADOR' if 'COLABORADOR' in df_users.columns else 'Nome'
                        
                        # Limpa chaves na Base de Usuários para criar a lista Mestre
                        df_users['Chave_Nome'] = df_users[col_nome].astype(str).str.strip().str.upper()
                        df_users['Chave_Nome'] = df_users['Chave_Nome'].apply(limpar_nome_duplo)
                        df_users = df_users.drop_duplicates(subset=['Chave_Nome'], keep='first')
                        nomes_mestre = df_users['Chave_Nome'].tolist()

                        def buscar_melhor_match(nome):
                            if pd.isna(nome) or str(nome).strip() == "": return str(nome)
                            nome = " ".join(str(nome).strip().split()).upper()
                            if nome in nomes_mestre: return nome
                            for nm in nomes_mestre:
                                if nome in nm or nm in nome: return nm
                            partes = nome.split()
                            if len(partes) >= 2:
                                for nm in nomes_mestre:
                                    pm = nm.split()
                                    if len(pm) >= 2 and partes[0] == pm[0] and partes[-1] == pm[-1]: return nm
                                for nm in nomes_mestre:
                                    pm = nm.split()
                                    if len(pm) >= 2 and partes[0] == pm[0] and partes[1] == pm[1]: return nm
                            return nome

                        # Processamento Performance
                        col_ade = next((c for c in df_perf.columns if 'ADER' in str(c).upper()), None)
                        col_conf = next((c for c in df_perf.columns if 'CONFOR' in str(c).upper()), None)
                        col_agente = next((c for c in df_perf.columns if 'AGENTE' in str(c).upper()), None)
                        
                        df_perf['Aderência (%)'] = df_perf[col_ade].apply(limpar_porcentagem)
                        df_perf['Conformidade (%)'] = df_perf[col_conf].apply(limpar_porcentagem)
                        df_perf['Chave_Nome'] = df_perf[col_agente].apply(buscar_melhor_match)
                        df_perf_agg = df_perf.groupby('Chave_Nome').agg({'Aderência (%)': 'mean', 'Conformidade (%)': 'mean'}).reset_index()

                        # Processamento Faltas
                        col_agente_falta = next((c for c in df_faltas_diarias.columns if 'AGENTE' in str(c).upper()), None)
                        col_conf_falta = next((c for c in df_faltas_diarias.columns if 'CONFOR' in str(c).upper()), None)
                        
                        df_faltas_diarias['Chave_Nome'] = df_faltas_diarias[col_agente_falta].apply(buscar_melhor_match)
                        df_faltas_diarias['Valor_Conformidade'] = pd.to_numeric(df_faltas_diarias[col_conf_falta].astype(str).str.replace(',', '.'), errors='coerce')
                        df_faltas_diarias['Falta_Dia'] = (df_faltas_diarias['Valor_Conformidade'] == 0.0).astype(int)
                        
                        df_faltas_agg = df_faltas_diarias.groupby('Chave_Nome').agg({'Falta_Dia': 'sum'}).reset_index()
                        df_faltas_agg.rename(columns={'Falta_Dia': 'Faltas'}, inplace=True)
                        
                        # Processamento Retenção
                        df_ret['Chave_Nome'] = df_ret['responsavel'].apply(buscar_melhor_match)
                        df_ret['Taxa_Retencao_Original'] = df_ret['% de retenção'].apply(limpar_porcentagem)
                        df_ret['RT geral valido'] = pd.to_numeric(df_ret['RT geral valido'], errors='coerce').fillna(0)
                        df_ret['RT geral calculado'] = df_ret.apply(lambda row: (row['RT geral valido'] / (row['Taxa_Retencao_Original'] / 100)) if row['Taxa_Retencao_Original'] > 0 else row['RT geral valido'], axis=1).fillna(0)
                        
                        col_rt_fibra = next((c for c in df_ret.columns if 'FIBRA' in str(c).upper() and 'VALID' in str(c).upper()), None)
                        if not col_rt_fibra: col_rt_fibra = next((c for c in df_ret.columns if 'FIBRA' in str(c).upper()), None)
                        col_rt_adic = next((c for c in df_ret.columns if 'ADICIONAL' in str(c).upper() and 'VALID' in str(c).upper()), None)
                        
                        df_ret['RT_Fibra_Validas'] = pd.to_numeric(df_ret[col_rt_fibra], errors='coerce').fillna(0) if col_rt_fibra else pd.to_numeric(df_ret['RT geral valido'], errors='coerce').fillna(0)
                        df_ret['RT_Adicional_Validas'] = pd.to_numeric(df_ret[col_rt_adic], errors='coerce').fillna(0) if col_rt_adic else 0
                        
                        df_ret_agg = df_ret.groupby('Chave_Nome').agg({
                            'RT geral valido': 'sum',
                            'RT geral calculado': 'sum',
                            'Taxa_Retencao_Original': 'mean',
                            'RT_Fibra_Validas': 'sum',
                            'RT_Adicional_Validas': 'sum'
                        }).reset_index()

                        # Processamento Gamificação
                        col_gam_colab = next((c for c in df_gam.columns if 'COLABORADOR' in str(c).upper()), None)
                        col_gam_diam = next((c for c in df_gam.columns if 'DIAMANTES' in str(c).upper()), None)
                        df_gam['Chave_Nome'] = df_gam[col_gam_colab].apply(buscar_melhor_match)
                        df_gam['Diamantes'] = pd.to_numeric(df_gam[col_gam_diam], errors='coerce').fillna(0)
                        df_gam_agg = df_gam.groupby('Chave_Nome').agg({'Diamantes': 'sum'}).reset_index()

                        # Processamento Chat
                        df_chat['Chave_Nome'] = df_chat['Nome do agente'].apply(buscar_melhor_match)
                        col_tpc_chat = next((c for c in df_chat.columns if any(x in str(c).upper() for x in ['TPC', 'PÓS', 'POS', 'TRABALHO'])), None)
                        agg_chat = {'Atendidas': 'sum', 'Tratamento médio': 'mean'}
                        if col_tpc_chat: agg_chat[col_tpc_chat] = 'mean'
                        
                        df_chat_agg = df_chat.groupby('Chave_Nome').agg(agg_chat).reset_index()
                        df_chat_agg.rename(columns={'Atendidas': 'Vol. Chat', 'Tratamento médio': 'TMA Chat (ms)'}, inplace=True)
                        df_chat_agg['TMA Chat (Min)'] = df_chat_agg['TMA Chat (ms)'].apply(ms_para_minutos)
                        if col_tpc_chat:
                            df_chat_agg.rename(columns={col_tpc_chat: 'TPC Chat (ms)'}, inplace=True)
                            df_chat_agg['TPC Chat (Seg)'] = df_chat_agg['TPC Chat (ms)'].apply(ms_para_segundos)
                        
                        # Processamento Voz
                        df_voz['Chave_Nome'] = df_voz['Nome do agente'].apply(buscar_melhor_match)
                        col_tpc_voz = next((c for c in df_voz.columns if any(x in str(c).upper() for x in ['TPC', 'PÓS', 'POS', 'TRABALHO'])), None)
                        agg_voz = {'Atendidas': 'sum', 'Tratamento médio': 'mean'}
                        if col_tpc_voz: agg_voz[col_tpc_voz] = 'mean'
                        
                        df_voz_agg = df_voz.groupby('Chave_Nome').agg(agg_voz).reset_index()
                        df_voz_agg.rename(columns={'Atendidas': 'Vol. Voz', 'Tratamento médio': 'TMA Voz (ms)'}, inplace=True)
                        df_voz_agg['TMA Voz (Min)'] = df_voz_agg['TMA Voz (ms)'].apply(ms_para_minutos)
                        if col_tpc_voz:
                            df_voz_agg.rename(columns={col_tpc_voz: 'TPC Voz (ms)'}, inplace=True)
                            df_voz_agg['TPC Voz (Seg)'] = df_voz_agg['TPC Voz (ms)'].apply(ms_para_segundos)
                        
                        # Processamento Pesquisa
                        df_pesq['Chave_Nome'] = df_pesq['Atendente'].apply(buscar_melhor_match)
                        df_pesq['CSAT_Num'] = pd.to_numeric(df_pesq['CSAT'], errors='coerce')
                        df_pesq_agg = df_pesq.groupby('Chave_Nome').agg(Total_Pesq_CSAT=('CSAT_Num', 'count'), Boas_Pesq_CSAT=('CSAT_Num', lambda x: (x >= 4).sum()), Total_Pesq_IR=('IR', 'count'), Sim_Pesq_IR=('IR', lambda x: (x.astype(str).str.strip().str.upper() == 'SIM').sum())).reset_index()

                        # Merge Final Seguro
                        df_novo = pd.merge(df_users, df_perf_agg, on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_faltas_agg, on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_ret_agg, on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_chat_agg, on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_voz_agg, on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_pesq_agg, on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_gam_agg, on='Chave_Nome', how='left')
                        
                        df_novo['Nome Exibição'] = df_novo['Chave_Nome'].apply(limpar_nome_duplo)
                        df_novo['Mês'] = mes_up
                        df_novo['Ano'] = str(ano_up)
                        
                        if 'TPC Chat (Seg)' not in df_novo.columns: df_novo['TPC Chat (Seg)'] = 0.0
                        if 'TPC Voz (Seg)' not in df_novo.columns: df_novo['TPC Voz (Seg)'] = 0.0
                        if 'Faltas' not in df_novo.columns: df_novo['Faltas'] = 0
                        if 'RT_Fibra_Validas' not in df_novo.columns: df_novo['RT_Fibra_Validas'] = 0.0
                        if 'RT_Adicional_Validas' not in df_novo.columns: df_novo['RT_Adicional_Validas'] = 0.0
                        if 'Diamantes' not in df_novo.columns: df_novo['Diamantes'] = 0
                        
                        try:
                            df_master_existente = ler_csv_via_api_github("dados_consolidados_master.csv")
                        except Exception:
                            df_master_existente = pd.DataFrame()
                            
                        if not df_master_existente.empty:
                            df_master_existente['M_temp'] = df_master_existente['Mês'].astype(str).str.strip().str.title()
                            df_master_existente['A_temp'] = df_master_existente['Ano'].astype(str).str.strip()
                            mask_diferente = ~((df_master_existente['M_temp'] == mes_up) & (df_master_existente['A_temp'] == str(ano_up)))
                            df_master_existente = df_master_existente[mask_diferente].drop(columns=['M_temp', 'A_temp', 'text_mes', 'text_ano'], errors='ignore')
                            if 'Diamantes' not in df_master_existente.columns: df_master_existente['Diamantes'] = 0
                            df_final_salvar = pd.concat([df_master_existente, df_novo], ignore_index=True)
                        else:
                            df_final_salvar = df_novo
                            
                        if 'TPC Chat (Seg)' not in df_final_salvar.columns: df_final_salvar['TPC Chat (Seg)'] = 0.0
                        if 'TPC Voz (Seg)' not in df_final_salvar.columns: df_final_salvar['TPC Voz (Seg)'] = 0.0
                        if 'Faltas' not in df_final_salvar.columns: df_final_salvar['Faltas'] = 0
                        if 'Diamantes' not in df_final_salvar.columns: df_final_salvar['Diamantes'] = 0
                        
                        enviar_para_github("dados_consolidados_master.csv", df_final_salvar.to_csv(index=False))
                        st.cache_data.clear()
                        obter_ultima_atualizacao.clear()
                        st.success(f"Relatórios de {mes_up}/{ano_up} integrados ao Histórico Geral com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e: st.error(f"Erro no processamento: {e}")

        with aba_dashboard:
            if not base_mestre_existe: st.warning("📢 Base mestre indisponível.")
            elif not dados_carregados: st.warning(f"⚠️ {erro_dados}")
            else:
                modo_visao = st.radio("Filtro de Quadro Operacional:", ["Mostrar Apenas Ativos", "Mostrar Todos (Incluir Férias/Afastados do Período)"], horizontal=True)
                
                if modo_visao == "Mostrar Apenas Ativos": df_calculado = df_periodo_mapeado[df_periodo_mapeado['Status_Dinamico'] == 'Ativo'].copy()
                else: df_calculado = df_periodo_mapeado.copy()

                if 'Total_Pesq_CSAT' in df_calculado.columns:
                    df_calculado['CSAT_Agente (%)'] = (df_calculado['Boas_Pesq_CSAT'] / df_calculado['Total_Pesq_CSAT'] * 100).fillna(0)
                    df_calculado['IR_Agente (%)'] = (df_calculado['Sim_Pesq_IR'] / df_calculado['Total_Pesq_IR'] * 100).fillna(0)
                else:
                    df_calculado['CSAT_Agente (%)'] = df_calculado['CSAT_Media'].fillna(0)
                    df_calculado['IR_Agente (%)'] = df_calculado['IR_Percentual'].fillna(0)
                
                df_calculado['% Retenção'] = df_calculado['Taxa_Retencao_Original'].fillna(0) if 'Taxa_Retencao_Original' in df_calculado.columns else 0.0
                df_calculado['% Cancelamento'] = df_calculado.apply(lambda r: 100 - r['% Retenção'] if r['% Retenção'] > 0 else 0.0, axis=1)
                
                df_calculado['Faltas'] = df_calculado.apply(lambda r: r.get('Faltas', 0) if r.get('Status_Dinamico') == 'Ativo' else 0, axis=1)

                df_calculado = df_calculado[
                    (df_calculado['Aderência (%)'] > 0) | 
                    (df_calculado['Conformidade (%)'] > 0) | 
                    (df_calculado['Vol. Chat'] > 0) | 
                    (df_calculado['Vol. Voz'] > 0) |
                    (df_calculado['Faltas'] > 0)
                ].copy()
                
                # APLICA CÁLCULO DE COMISSÃO E GAMIFICAÇÃO
                if 'Diamantes' not in df_calculado.columns: df_calculado['Diamantes'] = 0
                df_calculado['Comissão (R$)'] = df_calculado.apply(lambda r: calcular_comissao_rv(
                    r.get('% Retenção', 0.0),
                    r.get('RT_Fibra_Validas', 0.0),
                    r.get('RT_Adicional_Validas', 0.0),
                    r.get('Diamantes', 0)
                ), axis=1)

                st.subheader(f"🚨 Auditoria de Desvios de Metas Contratuais ({mes_view}/{ano_view})")
                df_ativos_alertas = df_calculado[df_calculado['Status_Dinamico'] == 'Ativo']
                
                lista_detratores_csat = df_ativos_alertas[df_ativos_alertas['CSAT_Agente (%)'] < META_CSAT]
                lista_detratores_ir = df_ativos_alertas[df_ativos_alertas['IR_Agente (%)'] < META_IR]
                detratores_retencao = df_ativos_alertas[df_ativos_alertas['% Retenção'] < META_RETENCAO]
                lista_detratores_conf = df_ativos_alertas[df_ativos_alertas['Conformidade (%)'] < META_CONFORMIDADE]
                lista_detratores_ade = df_ativos_alertas[df_ativos_alertas['Aderência (%)'] < META_ADERENCIA]
                lista_detratores_faltas = df_ativos_alertas[df_ativos_alertas['Faltas'] > 0]
                
                total_desvios_qualidade = len(lista_detratores_csat) + len(lista_detratores_ir)
                total_faltas_alertas = int(lista_detratores_faltas['Faltas'].sum()) if not lista_detratores_faltas.empty else 0

                c_a1, c_a2, c_a3, c_a4, c_a5 = st.columns(5)
                with c_a1:
                    with st.expander(f"⭐ Qualidade: {total_desvios_qualidade} desvios"):
                        for _, row in lista_detratores_csat.iterrows(): st.markdown(f"<div class='detractor-box'>⭐ <b>{row['Nome Exibição']}</b> | CSAT: <b>{row['CSAT_Agente (%)']:.1f}%</b></div>", unsafe_allow_html=True)
                        for _, row in lista_detratores_ir.iterrows(): st.markdown(f"<div class='detractor-box'>🎯 <b>{row['Nome Exibição']}</b> | IR: <b>{row['IR_Agente (%)']:.1f}%</b></div>", unsafe_allow_html=True)
                with c_a2:
                    with st.expander(f"📈 Retenção: {len(detratores_retencao)} desvios"):
                        for _, row in detratores_retencao.iterrows(): st.markdown(f"<div class='detractor-box' style='background-color:#fffaf0;border-color:#fbd38d;color:#dd6b20;'>📉 <b>{row['Nome Exibição']}</b> | Ret: <b>{row['% Retenção']:.2f}%</b></div>", unsafe_allow_html=True)
                with c_a3:
                    with st.expander(f"📅 Conformidade (Escala): {len(lista_detratores_conf)} desvios"):
                        for _, row in lista_detratores_conf.iterrows(): st.markdown(f"<div class='detractor-box' style='background-color:#e6fffa;border-color:#319795;color:#234e52;'>📅 <b>{row['Nome Exibição']}</b> | Conf: <b>{row['Conformidade (%)']:.1f}%</b></div>", unsafe_allow_html=True)
                with c_a4:
                    with st.expander(f"⏱️ Aderência (Pausas): {len(lista_detratores_ade)} desvios"):
                        for _, row in lista_detratores_ade.iterrows(): st.markdown(f"<div class='detractor-box' style='background-color:#fffaf5;border-color:#feb2b2;color:#c53030;'>⏱️ <b>{row['Nome Exibição']}</b> | Ade: <b>{row['Aderência (%)']:.1f}%</b></div>", unsafe_allow_html=True)
                with c_a5:
                    with st.expander(f"❌ Faltas: {total_faltas_alertas} ausências"):
                        for _, row in lista_detratores_faltas.iterrows(): st.markdown(f"<div class='detractor-box' style='background-color:#fff5f5;border-color:#feb2b2;color:#c53030;'>❌ <b>{row['Nome Exibição']}</b> | Faltas: <b>{int(row['Faltas'])}</b></div>", unsafe_allow_html=True)

                st.markdown("---")
                
                st.markdown("### 👥 Escopo da Análise")
                agentes_lista = ["Todos"] + list(df_calculado['Nome Exibição'].dropna().unique())
                filtro_agente = st.selectbox("Selecionar foco nominal:", agentes_lista)
                df_final_escopo = df_calculado[df_calculado['Nome Exibição'] == filtro_agente] if filtro_agente != "Todos" else df_calculado.copy()

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
                        col_total_nome = 'RT geral calculado' if 'RT geral calculado' in df_final_escopo.columns else 'RT geral calculado'
                        total_calculado_equipe = df_final_escopo[col_total_nome].sum()
                        v_retencao = (total_rt_valido / total_calculado_equipe * 100) if total_calculado_equipe > 0 else 0.0
                    else: v_retencao = df_final_escopo['Taxa_Retencao_Original'].iloc[0] if not df_final_escopo.empty else 0.0
                else: v_retencao = 0.0

                v_cancelamento = 100 - v_retencao if v_retencao > 0 else 0.0
                total_vol_chat = df_final_escopo['Vol. Chat'].sum()
                tma_chat_medio = df_final_escopo['TMA Chat (Min)'].mean()
                total_vol_voz = df_final_escopo['Vol. Voz'].sum()
                tma_voz_medio = df_final_escopo['TMA Voz (Min)'].mean()
                
                tpc_chat_medio = df_final_escopo['TPC Chat (Seg)'].mean() if 'TPC Chat (Seg)' in df_final_escopo.columns else 0.0
                tpc_voz_medio = df_final_escopo['TPC Voz (Seg)'].mean() if 'TPC Voz (Seg)' in df_final_escopo.columns else 0.0
                v_faltas = df_final_escopo['Faltas'].sum() if 'Faltas' in df_final_escopo.columns else 0
                
                if filtro_agente != "Todos":
                    v_comissao = df_final_escopo['Comissão (R$)'].sum() if 'Comissão (R$)' in df_final_escopo.columns else 0.0

                st.subheader(f"🎯 Métricas Consolidadas ({filtro_agente})")
                
                st.markdown("##### 🌟 Qualidade, Retenção e Escala")
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>⭐ CSAT Ponderado</div><div class='kpi-value'>{v_csat:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_CSAT:.0f}%</div></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🎯 Índice IR</div><div class='kpi-value'>{v_ir:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_IR:.0f}%</div></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>📈 Taxa Retenção</div><div class='kpi-value'>{v_retencao:.2f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_RETENCAO:.0f}%</div></div>", unsafe_allow_html=True)
                with c4: st.markdown(f"<div class='kpi-card' style='border-left-color: #9932cc;'><div class='kpi-title'>📅 Conformidade</div><div class='kpi-value'>{v_conf:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_CONFORMIDADE:.0f}%</div></div>", unsafe_allow_html=True)
                with c5: st.markdown(f"<div class='kpi-card' style='border-left-color: #ba55d3;'><div class='kpi-title'>⏱️ Aderência</div><div class='kpi-value'>{v_ade:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_ADERENCIA:.0f}%</div></div>", unsafe_allow_html=True)
                
                if filtro_agente == "Todos":
                    with c6: st.markdown(f"<div class='kpi-card' style='border-left-color: #dc3545;'><div class='kpi-title'>❌ Faltas totais</div><div class='kpi-value' style='color:#dc3545;'>{int(v_faltas)}</div><div style='font-size:11px;color:#6c757d;font-weight:bold;'>No Período</div></div>", unsafe_allow_html=True)
                else:
                    with c6: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745; background-color: #f6ffed;'><div class='kpi-title'>💰 Comissão</div><div class='kpi-value' style='color:#28a745;'>R$ {v_comissao:,.2f}</div><div style='font-size:11px;color:#6c757d;font-weight:bold;'>Estimativa (RV)</div></div>", unsafe_allow_html=True)

                col_chat, col_voz = st.columns(2)
                with col_chat:
                    st.markdown("##### 💬 Desempenho de Chat")
                    cc1, cc2, cc3 = st.columns(3)
                    with cc1: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>Vol. Chat</div><div class='kpi-value'>{int(total_vol_chat):,}</div></div>", unsafe_allow_html=True)
                    with cc2: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>TMA Chat</div><div class='kpi-value'>{tma_chat_medio:.1f}m</div></div>", unsafe_allow_html=True)
                    val_tpc_chat = f"{tpc_chat_medio:.1f}s" if 'TPC Chat (Seg)' in df_final_escopo.columns and tpc_chat_medio > 0 else "--"
                    with cc3: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>TPC Chat</div><div class='kpi-value'>{val_tpc_chat}</div><div style='font-size:11px;color:#6c757d;font-weight:bold;'>Meta: {META_TPC:.0f}s</div></div>", unsafe_allow_html=True)

                with col_voz:
                    st.markdown("##### 📞 Desempenho de Voz")
                    cv1, cv2, cv3 = st.columns(3)
                    with cv1: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Vol. Voz</div><div class='kpi-value'>{int(total_vol_voz):,}</div></div>", unsafe_allow_html=True)
                    with cv2: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>TMA Voz</div><div class='kpi-value'>{tma_voz_medio:.1f}m</div></div>", unsafe_allow_html=True)
                    val_tpc_voz = f"{tpc_voz_medio:.1f}s" if 'TPC Voz (Seg)' in df_final_escopo.columns and tpc_voz_medio > 0 else "--"
                    with cv3: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>TPC Voz</div><div class='kpi-value'>{val_tpc_voz}</div><div style='font-size:11px;color:#6c757d;font-weight:bold;'>Meta: {META_TPC:.0f}s</div></div>", unsafe_allow_html=True)

                st.markdown("---")
                
                st.subheader("📈 Análise de Evolução Histórica")
                df_hist_plot = obter_dados_historicos(df_completo, filtro_agente)
                
                if not df_hist_plot.empty and len(df_hist_plot) > 0:
                    indicadores_hist = ['CSAT Ponderado (%)', 'Índice IR (%)', 'Taxa Retenção (%)', 'Aderência (%)', 'Conformidade (%)', 'Faltas']
                    metrica_escolhida = st.selectbox("Selecione o indicador para acompanhar a evolução ao longo do tempo:", indicadores_hist)
                    
                    fig_hist = px.line(df_hist_plot, x='Mês/Ano', y=metrica_escolhida, markers=True, text=metrica_escolhida, title=f"Evolução de {metrica_escolhida} - {filtro_agente}")
                    fig_hist.update_traces(textposition="top center", texttemplate='%{text:.0f}' if metrica_escolhida == 'Faltas' else '%{text:.1f}%', line=dict(width=4), marker=dict(size=10))
                    
                    meta_valor = 0
                    if "CSAT" in metrica_escolhida: meta_valor = META_CSAT
                    elif "IR" in metrica_escolhida: meta_valor = META_IR
                    elif "Retenção" in metrica_escolhida: meta_valor = META_RETENCAO
                    elif "Aderência" in metrica_escolhida: meta_valor = META_ADERENCIA
                    elif "Conformidade" in metrica_escolhida: meta_valor = META_CONFORMIDADE
                    
                    if meta_valor > 0:
                        fig_hist.add_hline(y=meta_valor, line_dash="dash", line_color="green", annotation_text=f"Meta: {meta_valor}%")
                        
                    max_y = df_hist_plot[metrica_escolhida].max() + (5 if metrica_escolhida == 'Faltas' else 10)
                    if meta_valor > 0: max_y = max(max_y, meta_valor + 5, 100)
                    fig_hist.update_yaxes(range=[0, max_y])
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("Faça o upload de mais de um mês para visualizar a curva histórica.")

                st.markdown("---")
                
                if filtro_agente == "Todos":
                    st.subheader("📊 Central de Auditoria Visual de Indicadores")
                    tab_graf_1, tab_graf_2, tab_graf_3, tab_graf_4 = st.tabs(["🏅 Rankings de Qualidade & Retenção", "⏱️ Rankings de Processos & Eficiência", "💬 Volumetria de Atendimentos", "💰 Rankings de Comissões"])
                    df_chart_base = df_final_escopo.dropna(subset=['Nome Exibição'])
                    
                    with tab_graf_1:
                        cg1, cg2, cg3 = st.columns(3)
                        with cg1:
                            fig_csat = px.bar(df_chart_base.sort_values(by='CSAT_Agente (%)', ascending=True).head(10), x='CSAT_Agente (%)', y='Nome Exibição', orientation='h', title="⭐ CSAT (Detratores)", color='CSAT_Agente (%)', color_continuous_scale='Reds_r', text='CSAT_Agente (%)')
                            fig_csat.update_traces(texttemplate='%{text:.1f}%', textposition='auto')
                            fig_csat.update_yaxes(autorange="reversed")
                            fig_csat.add_vline(x=META_CSAT, line_dash="dash", line_color="green")
                            st.plotly_chart(fig_csat, use_container_width=True)
                        with cg2:
                            fig_ir = px.bar(df_chart_base.sort_values(by='IR_Agente (%)', ascending=True).head(10), x='IR_Agente (%)', y='Nome Exibição', orientation='h', title="🎯 Índice IR", color='IR_Agente (%)', color_continuous_scale='Reds_r', text='IR_Agente (%)')
                            fig_ir.update_traces(texttemplate='%{text:.1f}%', textposition='auto')
                            fig_ir.update_yaxes(autorange="reversed")
                            fig_ir.add_vline(x=META_IR, line_dash="dash", line_color="green")
                            st.plotly_chart(fig_ir, use_container_width=True)
                        with cg3:
                            fig_ret = px.bar(df_chart_base.sort_values(by='% Retenção', ascending=True).head(10), x='% Retenção', y='Nome Exibição', orientation='h', title="📈 Retenção", color='% Retenção', color_continuous_scale='Reds_r', text='% Retenção')
                            fig_ret.update_traces(texttemplate='%{text:.1f}%', textposition='auto')
                            fig_ret.update_yaxes(autorange="reversed")
                            fig_ret.add_vline(x=META_RETENCAO, line_dash="dash", line_color="green")
                            st.plotly_chart(fig_ret, use_container_width=True)

                    with tab_graf_2:
                        st.markdown("#### ⏱️ Escala e Aderência")
                        cx1, cx2 = st.columns(2)
                        with cx1:
                            fig_ade = px.bar(df_chart_base.sort_values(by='Aderência (%)', ascending=True).head(10), x='Aderência (%)', y='Nome Exibição', orientation='h', title="⏱️ Aderência (Pausas)", color='Aderência (%)', color_continuous_scale='Reds_r', text='Aderência (%)')
                            fig_ade.update_traces(texttemplate='%{text:.1f}%', textposition='auto')
                            fig_ade.update_yaxes(autorange="reversed")
                            fig_ade.add_vline(x=META_ADERENCIA, line_dash="dash", line_color="green")
                            st.plotly_chart(fig_ade, use_container_width=True)
                        with cx2:
                            fig_conf = px.bar(df_chart_base.sort_values(by='Conformidade (%)', ascending=True).head(10), x='Conformidade (%)', y='Nome Exibição', orientation='h', title="📅 Conformidade (Escala)", color='Conformidade (%)', color_continuous_scale='Reds_r', text='Conformidade (%)')
                            fig_conf.update_traces(texttemplate='%{text:.1f}%', textposition='auto')
                            fig_conf.update_yaxes(autorange="reversed")
                            fig_conf.add_vline(x=META_CONFORMIDADE, line_dash="dash", line_color="green")
                            st.plotly_chart(fig_conf, use_container_width=True)
                            
                        st.markdown("---")
                        st.markdown("#### 💬 Tempos de Chat (Ofensores)")
                        cx3, cx4 = st.columns(2)
                        with cx3:
                            fig_tmach = px.bar(df_chart_base.sort_values(by='TMA Chat (Min)', ascending=False).head(10), x='TMA Chat (Min)', y='Nome Exibição', orientation='h', title="⏳ Maiores TMAs Chat", color='TMA Chat (Min)', color_continuous_scale='Oranges', text='TMA Chat (Min)')
                            fig_tmach.update_traces(texttemplate='%{text:.1f}m', textposition='auto')
                            fig_tmach.update_yaxes(autorange="reversed")
                            st.plotly_chart(fig_tmach, use_container_width=True)
                        with cx4:
                            if 'TPC Chat (Seg)' in df_chart_base.columns and df_chart_base['TPC Chat (Seg)'].sum() > 0:
                                fig_tpcch = px.bar(df_chart_base.sort_values(by='TPC Chat (Seg)', ascending=False).head(10), x='TPC Chat (Seg)', y='Nome Exibição', orientation='h', title="⏱️ Maiores TPCs Chat (Segundos)", color='TPC Chat (Seg)', color_continuous_scale='Oranges', text='TPC Chat (Seg)')
                                fig_tpcch.update_traces(texttemplate='%{text:.1f}s', textposition='auto')
                                fig_tpcch.update_yaxes(autorange="reversed")
                                fig_tpcch.add_vline(x=META_TPC, line_dash="dash", line_color="green")
                                st.plotly_chart(fig_tpcch, use_container_width=True)
                            else:
                                st.info("Gráfico de TPC Chat indisponível (Dados Zerados).")

                        st.markdown("---")
                        st.markdown("#### 📞 Tempos de Voz (Ofensores)")
                        cx5, cx6 = st.columns(2)
                        with cx5:
                            fig_tmavz = px.bar(df_chart_base.sort_values(by='TMA Voz (Min)', ascending=False).head(10), x='TMA Voz (Min)', y='Nome Exibição', orientation='h', title="⏳ Maiores TMAs Voz", color='TMA Voz (Min)', color_continuous_scale='Oranges', text='TMA Voz (Min)')
                            fig_tmavz.update_traces(texttemplate='%{text:.1f}m', textposition='auto')
                            fig_tmavz.update_yaxes(autorange="reversed")
                            st.plotly_chart(fig_tmavz, use_container_width=True)
                        with cx6:
                            if 'TPC Voz (Seg)' in df_chart_base.columns and df_chart_base['TPC Voz (Seg)'].sum() > 0:
                                fig_tpcvz = px.bar(df_chart_base.sort_values(by='TPC Voz (Seg)', ascending=False).head(10), x='TPC Voz (Seg)', y='Nome Exibição', orientation='h', title="⏱️ Maiores TPCs Voz (Segundos)", color='TPC Voz (Seg)', color_continuous_scale='Oranges', text='TPC Voz (Seg)')
                                fig_tpcvz.update_traces(texttemplate='%{text:.1f}s', textposition='auto')
                                fig_tpcvz.update_yaxes(autorange="reversed")
                                fig_tpcvz.add_vline(x=META_TPC, line_dash="dash", line_color="green")
                                st.plotly_chart(fig_tpcvz, use_container_width=True)
                            else:
                                st.info("Gráfico de TPC Voz indisponível (Dados Zerados).")

                    with tab_graf_3:
                        cv1, cv2 = st.columns(2)
                        with cv1:
                            fig_volch = px.bar(df_chart_base.sort_values(by='Vol. Chat', ascending=False).head(12), x='Vol. Chat', y='Nome Exibição', orientation='h', title="💬 Volume Chats por Operador", color='Vol. Chat', color_continuous_scale='Blues', text='Vol. Chat')
                            fig_volch.update_traces(texttemplate='%{text:,.0f}', textposition='auto')
                            fig_volch.update_yaxes(autorange="reversed")
                            st.plotly_chart(fig_volch, use_container_width=True)
                        with cv2:
                            fig_volvz = px.bar(df_chart_base.sort_values(by='Vol. Voz', ascending=False).head(12), x='Vol. Voz', y='Nome Exibição', orientation='h', title="📞 Volume Voz por Operador", color='Vol. Voz', color_continuous_scale='Teal', text='Vol. Voz')
                            fig_volvz.update_traces(texttemplate='%{text:,.0f}', textposition='auto')
                            fig_volvz.update_yaxes(autorange="reversed")
                            st.plotly_chart(fig_volvz, use_container_width=True)
                            
                    with tab_graf_4:
                        if 'Comissão (R$)' in df_chart_base.columns and df_chart_base['Comissão (R$)'].sum() > 0:
                            df_comissao = df_chart_base[df_chart_base['Comissão (R$)'] > 0].sort_values(by='Comissão (R$)', ascending=True)
                            if not df_comissao.empty:
                                fig_comissao = px.bar(df_comissao, x='Comissão (R$)', y='Nome Exibição', orientation='h', title="💰 Ranking de Remuneração Variável Estimada", color='Comissão (R$)', color_continuous_scale='Greens', text='Comissão (R$)')
                                fig_comissao.update_traces(texttemplate='R$ %{text:,.2f}', textposition='auto')
                                st.plotly_chart(fig_comissao, use_container_width=True)
                            else:
                                st.info("Nenhum operador atingiu os gatilhos e volume para comissionamento neste período.")
                        else:
                            st.info("Nenhuma comissão gerada neste período. Verifique os dados de volume e qualidade.")
                    
                st.markdown("---")
                
                st.subheader(f"📅 Absenteísmo no Mês ({mes_view}/{ano_view})")
                
                if 'Faltas' in df_periodo_mapeado.columns:
                    df_faltas_mes = df_periodo_mapeado.copy()
                    df_faltas_mes['Faltas_Reais'] = df_faltas_mes.apply(lambda r: pd.to_numeric(r.get('Faltas', 0), errors='coerce') if r['Status_Dinamico'] == 'Ativo' else 0, axis=1).fillna(0)
                    
                    if filtro_agente == "Todos":
                        st.markdown("#### ⚙️ Calculadora de Absenteísmo da Equipe")
                        st.markdown("Considere a jornada padrão de **6 horas diárias (Seg a Sáb)** para os operadores ativos.")
                        col_calc1, col_calc2 = st.columns(2)
                        dias_uteis = col_calc1.number_input("Dias previstos de escala no mês:", min_value=1, max_value=31, value=26)
                        perdas_minutos = col_calc2.number_input("Perdas extras da equipe em minutos (Atrasos, saídas, etc):", min_value=0, value=0)
                        
                        total_ativos = len(df_faltas_mes[df_faltas_mes['Status_Dinamico'] == 'Ativo'])
                        total_faltas_equipe = df_faltas_mes['Faltas_Reais'].sum()
                        
                        horas_planejadas = total_ativos * dias_uteis * 6
                        horas_perdidas = (total_faltas_equipe * 6) + (perdas_minutos / 60)
                        taxa_abs = (horas_perdidas / horas_planejadas * 100) if horas_planejadas > 0 else 0.0
                        
                        st.markdown(f"<div class='kpi-card' style='border-left-color: #e53e3e; max-width: 400px; margin: 0 auto;'><div class='kpi-title'>Taxa de Absenteísmo Estimada</div><div class='kpi-value' style='color:#e53e3e;'>{taxa_abs:.2f}%</div><div style='font-size:12px;color:#6c757d;margin-top:5px;'>Perda: {horas_perdidas:.1f}h / Previsto: {horas_planejadas:.0f}h</div></div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                    
                    df_faltou = df_faltas_mes[df_faltas_mes['Faltas_Reais'] > 0].copy()
                    if filtro_agente != "Todos":
                        df_faltou = df_faltou[df_faltou['Nome Exibição'] == filtro_agente]
                        
                    if not df_faltou.empty:
                        df_faltou_grp = df_faltou.groupby('Nome Exibição').agg(
                            Total_Faltas=('Faltas_Reais', 'sum')
                        ).reset_index()
                        
                        df_faltou_grp.rename(columns={'Nome Exibição': 'Operador', 'Total_Faltas': 'Faltas no Mês'}, inplace=True)
                        df_faltou_grp = df_faltou_grp.sort_values(by='Faltas no Mês', ascending=False)
                        
                        st.dataframe(df_faltou_grp.style.format({'Faltas no Mês': '{:.0f}'}), use_container_width=True)
                    else:
                        st.success(f"🎉 Nenhuma falta registrada na operação em {mes_view}/{ano_view} (entre os ativos)!")
                else:
                    st.info(f"O relatório de faltas para {mes_view}/{ano_view} não está disponível.")

                st.markdown("---")

                st.subheader("👥 Detalhamento Operacional por Colaborador")
                colunas_tabela = ['Nome Exibição', 'Status_Dinamico', 'Comissão (R$)', 'Faltas', 'CSAT_Agente (%)', 'IR_Agente (%)', 'Conformidade (%)', 'Aderência (%)', 'Vol. Chat', 'TMA Chat (Min)']
                if 'TPC Chat (Seg)' in df_final_escopo.columns: colunas_tabela.append('TPC Chat (Seg)')
                colunas_tabela += ['Vol. Voz', 'TMA Voz (Min)']
                if 'TPC Voz (Seg)' in df_final_escopo.columns: colunas_tabela.append('TPC Voz (Seg)')
                colunas_tabela += ['RT geral valido', '% Retenção', '% Cancelamento']
                
                colunas_tabela = list(dict.fromkeys(colunas_tabela))
                
                def estilizar_linhas_status(row):
                    if str(row['Status_Dinamico']).strip().lower() != 'ativo': return ['background-color: #f1f3f5; color: #adb5bd; font-style: italic;'] * len(row)
                    return [''] * len(row)

                df_tabela_final = df_final_escopo.copy()
                df_tabela_final['Comissão (R$)'] = df_tabela_final['Comissão (R$)'].apply(lambda x: f"R$ {x:,.2f}")
                df_tabela_final['Faltas'] = df_tabela_final['Faltas'].apply(lambda x: f"{x:.0f}")
                df_tabela_final['CSAT_Agente (%)'] = df_tabela_final['CSAT_Agente (%)'].apply(lambda x: f"{x:.1f}%")
                df_tabela_final['IR_Agente (%)'] = df_tabela_final['IR_Agente (%)'].apply(lambda x: f"{x:.1f}%")
                df_tabela_final['Aderência (%)'] = df_tabela_final['Aderência (%)'].apply(lambda x: f"{x:.1f}%")
                df_tabela_final['Conformidade (%)'] = df_tabela_final['Conformidade (%)'].apply(lambda x: f"{x:.1f}%")
                df_tabela_final['% Retenção'] = df_tabela_final['% Retenção'].apply(lambda x: f"{x:.2f}%")
                df_tabela_final['% Cancelamento'] = df_tabela_final['% Cancelamento'].apply(lambda x: f"{x:.2f}%")
                df_tabela_final['Vol. Chat'] = df_tabela_final['Vol. Chat'].apply(lambda x: f"{x:,.0f}")
                df_tabela_final['TMA Chat (Min)'] = df_tabela_final['TMA Chat (Min)'].apply(lambda x: f"{x:.1f}m")
                df_tabela_final['Vol. Voz'] = df_tabela_final['Vol. Voz'].apply(lambda x: f"{x:,.0f}")
                df_tabela_final['TMA Voz (Min)'] = df_tabela_final['TMA Voz (Min)'].apply(lambda x: f"{x:.1f}m")
                df_tabela_final['RT geral valido'] = df_tabela_final['RT geral valido'].apply(lambda x: f"{x:,.0f}")
                
                if 'TPC Chat (Seg)' in df_tabela_final.columns: df_tabela_final['TPC Chat (Seg)'] = df_tabela_final['TPC Chat (Seg)'].apply(lambda x: f"{x:.1f}s")
                if 'TPC Voz (Seg)' in df_tabela_final.columns: df_tabela_final['TPC Voz (Seg)'] = df_tabela_final['TPC Voz (Seg)'].apply(lambda x: f"{x:.1f}s")

                st.dataframe(df_tabela_final[colunas_tabela].style.apply(estilizar_linhas_status, axis=1), use_container_width=True)

    # ==========================================
    # VISÃO DO AGENTE NOMINAL LOGADO (GAMIFICADO E HISTÓRICO)
    # ==========================================
    elif st.session_state.perfil == "Agente":
        if not base_mestre_existe: st.error("⚠️ Configurando o sistema. Tente novamente mais tarde.")
        elif not dados_carregados: st.warning(f"⚠️ {erro_dados}")
        else:
            df_users_login = ler_csv_via_api_github("dados_usuarios.csv")
            if 'E-MAIL' in df_users_login.columns: df_users_login.rename(columns={'E-MAIL': 'E-mail'}, inplace=True)
            
            df_users_login['E-mail'] = df_users_login['E-mail'].astype(str)
            
            mask_user = df_users_login['E-mail'].str.strip().str.lower() == st.session_state.user_email.strip().lower()
            meus_dados_cadastrais = df_users_login[mask_user].iloc[0]
            
            mes_ferias_cadastrado = str(meus_dados_cadastrais.get('FÉRIAS 2026', '')).strip().title()
            if mes_ferias_cadastrado.lower() == 'nan' or mes_ferias_cadastrado == '':
                mes_ferias_cadastrado = "Não programadas"

            data_admissao = str(meus_dados_cadastrais.get('ADMISSÃO', '')).strip()
            tempo_empresa = calcular_tempo_empresa(data_admissao)
            
            primeiro_nome = st.session_state.user_nome.split()[0]
            st.markdown(f"<h2>👋 Olá, {primeiro_nome}!</h2>", unsafe_allow_html=True)
            
            col_email_periodo = 'E-MAIL' if 'E-MAIL' in df_periodo.columns else 'E-mail'
            df_completo_agente = df_completo[df_completo[col_email_periodo].str.strip().str.lower() == st.session_state.user_email.strip().lower()].copy()
            
            if not df_completo_agente.empty and 'Faltas' in df_completo_agente.columns:
                def get_status_global_ag(row):
                    if str(row.get('STATUS', 'ATIVO')).strip().upper() == 'AFASTADO': return 'Afastado'
                    mes_f = str(row.get('FÉRIAS 2026', '')).strip().upper()
                    if mes_f == str(row.get('Mês', '')).strip().upper(): return 'Férias'
                    return 'Ativo'
                
                df_completo_agente['Status_Dinamico'] = df_completo_agente.apply(get_status_global_ag, axis=1)
                df_completo_agente['Faltas_Reais'] = df_completo_agente.apply(lambda r: pd.to_numeric(r.get('Faltas', 0), errors='coerce') if r['Status_Dinamico'] == 'Ativo' else 0, axis=1).fillna(0)
                df_faltou_ag = df_completo_agente[df_completo_agente['Faltas_Reais'] > 0]
                
                if not df_faltou_ag.empty:
                    meses_falta_ag = ", ".join((df_faltou_ag['Mês'].astype(str) + "/" + df_faltou_ag['Ano'].astype(str)).tolist())
                    st.markdown(f"<div class='detractor-box' style='background-color:#fff5f5;border-color:#feb2b2;color:#c53030;'>⚠️ <b>Atenção:</b> Você possui registro de falta(s) no seu histórico (<b>{meses_falta_ag}</b>). Mantenha sua aderência e presença em dia!</div>", unsafe_allow_html=True)
            
            st.markdown("---")

            aba_desempenho, aba_ferias, aba_wiki, aba_conta = st.tabs([
                "📊 Meu Desempenho", 
                "🌴 Minhas Férias", 
                "📚 Base de Conhecimento", 
                "⚙️ Minha Conta"
            ])

            with aba_desempenho:
                st.markdown(f"<p style='color: #6c757d; font-size: 16px;'>Acompanhe o seu desempenho e metas referentes a <b>{mes_view} de {ano_view}</b>.</p>", unsafe_allow_html=True)
                
                st.markdown("### 📋 Informações Cadastrais")
                c_info1, c_info2, c_info3 = st.columns(3)
                
                with c_info1:
                    if mes_ferias_cadastrado.upper() == mes_view.upper() and mes_ferias_cadastrado != "Não programadas":
                        st.markdown(f"<div class='info-card' style='border-left: 5px solid #1e88e5;'><div class='info-title'>Status em {mes_view}</div><div class='info-data' style='color:#1e88e5;'>🌴 Férias Programadas</div></div>", unsafe_allow_html=True)
                    elif str(meus_dados_cadastrais.get('STATUS', '')).strip().upper() == 'AFASTADO':
                        st.markdown(f"<div class='info-card' style='border-left: 5px solid #e53e3e;'><div class='info-title'>Status em {mes_view}</div><div class='info-data' style='color:#e53e3e;'>🩺 Afastado</div></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='info-card' style='border-left: 5px solid #28a745;'><div class='info-title'>Status em {mes_view}</div><div class='info-data' style='color:#28a745;'>✅ Ativo</div></div>", unsafe_allow_html=True)
                
                with c_info2:
                    st.markdown(f"<div class='info-card'><div class='info-title'>Data de Admissão</div><div class='info-data'>{data_admissao if data_admissao != 'nan' else 'Não cadastrada'}</div></div>", unsafe_allow_html=True)
                
                with c_info3:
                    st.markdown(f"<div class='info-card'><div class='info-title'>Tempo de Empresa</div><div class='info-data'>{tempo_empresa}</div></div>", unsafe_allow_html=True)

                meus_dados = df_periodo[df_periodo[col_email_periodo].str.strip().str.lower() == st.session_state.user_email.strip().lower()]
                
                if not meus_dados.empty:
                    dados = meus_dados.iloc[0]
                    tem_colunas_novas = 'Total_Pesq_CSAT' in df_periodo.columns
                    my_csat = (dados['Boas_Pesq_CSAT'] / dados['Total_Pesq_CSAT'] * 100) if tem_colunas_novas and dados['Total_Pesq_CSAT'] > 0 else 0.0
                    my_ir = (dados['Sim_Pesq_IR'] / dados['Total_Pesq_IR'] * 100) if tem_colunas_novas and dados['Total_Pesq_IR'] > 0 else 0.0
                    my_tx_ret = dados['Taxa_Retencao_Original'] if 'Taxa_Retencao_Original' in dados else 0.0
                    
                    status_agente_mes = 'Ativo'
                    if mes_ferias_cadastrado.upper() == mes_view.upper() and mes_ferias_cadastrado != "Não programadas": status_agente_mes = 'Férias'
                    elif str(meus_dados_cadastrais.get('STATUS', '')).strip().upper() == 'AFASTADO': status_agente_mes = 'Afastado'
                    minhas_faltas = int(dados['Faltas']) if 'Faltas' in df_periodo.columns and pd.notna(dados.get('Faltas')) and status_agente_mes == 'Ativo' else 0
                    
                    # CÁLCULO DE COMISSÃO DO AGENTE
                    minha_comissao = calcular_comissao_rv(
                        taxa_ret=my_tx_ret,
                        vol_fibra=dados.get('RT_Fibra_Validas', 0.0),
                        vol_adic=dados.get('RT_Adicional_Validas', 0.0),
                        diamantes=dados.get('Diamantes', 0)
                    )
                    
                    df_ranking = df_periodo.copy()
                    rank_display = "N/A"
                    cor_rank = "#6c757d"
                    
                    if 'Taxa_Retencao_Original' in df_ranking.columns:
                        df_ranking = df_ranking.dropna(subset=['Taxa_Retencao_Original'])
                        df_ranking = df_ranking.sort_values(by='Taxa_Retencao_Original', ascending=False).reset_index(drop=True)
                        df_ranking['email_clean'] = df_ranking[col_email_periodo].astype(str).str.strip().str.lower()
                        
                        user_email_clean = st.session_state.user_email.strip().lower()
                        if user_email_clean in df_ranking['email_clean'].values:
                            user_rank = df_ranking[df_ranking['email_clean'] == user_email_clean].index[0] + 1
                            total_agents = len(df_ranking)
                            top_retencao = df_ranking['Taxa_Retencao_Original'].iloc[0]
                            
                            if user_rank == 1:
                                rank_display = f"🥇 <b>Parabéns!</b> Você é o líder absoluto de Retenção entre {total_agents} operadores!"
                                cor_rank = "#ffc107" 
                            elif user_rank <= 3:
                                rank_display = f"🥈 <b>Top {user_rank}!</b> Você é um dos melhores de um grupo de {total_agents} operadores!"
                                cor_rank = "#17a2b8" 
                            else:
                                rank_display = f"🏆 <b>{user_rank}º Lugar</b> de {total_agents} operadores. <i>(O 1º lugar está com {top_retencao:.2f}%)</i>"
                                cor_rank = "#007bff" 
                        else:
                            rank_display = "Dados insuficientes para gerar o seu ranking neste mês."
                            
                    st.markdown(f"""
                        <div style='background-color: #ffffff; border: 1px solid #e9ecef; border-left: 5px solid {cor_rank}; padding: 15px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0px 2px 5px rgba(0,0,0,0.02);'>
                            <h4 style='margin: 0; color: #6c757d; font-size: 13px; text-transform: uppercase;'>Seu Ranking na Equipe (Retenção)</h4>
                            <p style='margin: 5px 0 0 0; color: #343a40; font-size: 18px;'>{rank_display}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("### ⭐ Qualidade e Processos")
                    ca1, ca2, ca3, ca4, ca5, ca6 = st.columns(6)
                    with ca1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Meu CSAT</div><div class='kpi-value'>{my_csat:.1f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_CSAT:.0f}%</div></div>", unsafe_allow_html=True)
                    with ca2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Meu Índice IR</div><div class='kpi-value'>{my_ir:.1f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_IR:.0f}%</div></div>", unsafe_allow_html=True)
                    with ca3: st.markdown(f"<div class='kpi-card' style='border-left-color: #9932cc;'><div class='kpi-title'>Conformidade</div><div class='kpi-value'>{dados['Conformidade (%)']:.1f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_CONFORMIDADE:.0f}%</div></div>", unsafe_allow_html=True)
                    with ca4: st.markdown(f"<div class='kpi-card' style='border-left-color: #ba55d3;'><div class='kpi-title'>Aderência</div><div class='kpi-value'>{dados['Aderência (%)']:.1f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_ADERENCIA:.0f}%</div></div>", unsafe_allow_html=True)
                    with ca5: st.markdown(f"<div class='kpi-card' style='border-left-color: #dc3545;'><div class='kpi-title'>Minhas Faltas</div><div class='kpi-value' style='color:#dc3545;'>{minhas_faltas}</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>No Período</div></div>", unsafe_allow_html=True)
                    with ca6: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745; background-color: #f6ffed;'><div class='kpi-title'>💰 Minha Comissão</div><div class='kpi-value' style='color:#28a745;'>R$ {minha_comissao:,.2f}</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Estimativa (RV)</div></div>", unsafe_allow_html=True)

                    st.markdown("### 🎧 Produtividade e Resultados")
                    co1, co2, co3, co4, co5 = st.columns(5)
                    with co1: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>Chats Atendidos</div><div class='kpi-value'>{int(dados['Vol. Chat']) if pd.notna(dados['Vol. Chat']) else 0}</div></div>", unsafe_allow_html=True)
                    with co2: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>Meu TMA Chat</div><div class='kpi-value'>{dados['TMA Chat (Min)']:.1f}m</div></div>", unsafe_allow_html=True)
                    val_tpc_chat = f"{dados['TPC Chat (Seg)']:.1f}s" if 'TPC Chat (Seg)' in df_periodo.columns and pd.notna(dados.get('TPC Chat (Seg)')) and dados['TPC Chat (Seg)'] > 0 else "--"
                    with co3: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>Meu TPC Chat</div><div class='kpi-value'>{val_tpc_chat}</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_TPC:.0f}s</div></div>", unsafe_allow_html=True)
                    with co4: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Taxa de Retenção</div><div class='kpi-value'>{my_tx_ret:.2f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_RETENCAO:.0f}%</div></div>", unsafe_allow_html=True)
                    with co5: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Diamantes (Gami)</div><div class='kpi-value' style='color:#28a745;'>{int(dados.get('Diamantes', 0))}</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>No Período</div></div>", unsafe_allow_html=True)

                    cv1, cv2, cv3, cv4 = st.columns(4)
                    with cv1: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Chamadas Voz</div><div class='kpi-value'>{int(dados['Vol. Voz']) if pd.notna(dados['Vol. Voz']) else 0}</div></div>", unsafe_allow_html=True)
                    with cv2: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Meu TMA Voz</div><div class='kpi-value'>{dados['TMA Voz (Min)']:.1f}m</div></div>", unsafe_allow_html=True)
                    val_tpc_voz = f"{dados['TPC Voz (Seg)']:.1f}s" if 'TPC Voz (Seg)' in df_periodo.columns and pd.notna(dados.get('TPC Voz (Seg)')) and dados['TPC Voz (Seg)'] > 0 else "--"
                    with cv3: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Meu TPC Voz</div><div class='kpi-value'>{val_tpc_voz}</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_TPC:.0f}s</div></div>", unsafe_allow_html=True)
                    with cv4: pass

                    st.markdown("---")
                    st.markdown("### 📈 Minha Evolução Histórica")
                    if not df_completo_agente.empty:
                        df_completo_agente['Nome Exibição'] = "Eu"
                        df_hist_plot_ag = obter_dados_historicos(df_completo_agente, "Eu")
                        
                        if not df_hist_plot_ag.empty and len(df_hist_plot_ag) > 0:
                            indicadores_hist_ag = ['CSAT Ponderado (%)', 'Índice IR (%)', 'Taxa Retenção (%)', 'Aderência (%)', 'Conformidade (%)', 'Faltas']
                            metrica_escolhida_ag = st.selectbox("Selecione o indicador para acompanhar o seu progresso:", indicadores_hist_ag, key="hist_ag")
                            
                            fig_hist_ag = px.line(df_hist_plot_ag, x='Mês/Ano', y=metrica_escolhida_ag, markers=True, text=metrica_escolhida_ag, title=f"Minha Evolução: {metrica_escolhida_ag}")
                            fig_hist_ag.update_traces(textposition="top center", texttemplate='%{text:.0f}' if metrica_escolhida_ag == 'Faltas' else '%{text:.1f}%', line=dict(width=4), marker=dict(size=10))
                            
                            meta_valor_ag = 0
                            if "CSAT" in metrica_escolhida_ag: meta_valor_ag = META_CSAT
                            elif "IR" in metrica_escolhida_ag: meta_valor_ag = META_IR
                            elif "Retenção" in metrica_escolhida_ag: meta_valor_ag = META_RETENCAO
                            elif "Aderência" in metrica_escolhida_ag: meta_valor_ag = META_ADERENCIA
                            elif "Conformidade" in metrica_escolhida_ag: meta_valor_ag = META_CONFORMIDADE
                            
                            if meta_valor_ag > 0:
                                fig_hist_ag.add_hline(y=meta_valor_ag, line_dash="dash", line_color="green", annotation_text=f"Meta: {meta_valor_ag}%")
                                
                            max_y_ag = df_hist_plot_ag[metrica_escolhida_ag].max() + (5 if metrica_escolhida_ag == 'Faltas' else 10)
                            if meta_valor_ag > 0: max_y_ag = max(max_y_ag, meta_valor_ag + 5, 100)
                            fig_hist_ag.update_yaxes(range=[0, max_y_ag])
                            st.plotly_chart(fig_hist_ag, use_container_width=True)
                        else:
                            st.info("Nenhum dado histórico suficiente para gerar o gráfico.")

                else:
                    st.info(f"Ainda não existem dados operacionais associados ao seu perfil para as planilhas de {mes_view}.")

            with aba_ferias:
                st.markdown("### 🌴 Planejamento Anual de Férias")
                if mes_ferias_cadastrado == "Não programadas":
                    st.info("Ainda não tem um mês de férias programado no sistema para este ano. Entre em contato com a gestão para realizar o planejamento.")
                else:
                    st.success(f"🎉 O seu descanso está garantido! As suas férias estão planejadas para o mês de **{mes_ferias_cadastrado}**.")
                    st.markdown(f"""
                        <div class='banner-ferias'>
                            <p style='font-size: 18px; margin-bottom: 0px;'>O seu mês de descanso será em:</p>
                            <h2>{mes_ferias_cadastrado.upper()}</h2>
                        </div>
                    """, unsafe_allow_html=True)

            with aba_wiki:
                st.markdown("### 📚 Base de Conhecimento (Wiki)")
                st.markdown("Bem-vindo à Wiki da Operação! Aqui você encontra todos os materiais, roteiros, manuais e dicas essenciais para o seu dia a dia.")
                
                st.info("💡 **Dica:** Salve o link do Drive nos seus favoritos para acesso rápido durante os atendimentos.")
                
                st.markdown("""
                    <div style='background-color: #f8f9fa; border: 1px solid #e9ecef; border-left: 5px solid #ffc107; padding: 25px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0px 2px 5px rgba(0,0,0,0.02);'>
                        <h3 style='margin: 0; color: #343a40;'>📁 Repositório Oficial de Materiais</h3>
                        <p style='color: #6c757d; font-size: 16px; margin-top: 10px; margin-bottom: 20px;'>
                            Acesse a nossa pasta oficial no Google Drive. Lá você encontrará atualizações de ofertas, comunicados, regras de negócio e roteiros de retenção.
                        </p>
                        <a href='COLE_AQUI_SEU_LINK_DO_DRIVE' target='_blank' class='btn-wiki'>
                            🔗 Acessar Pasta no Google Drive
                        </a>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 📌 O que você vai encontrar no nosso repositório?")
                c_w1, c_w2 = st.columns(2)
                with c_w1:
                    st.markdown("✔️ Manuais de Sistemas e Plataformas\n✔️ Scripts de Retenção e Argumentação\n✔️ Dicas de Qualidade e CSAT")
                with c_w2:
                    st.markdown("✔️ Regras de Ponto, Pausas e Escala\n✔️ Comunicados Oficiais\n✔️ Atualizações de Planos e Ofertas")

            with aba_conta:
                st.markdown("### ⚙️ Configurações de Segurança")
                st.markdown("Para sua segurança, escolha uma senha forte, com letras e números, e não a compartilhe com terceiros.")
                
                with st.form("form_senha_interna"):
                    nova_senha = st.text_input("Digite a sua nova senha", type="password")
                    confirmar_senha = st.text_input("Confirme a nova senha", type="password")
                    if st.form_submit_button("Salvar Senha"):
                        if nova_senha != confirmar_senha:
                            st.error("As senhas não coincidem. Tente novamente.")
                        elif len(nova_senha) < 4:
                            st.error("A senha deve ter pelo menos 4 caracteres.")
                        else:
                            df_users_update = ler_csv_via_api_github("dados_usuarios.csv")
                            col_email_up = 'E-MAIL' if 'E-MAIL' in df_users_update.columns else 'E-mail'
                            
                            df_users_update[col_email_up] = df_users_update[col_email_up].astype(str)
                            if 'SENHA' not in df_users_update.columns:
                                df_users_update['SENHA'] = ""
                            df_users_update['SENHA'] = df_users_update['SENHA'].astype(str)
                            
                            mask = df_users_update[col_email_up].str.strip().str.lower() == st.session_state.user_email.strip().lower()
                            
                            if mask.any():
                                df_users_update.loc[mask, 'SENHA'] = nova_senha
                                enviar_para_github("dados_usuarios.csv", df_users_update.to_csv(index=False))
                                st.cache_data.clear()
                                st.success("✅ A sua senha foi alterada com sucesso!")
                            else:
                                st.error("Erro interno: Usuário não encontrado.")
