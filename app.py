import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github
import io
import time
import base64
import json
from datetime import datetime

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

# NOVO: Função para manter o TPC em segundos de forma correta
def ms_para_segundos(ms):
    if pd.isna(ms): return 0.0
    return ms / 1000

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

@st.cache_data(ttl=5)
def carregar_dados_mestre_seguro():
    df = ler_csv_via_api_github("dados_consolidados_master.csv")
    df['text_ano'] = df['Ano'].astype(str).str.strip()
    df['text_mes'] = df['Mês'].astype(str).str.strip().str.title()
    return df

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
                                st.session_state.user_nome = str(dados_usr[col_nome]).title()
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

        aba_dashboard, aba_retencao, aba_ponto, aba_equipe, aba_ferias, aba_upload = st.tabs([
            "📊 Dashboard Geral", 
            "🎯 Inteligência de Retenção",
            "⏰ Banco de Horas",
            "👥 Gestão da Equipe",
            "🌴 Calendário de Férias",
            "⚙️ Consolidação (Upload)"
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

        # --- O SEGREDO DO SUCESSO: LEITOR UNIVERSAL ROBUSTO NA ABA UPLOAD ---
        with aba_upload:
            st.header("⚙️ Central de Consolidação de Relatórios")
            
            col_m, col_a = st.columns(2)
            mes_up = col_m.selectbox("Mês de competência das planilhas:", MESES, index=4)
            ano_up = col_a.selectbox("Ano de competência das planilhas:", ANOS)
            st.markdown("---")
            
            arquivos_carregados = st.file_uploader("Arraste e solte os 5 arquivos CSV aqui de uma vez", type=["csv"], accept_multiple_files=True)
            relatorios_identificados = {"Aderência e Conformidade": None, "Pesquisa (CSAT/IR)": None, "Chat": None, "Voz": None, "Retenção": None}
            if arquivos_carregados:
                for arquivo in arquivos_carregados:
                    try:
                        df_header = ler_csv_upload_seguro(arquivo, nrows=0)
                        
                        cols_upper = [str(c).strip().upper() for c in df_header.columns]
                        
                        if any('ADER' in c for c in cols_upper) and any('CONFOR' in c for c in cols_upper):
                            relatorios_identificados["Aderência e Conformidade"] = arquivo
                        elif any('CSAT' in c for c in cols_upper) and any('ATENDENTE' in c for c in cols_upper):
                            relatorios_identificados["Pesquisa (CSAT/IR)"] = arquivo
                        elif any('ATENDIDAS' in c for c in cols_upper) and any('NOME DO AGENTE' in c for c in cols_upper):
                            if "CHAT" in arquivo.name.upper(): relatorios_identificados["Chat"] = arquivo
                            else: relatorios_identificados["Voz"] = arquivo
                        elif any('RESPONSAVEL' in c for c in cols_upper) and any('RETEN' in c for c in cols_upper):
                            relatorios_identificados["Retenção"] = arquivo
                    except Exception: pass

            st.markdown("### 📋 Status da Validação")
            c_chk1, c_chk2, c_chk3, c_chk4, c_chk5 = st.columns(5)
            with c_chk1: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Aderência e Conformidade'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>1. Aderência & Conformidade</b></div>", unsafe_allow_html=True)
            with c_chk2: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Pesquisa (CSAT/IR)'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>2. Pesquisas</b></div>", unsafe_allow_html=True)
            with c_chk3: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Chat'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>3. Chat</b></div>", unsafe_allow_html=True)
            with c_chk4: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Voz'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>4. Voz</b></div>", unsafe_allow_html=True)
            with c_chk5: st.markdown(f"<div style='background-color:{'#e6fffa;border:1px solid #319795;' if relatorios_identificados['Retenção'] else '#fff5f5;border:1px solid #e53e3e;'};padding:10px;border-radius:5px;text-align:center;'><b>5. Retenção</b></div>", unsafe_allow_html=True)

            if all(relatorios_identificados.values()) and st.button("🚀 Processar e Atualizar Base Mestre AGORA", type="primary", use_container_width=True):
                with st.spinner("Consolidando..."):
                    try:
                        df_perf = ler_csv_upload_seguro(relatorios_identificados["Aderência e Conformidade"])
                        df_ret = ler_csv_upload_seguro(relatorios_identificados["Retenção"])
                        df_chat = ler_csv_upload_seguro(relatorios_identificados["Chat"])
                        df_voz = ler_csv_upload_seguro(relatorios_identificados["Voz"])
                        df_pesq = ler_csv_upload_seguro(relatorios_identificados["Pesquisa (CSAT/IR)"])
                        df_users = ler_csv_via_api_github("dados_usuarios.csv")
                        
                        col_ade = next((c for c in df_perf.columns if 'ADER' in str(c).upper()), None)
                        col_conf = next((c for c in df_perf.columns if 'CONFOR' in str(c).upper()), None)
                        col_agente = next((c for c in df_perf.columns if 'AGENTE' in str(c).upper()), None)
                        
                        df_perf['Aderência (%)'] = df_perf[col_ade].apply(limpar_porcentagem)
                        df_perf['Conformidade (%)'] = df_perf[col_conf].apply(limpar_porcentagem)
                        df_perf['Chave_Nome'] = df_perf[col_agente].astype(str).str.strip().str.upper()
                        
                        col_nome = 'COLABORADOR' if 'COLABORADOR' in df_users.columns else 'Nome'
                        df_users['Chave_Nome'] = df_users[col_nome].astype(str).str.strip().str.upper()
                        
                        df_ret['Chave_Nome'] = df_ret['responsavel'].astype(str).str.strip().str.upper()
                        df_ret['Taxa_Retencao_Original'] = df_ret['% de retenção'].apply(limpar_porcentagem)
                        df_ret['RT geral valido'] = pd.to_numeric(df_ret['RT geral valido'], errors='coerce').fillna(0)
                        df_ret['RT geral calculado'] = df_ret.apply(lambda row: (row['RT geral valido'] / (row['Taxa_Retencao_Original'] / 100)) if row['Taxa_Retencao_Original'] > 0 else row['RT geral valido'], axis=1).fillna(0)
                        
                        # --- CAPTURA DE TPC PARA CHAT ---
                        df_chat['Chave_Nome'] = df_chat['Nome do agente'].astype(str).str.strip().str.upper()
                        col_tpc_chat = next((c for c in df_chat.columns if 'TPC' in str(c).upper() or 'PÓS' in str(c).upper() or 'POS' in str(c).upper() or 'TRABALHO' in str(c).upper()), None)
                        agg_chat = {'Atendidas': 'sum', 'Tratamento médio': 'mean'}
                        if col_tpc_chat: agg_chat[col_tpc_chat] = 'mean'
                        
                        df_chat_agg = df_chat.groupby('Chave_Nome').agg(agg_chat).reset_index()
                        df_chat_agg.rename(columns={'Atendidas': 'Vol. Chat', 'Tratamento médio': 'TMA Chat (ms)'}, inplace=True)
                        df_chat_agg['TMA Chat (Min)'] = df_chat_agg['TMA Chat (ms)'].apply(ms_para_minutos)
                        if col_tpc_chat:
                            df_chat_agg.rename(columns={col_tpc_chat: 'TPC Chat (ms)'}, inplace=True)
                            df_chat_agg['TPC Chat (Seg)'] = df_chat_agg['TPC Chat (ms)'].apply(ms_para_segundos)
                        
                        # --- CAPTURA DE TPC PARA VOZ ---
                        df_voz['Chave_Nome'] = df_voz['Nome do agente'].astype(str).str.strip().str.upper()
                        col_tpc_voz = next((c for c in df_voz.columns if 'TPC' in str(c).upper() or 'PÓS' in str(c).upper() or 'POS' in str(c).upper() or 'TRABALHO' in str(c).upper()), None)
                        agg_voz = {'Atendidas': 'sum', 'Tratamento médio': 'mean'}
                        if col_tpc_voz: agg_voz[col_tpc_voz] = 'mean'
                        
                        df_voz_agg = df_voz.groupby('Chave_Nome').agg(agg_voz).reset_index()
                        df_voz_agg.rename(columns={'Atendidas': 'Vol. Voz', 'Tratamento médio': 'TMA Voz (ms)'}, inplace=True)
                        df_voz_agg['TMA Voz (Min)'] = df_voz_agg['TMA Voz (ms)'].apply(ms_para_minutos)
                        if col_tpc_voz:
                            df_voz_agg.rename(columns={col_tpc_voz: 'TPC Voz (ms)'}, inplace=True)
                            df_voz_agg['TPC Voz (Seg)'] = df_voz_agg['TPC Voz (ms)'].apply(ms_para_segundos)
                        
                        df_pesq['Chave_Nome'] = df_pesq['Atendente'].astype(str).str.strip().str.upper()
                        df_pesq['CSAT_Num'] = pd.to_numeric(df_pesq['CSAT'], errors='coerce')
                        df_pesq_agg = df_pesq.groupby('Chave_Nome').agg(Total_Pesq_CSAT=('CSAT_Num', 'count'), Boas_Pesq_CSAT=('CSAT_Num', lambda x: (x >= 4).sum()), Total_Pesq_IR=('IR', 'count'), Sim_Pesq_IR=('IR', lambda x: (x.astype(str).str.strip().str.upper() == 'SIM').sum())).reset_index()

                        df_novo = pd.merge(df_users, df_perf[['Chave_Nome', 'Aderência (%)', 'Conformidade (%)']], on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_ret[['Chave_Nome', 'RT geral valido', 'RT geral calculado', 'Taxa_Retencao_Original']], on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_chat_agg, on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_voz_agg, on='Chave_Nome', how='left')
                        df_novo = pd.merge(df_novo, df_pesq_agg, on='Chave_Nome', how='left')
                        df_novo['Nome Exibição'] = df_novo['Chave_Nome'].str.title()
                        df_novo['Mês'] = mes_up
                        df_novo['Ano'] = str(ano_up)
                        
                        enviar_para_github("dados_consolidados_master.csv", df_novo.to_csv(index=False))
                        st.cache_data.clear()
                        st.success("Base Mestre atualizada com sucesso!")
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

                df_calculado = df_calculado[
                    (df_calculado['Aderência (%)'] > 0) | 
                    (df_calculado['Conformidade (%)'] > 0) | 
                    (df_calculado['Vol. Chat'] > 0) | 
                    (df_calculado['Vol. Voz'] > 0)
                ].copy()

                st.subheader(f"🚨 Auditoria de Desvios de Metas Contratuais ({mes_view}/{ano_view})")
                df_ativos_alertas = df_calculado[df_calculado['Status_Dinamico'] == 'Ativo']
                
                lista_detratores_csat = df_ativos_alertas[df_ativos_alertas['CSAT_Agente (%)'] < META_CSAT]
                lista_detratores_ir = df_ativos_alertas[df_ativos_alertas['IR_Agente (%)'] < META_IR]
                detratores_retencao = df_ativos_alertas[df_ativos_alertas['% Retenção'] < META_RETENCAO]
                lista_detratores_conf = df_ativos_alertas[df_ativos_alertas['Conformidade (%)'] < META_CONFORMIDADE]
                lista_detratores_ade = df_ativos_alertas[df_ativos_alertas['Aderência (%)'] < META_ADERENCIA]
                
                total_desvios_qualidade = len(lista_detratores_csat) + len(lista_detratores_ir)

                c_a1, c_a2, c_a3, c_a4 = st.columns(4)
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

                st.subheader(f"🎯 Métricas Consolidadas ({filtro_agente})")
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>⭐ CSAT Ponderado</div><div class='kpi-value'>{v_csat:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_CSAT:.0f}%</div></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🎯 Índice IR</div><div class='kpi-value'>{v_ir:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_IR:.0f}%</div></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>📈 Taxa Retenção</div><div class='kpi-value'>{v_retencao:.2f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_RETENCAO:.0f}%</div></div>", unsafe_allow_html=True)
                with c4: st.markdown(f"<div class='kpi-card' style='border-left-color: #dc3545;'><div class='kpi-title'>📉 Taxa Cancelamento</div><div class='kpi-value'>{v_cancelamento:.2f}%</div><div style='font-size:11px;color:#dc3545;'>Complementar</div></div>", unsafe_allow_html=True)
                with c5: st.markdown(f"<div class='kpi-card' style='border-left-color: #9932cc;'><div class='kpi-title'>📅 Conformidade (Escala)</div><div class='kpi-value'>{v_conf:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_CONFORMIDADE:.0f}%</div></div>", unsafe_allow_html=True)

                cx0, cx1, cx2, cx3, cx4 = st.columns(5)
                with cx0: st.markdown(f"<div class='kpi-card' style='border-left-color: #ba55d3;'><div class='kpi-title'>⏱️ Aderência (Pausas)</div><div class='kpi-value'>{v_ade:.1f}%</div><div style='font-size:11px;color:#28a745;font-weight:bold;'>Meta: {META_ADERENCIA:.0f}%</div></div>", unsafe_allow_html=True)
                with cx1: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>💬 Vol. Total Chat</div><div class='kpi-value'>{int(total_vol_chat):,}</div></div>", unsafe_allow_html=True)
                with cx2: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>⏳ TMA Chat</div><div class='kpi-value'>{tma_chat_medio:.1f} min</div></div>", unsafe_allow_html=True)
                with cx3: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>📞 Vol. Total Voz</div><div class='kpi-value'>{int(total_vol_voz):,}</div></div>", unsafe_allow_html=True)
                with cx4: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>⏳ TMA Voz</div><div class='kpi-value'>{tma_voz_medio:.1f} min</div></div>", unsafe_allow_html=True)

                st.markdown("---")

                if filtro_agente == "Todos":
                    st.subheader("📊 Central de Auditoria Visual de Indicadores")
                    tab_graf_1, tab_graf_2, tab_graf_3 = st.tabs(["🏅 Rankings de Qualidade & Retenção", "⏱️ Rankings de Processos & Eficiência", "💬 Volumetria de Atendimentos"])
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
                        cx1, cx2, cx3, cx4 = st.columns(4)
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
                        with cx3:
                            fig_tmach = px.bar(df_chart_base.sort_values(by='TMA Chat (Min)', ascending=False).head(10), x='TMA Chat (Min)', y='Nome Exibição', orientation='h', title="⏳ Maiores TMAs Chat", color='TMA Chat (Min)', color_continuous_scale='Oranges', text='TMA Chat (Min)')
                            fig_tmach.update_traces(texttemplate='%{text:.1f}m', textposition='auto')
                            fig_tmach.update_yaxes(autorange="reversed")
                            st.plotly_chart(fig_tmach, use_container_width=True)
                        with cx4:
                            fig_tmavz = px.bar(df_chart_base.sort_values(by='TMA Voz (Min)', ascending=False).head(10), x='TMA Voz (Min)', y='Nome Exibição', orientation='h', title="⏳ Maiores TMAs Voz", color='TMA Voz (Min)', color_continuous_scale='Oranges', text='TMA Voz (Min)')
                            fig_tmavz.update_traces(texttemplate='%{text:.1f}m', textposition='auto')
                            fig_tmavz.update_yaxes(autorange="reversed")
                            st.plotly_chart(fig_tmavz, use_container_width=True)

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
                    st.markdown("---")

                st.subheader("👥 Detalhamento Operacional por Colaborador")
                colunas_tabela = ['Nome Exibição', 'Status_Dinamico', 'CSAT_Agente (%)', 'IR_Agente (%)', 'Conformidade (%)', 'Aderência (%)', 'Vol. Chat', 'TMA Chat (Min)']
                if 'TPC Chat (Seg)' in df_final_escopo.columns: colunas_tabela.append('TPC Chat (Seg)')
                colunas_tabela += ['Vol. Voz', 'TMA Voz (Min)']
                if 'TPC Voz (Seg)' in df_final_escopo.columns: colunas_tabela.append('TPC Voz (Seg)')
                colunas_tabela += ['RT geral valido', '% Retenção', '% Cancelamento']
                
                colunas_tabela = list(dict.fromkeys(colunas_tabela))
                
                def estilizar_linhas_status(row):
                    if str(row['Status_Dinamico']).strip().lower() != 'ativo': return ['background-color: #f1f3f5; color: #adb5bd; font-style: italic;'] * len(row)
                    return [''] * len(row)

                format_dict = {
                    'CSAT_Agente (%)': '{:.1f}%', 'IR_Agente (%)': '{:.1f}%', 'Aderência (%)': '{:.1f}%', 'Conformidade (%)': '{:.1f}%',
                    '% Retenção': '{:.2f}%', '% Cancelamento': '{:.2f}%', 'Vol. Chat': '{:,.0f}', 'TMA Chat (Min)': '{:.1f}m',
                    'Vol. Voz': '{:,.0f}', 'TMA Voz (Min)': '{:.1f}m', 'RT geral valido': '{:,.0f}'
                }
                if 'TPC Chat (Seg)' in df_final_escopo.columns: format_dict['TPC Chat (Seg)'] = '{:.1f}s'
                if 'TPC Voz (Seg)' in df_final_escopo.columns: format_dict['TPC Voz (Seg)'] = '{:.1f}s'

                st.dataframe(df_final_escopo[colunas_tabela].style.apply(estilizar_linhas_status, axis=1).format(format_dict), use_container_width=True)

    # ==========================================
    # VISÃO DO AGENTE NOMINAL LOGADO (GAMIFICADO)
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

                col_email_periodo = 'E-MAIL' if 'E-MAIL' in df_periodo.columns else 'E-mail'
                meus_dados = df_periodo[df_periodo[col_email_periodo].str.strip().str.lower() == st.session_state.user_email.strip().lower()]
                
                if not meus_dados.empty:
                    dados = meus_dados.iloc[0]
                    tem_colunas_novas = 'Total_Pesq_CSAT' in df_periodo.columns
                    my_csat = (dados['Boas_Pesq_CSAT'] / dados['Total_Pesq_CSAT'] * 100) if tem_colunas_novas and dados['Total_Pesq_CSAT'] > 0 else 0.0
                    my_ir = (dados['Sim_Pesq_IR'] / dados['Total_Pesq_IR'] * 100) if tem_colunas_novas and dados['Total_Pesq_IR'] > 0 else 0.0
                    my_tx_ret = dados['Taxa_Retencao_Original'] if 'Taxa_Retencao_Original' in dados else 0.0
                    
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
                    ca1, ca2, ca3, ca4 = st.columns(4)
                    with ca1: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Meu CSAT</div><div class='kpi-value'>{my_csat:.1f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_CSAT:.0f}%</div></div>", unsafe_allow_html=True)
                    with ca2: st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Meu Índice IR</div><div class='kpi-value'>{my_ir:.1f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_IR:.0f}%</div></div>", unsafe_allow_html=True)
                    with ca3: st.markdown(f"<div class='kpi-card' style='border-left-color: #9932cc;'><div class='kpi-title'>Conformidade (Escala)</div><div class='kpi-value'>{dados['Conformidade (%)']:.1f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_CONFORMIDADE:.0f}%</div></div>", unsafe_allow_html=True)
                    with ca4: st.markdown(f"<div class='kpi-card' style='border-left-color: #ba55d3;'><div class='kpi-title'>Aderência (Pausas)</div><div class='kpi-value'>{dados['Aderência (%)']:.1f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_ADERENCIA:.0f}%</div></div>", unsafe_allow_html=True)

                    st.markdown("### 🎧 Produtividade")
                    co1, co2, co3, co4 = st.columns(4)
                    with co1: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>Chats Atendidos</div><div class='kpi-value'>{int(dados['Vol. Chat']) if pd.notna(dados['Vol. Chat']) else 0}</div></div>", unsafe_allow_html=True)
                    with co2: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>Meu TMA Chat</div><div class='kpi-value'>{dados['TMA Chat (Min)']:.1f}m</div></div>", unsafe_allow_html=True)
                    
                    val_tpc_chat = f"{dados['TPC Chat (Seg)']:.1f}s" if 'TPC Chat (Seg)' in df_periodo.columns else "--"
                    with co3: st.markdown(f"<div class='kpi-card' style='border-left-color: #17a2b8;'><div class='kpi-title'>Meu TPC Chat</div><div class='kpi-value'>{val_tpc_chat}</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_TPC:.0f}s</div></div>", unsafe_allow_html=True)
                    with co4: st.markdown(f"<div class='kpi-card' style='border-left-color: #28a745;'><div class='kpi-title'>Taxa de Retenção</div><div class='kpi-value'>{my_tx_ret:.2f}%</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_RETENCAO:.0f}%</div></div>", unsafe_allow_html=True)

                    cv1, cv2, cv3, cv4 = st.columns(4)
                    with cv1: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Chamadas Voz</div><div class='kpi-value'>{int(dados['Vol. Voz']) if pd.notna(dados['Vol. Voz']) else 0}</div></div>", unsafe_allow_html=True)
                    with cv2: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Meu TMA Voz</div><div class='kpi-value'>{dados['TMA Voz (Min)']:.1f}m</div></div>", unsafe_allow_html=True)
                    
                    val_tpc_voz = f"{dados['TPC Voz (Seg)']:.1f}s" if 'TPC Voz (Seg)' in df_periodo.columns else "--"
                    with cv3: st.markdown(f"<div class='kpi-card' style='border-left-color: #ffc107;'><div class='kpi-title'>Meu TPC Voz</div><div class='kpi-value'>{val_tpc_voz}</div><div style='font-size:11px;color:#6c757d;margin-top:5px;'>Meta: {META_TPC:.0f}s</div></div>", unsafe_allow_html=True)
                    with cv4: pass
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
