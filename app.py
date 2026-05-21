import streamlit as st
import pandas as pd
import plotly.express as px
from github import Github

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Sistema Operacional 360", page_icon="🎯", layout="wide")

# ==========================================
# FUNÇÕES GERAIS E TRATAMENTO DE DADOS
# ==========================================
def limpar_porcentagem(valor):
    if pd.isna(valor):
        return 0.0
    valor_str = str(valor).replace('%', '').replace(',', '.')
    if valor_str.lower() == 'nan':
        return 0.0
    return float(valor_str)

def calcular_ir(serie_ir):
    validos = serie_ir.dropna()
    if len(validos) == 0:
        return 0.0
    qtd_sim = (validos.str.strip().str.upper() == 'SIM').sum()
    return (qtd_sim / len(validos)) * 100

def ms_para_minutos(ms):
    if pd.isna(ms):
        return 0.0
    return ms / 1000 / 60

# Função para enviar/atualizar ficheiros no GitHub
def enviar_para_github(nome_arquivo_git, arquivo_carregado):
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        conteudo = arquivo_carregado.getvalue()
        
        try:
            arquivo_existente = repo.get_contents(nome_arquivo_git)
            repo.update_file(
                arquivo_existente.path,
                f"Atualização automática via Streamlit: {nome_arquivo_git}",
                conteudo,
                arquivo_existente.sha
            )
            return True, f"O ficheiro {nome_arquivo_git} foi atualizado com sucesso!"
        except Exception:
            repo.create_file(
                nome_arquivo_git,
                f"Criação automática via Streamlit: {nome_arquivo_git}",
                conteudo
            )
            return True, f"O ficheiro {nome_arquivo_git} foi criado com sucesso!"
            
    except Exception as e:
        return False, f"Erro na ligação ao GitHub: {e}"

# ==========================================
# MENU DE NAVEGAÇÃO SUPERIOR (ABAS)
# ==========================================
aba_dashboard, aba_upload = st.tabs(["📊 Dashboard de Indicadores", "⚙️ Administração e Envio de Dados"])

# ==========================================
# ABA 1: ENVIO DE FICHEIROS (ADMIN)
# ==========================================
with aba_upload:
    st.header("⚙️ Atualização da Base de Dados")
    st.markdown("Faça o upload dos ficheiros para atualizar a base oficial no GitHub. O Dashboard será atualizado automaticamente.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Qualidade")
        up_aderencia = st.file_uploader("1. Aderência e Conformidade (CSV)", type=["csv"], key="up_ad")
        if up_aderencia and st.button("Salvar Aderência"):
            with st.spinner("A enviar..."):
                sucesso, msg = enviar_para_github("dados_aderencia.csv", up_aderencia)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)
                    
        up_pesquisa = st.file_uploader("2. Pesquisa CSAT/IR (CSV)", type=["csv"], key="up_pesq")
        if up_pesquisa and st.button("Salvar Pesquisa"):
            with st.spinner("A enviar..."):
                sucesso, msg = enviar_para_github("dados_pesquisa.csv", up_pesquisa)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)

    with col2:
        st.subheader("Operação")
        up_chat = st.file_uploader("3. Relatório de Chat (CSV)", type=["csv"], key="up_ch")
        if up_chat and st.button("Salvar Chat"):
            with st.spinner("A enviar..."):
                sucesso, msg = enviar_para_github("dados_chat.csv", up_chat)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)
                    
        up_voz = st.file_uploader("4. Relatório de Voz (CSV)", type=["csv"], key="up_voz")
        if up_voz and st.button("Salvar Voz"):
            with st.spinner("A enviar..."):
                sucesso, msg = enviar_para_github("dados_voz.csv", up_voz)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)

    with col3:
        st.subheader("Retenção e Acessos")
        up_retencao = st.file_uploader("5. Relatório de Retenção (CSV)", type=["csv"], key="up_ret")
        if up_retencao and st.button("Salvar Retenção"):
            with st.spinner("A enviar..."):
                sucesso, msg = enviar_para_github("dados_retencao.csv", up_retencao)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)
                    
        up_usuarios = st.file_uploader("6. Lista de Utilizadores (CSV)", type=["csv"], key="up_usr")
        if up_usuarios and st.button("Salvar Utilizadores"):
            with st.spinner("A enviar..."):
                sucesso, msg = enviar_para_github("dados_usuarios.csv", up_usuarios)
                if sucesso:
                    st.success(msg)
                else:
                    st.error(msg)

# ==========================================
# ABA 2: DASHBOARD (LEITURA)
# ==========================================
with aba_dashboard:
    st.sidebar.title("Navegação")
    perfil = st.sidebar.radio("Selecione o seu perfil:", ["Gestor", "Agente"])
    st.sidebar.markdown("---")
    
    # IMPORTANTE: SUBSTITUA 'SEU_USUARIO' E 'SEU_REPO' ABAIXO PELOS SEUS DADOS!
    BASE_URL = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/"
    
    try:
        # Lendo diretamente do GitHub
        df_perf = pd.read_csv(f"{BASE_URL}dados_aderencia.csv")
        df_ret = pd.read_csv(f"{BASE_URL}dados_retencao.csv")
        df_users = pd.read_csv(f"{BASE_URL}dados_usuarios.csv")
        df_chat = pd.read_csv(f"{BASE_URL}dados_chat.csv")
        df_voz = pd.read_csv(f"{BASE_URL}dados_voz.csv")
        df_pesq = pd.read_csv(f"{BASE_URL}dados_pesquisa.csv")
        
        # ------------------------------------------
        # TRATAMENTO DE DADOS (PREPARAÇÃO)
        # ------------------------------------------
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

        # MESCLANDO TUDO
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
            
            agentes = ["Todos"] + list(df_completo['Nome Exibição'].dropna().unique())
            filtro_agente = st.selectbox("Filtrar visualização por Agente:", agentes)
            
            if filtro_agente != "Todos":
                df_view = df_completo[df_completo['Nome Exibição'] == filtro_agente]
            else:
                df_view = df_completo.copy()

            st.subheader("🎯 KPIs Globais")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Média CSAT", f"{df_view['CSAT_Media'].mean():.2f}")
            col2.metric("Média IR", f"{df_view['IR_Percentual'].mean():.2f}%")
            col3.metric("Média Aderência", f"{df_view['Aderência (%)'].mean():.2f}%")
            col4.metric("Média Conformidade", f"{df_view['Conformidade (%)'].mean():.2f}%")
            st.markdown("---")
            
            st.subheader("🎧 Volume e Tempos de Atendimento")
            c_op1, c_op2, c_op3, c_op4 = st.columns(4)
            c_op1.metric("Total Vol. Chat", int(df_view['Vol. Chat'].sum()))
            c_op2.metric("TMA Médio Chat", f"{df_view['TMA Chat (Min)'].mean():.1f} min")
            c_op3.metric("Total Vol. Voz", int(df_view['Vol. Voz'].sum()))
            c_op4.metric("TMA Médio Voz", f"{df_view['TMA Voz (Min)'].mean():.1f} min")
            st.markdown("---")
            
            st.subheader("👥 Visão Consolidada por Agente")
            colunas_exibicao = [
                'Nome Exibição', 'CSAT_Media', 'IR_Percentual', 'Aderência (%)', 'Conformidade (%)',
                'Vol. Chat', 'TMA Chat (Min)', 'Vol. Voz', 'TMA Voz (Min)', 'RT geral', 'RT geral valido'
            ]
            df_tabela = df_view[colunas_exibicao].copy()
            df_tabela['% Retenção'] = (df_tabela['RT geral valido'] / df_tabela['RT geral']) * 100
            
            st.dataframe(df_tabela.style.format({
                'CSAT_Media': '{:.2f}', 'IR_Percentual': '{:.2f}%', 'Aderência (%)': '{:.2f}%', 
                'Conformidade (%)': '{:.2f}%', '% Retenção': '{:.2f}%', 
                'TMA Chat (Min)': '{:.1f}m', 'TMA Voz (Min)': '{:.1f}m'
            }), use_container_width=True)

        # ==========================================
        # VISÃO DO AGENTE
        # ==========================================
        elif perfil == "Agente":
            st.title("👤 O Meu Painel de Performance")
            
            lista_emails = df_completo['E-mail'].dropna().unique()
            email_selecionado = st.selectbox("Selecione o seu e-mail corporativo:", ["Selecione..."] + list(lista_emails))
            
            if email_selecionado != "Selecione...":
                meus_dados = df_completo[df_completo['E-mail'] == email_selecionado].iloc[0]
                st.success(f"Olá, **{meus_dados['Nome Exibição']}**! Estes são os seus resultados.")
                
                st.markdown("### ⭐ Satisfação e Qualidade")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Minha Nota CSAT", f"{meus_dados['CSAT_Media']:.2f}" if pd.notna(meus_dados['CSAT_Media']) else "N/A")
                c2.metric("Meu IR (%)", f"{meus_dados['IR_Percentual']:.2f}%" if pd.notna(meus_dados['IR_Percentual']) else "N/A")
                c3.metric("Minha Aderência", f"{meus_dados['Aderência (%)']:.2f}%" if pd.notna(meus_dados['Aderência (%)']) else "N/A")
                c4.metric("Minha Conformidade", f"{meus_dados['Conformidade (%)']:.2f}%" if pd.notna(meus_dados['Conformidade (%)']) else "N/A")
                st.markdown("---")
                
                st.markdown("### 🎧 Operação (Chat / Voz)")
                co1, co2, co3, co4 = st.columns(4)
                co1.metric("Volume Chat", int(meus_dados['Vol. Chat']) if pd.notna(meus_dados['Vol. Chat']) else 0)
                co2.metric("Meu TMA Chat", f"{meus_dados['TMA Chat (Min)']:.1f} min" if pd.notna(meus_dados['TMA Chat (Min)']) else "N/A")
                co3.metric("Volume Voz", int(meus_dados['Vol. Voz']) if pd.notna(meus_dados['Vol. Voz']) else 0)
                co4.metric("Meu TMA Voz", f"{meus_dados['TMA Voz (Min)']:.1f} min" if pd.notna(meus_dados['TMA Voz (Min)']) else "N/A")
                st.markdown("---")
                
                st.markdown("### 💰 Retenção")
                rt_geral = meus_dados['RT geral']
                rt_valido = meus_dados['RT geral valido']
                minha_tx_ret = (rt_valido / rt_geral * 100) if pd.notna(rt_geral) and rt_geral > 0 else 0
                
                cr1, cr2, cr3 = st.columns(3)
                cr1.metric("Volume Geral Tratado", int(rt_geral) if pd.notna(rt_geral) else 0)
                cr2.metric("Volume Geral Retido", int(rt_valido) if pd.notna(rt_valido) else 0)
                cr3.metric("Taxa de Retenção", f"{minha_tx_ret:.2f}%")

            else:
                st.info("👆 Por favor, selecione o seu e-mail acima.")

    except Exception as e:
        st.warning("⚠️ Os ficheiros ainda não foram carregados no GitHub, ou as ligações não estão corretas.")
        st.info("Vá à aba 'Administração e Envio de Dados' e submeta os 6 ficheiros.")
        # Opcional: mostrar erro técnico para ajudar a depurar (pode remover depois)
        st.write(f"Detalhe do erro técnico: {e}")
