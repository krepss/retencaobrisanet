import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Performance", page_icon="🎯", layout="wide")

# Função para limpar as porcentagens
def limpar_porcentagem(valor):
    if pd.isna(valor):
        return 0.0
    valor_str = str(valor).replace('%', '').replace(',', '.')
    if valor_str.lower() == 'nan':
        return 0.0
    return float(valor_str)

# 1. BARRA LATERAL - NAVEGAÇÃO DE PERFIL
st.sidebar.title("Navegação")
perfil = st.sidebar.radio("Selecione o seu perfil:", ["Gestor", "Agente"])
st.sidebar.markdown("---")

# 2. ÁREA DE UPLOAD DE ARQUIVOS (Na barra lateral para não poluir a tela principal)
st.sidebar.subheader("📥 Upload de Dados")
arquivo_aderencia = st.sidebar.file_uploader("1. Relatório de Aderência (CSV)", type=["csv"])
arquivo_usuarios = st.sidebar.file_uploader("2. Lista de Usuários/Equipe (CSV)", type=["csv"])

# Lógica principal se os arquivos foram carregados
if arquivo_aderencia is not None and arquivo_usuarios is not None:
    try:
        # Lendo os dados
        df_perf = pd.read_csv(arquivo_aderencia)
        df_users = pd.read_csv(arquivo_usuarios)
        
        # Tratando os dados de performance
        df_perf['Aderência (%)'] = df_perf['Aderência (%)'].apply(limpar_porcentagem)
        df_perf['Conformidade (%)'] = df_perf['Conformidade (%)'].apply(limpar_porcentagem)
        
        # Padronizando os nomes para garantir que o cruzamento funcione 
        # (transforma tudo em maiúsculo e tira espaços sobrando)
        df_perf['Agente'] = df_perf['Agente'].str.strip().str.upper()
        df_users['Nome'] = df_users['Nome'].str.strip().str.upper()
        
        # Mesclando (juntando) os dados de performance com os emails da lista de usuários
        # Usamos left join para manter todos da performance, mesmo se faltar email
        df_completo = pd.merge(df_perf, df_users, left_on='Agente', right_on='Nome', how='left')
        
        # ==========================================
        # VISÃO DO GESTOR
        # ==========================================
        if perfil == "Gestor":
            st.title("📈 Painel Administrativo do Gestor")
            
            # Filtro opcional na tela principal
            agentes = ["Todos"] + list(df_completo['Agente'].dropna().unique())
            filtro_agente = st.selectbox("Filtrar visualização por Agente:", agentes)
            
            if filtro_agente != "Todos":
                df_view = df_completo[df_completo['Agente'] == filtro_agente]
            else:
                df_view = df_completo.copy()

            st.subheader("🎯 Resumo de Aderência e Conformidade")
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Média Aderência", value=f"{df_view['Aderência (%)'].mean():.2f}%")
            col2.metric(label="Média Conformidade", value=f"{df_view['Conformidade (%)'].mean():.2f}%")
            col3.metric(label="Total de Exceções", value=df_view['Exceções'].sum())
            
            st.markdown("---")
            st.subheader("👥 Performance Comparativa da Equipe")
            
            c1, c2 = st.columns(2)
            with c1:
                fig_aderencia = px.bar(
                    df_view.sort_values(by="Aderência (%)", ascending=False), 
                    x='Agente', y='Aderência (%)', title="Aderência por Agente",
                    text_auto='.2f', color='Aderência (%)', color_continuous_scale="Viridis"
                )
                st.plotly_chart(fig_aderencia, use_container_width=True)
            with c2:
                fig_conf = px.bar(
                    df_view.sort_values(by="Conformidade (%)", ascending=False), 
                    x='Agente', y='Conformidade (%)', title="Conformidade por Agente",
                    text_auto='.2f', color='Conformidade (%)', color_continuous_scale="Blues"
                )
                st.plotly_chart(fig_conf, use_container_width=True)

        # ==========================================
        # VISÃO DO AGENTE (INDIVIDUAL)
        # ==========================================
        elif perfil == "Agente":
            st.title("👤 Meu Painel de Performance")
            st.markdown("Selecione seu e-mail para visualizar seus indicadores individuais.")
            
            # Simulação de Login (Seleção de E-mail)
            lista_emails = df_users['E-mail'].dropna().unique()
            email_selecionado = st.selectbox("E-mail corporativo:", ["Selecione..."] + list(lista_emails))
            
            if email_selecionado != "Selecione...":
                # Filtra os dados apenas para o agente logado
                meus_dados = df_completo[df_completo['E-mail'] == email_selecionado]
                
                if not meus_dados.empty:
                    nome_agente = meus_dados.iloc[0]['Agente']
                    st.success(f"Olá, **{nome_agente.title()}**! Bem-vindo(a) ao seu painel.")
                    
                    st.markdown("### Seus Resultados Cadastrados")
                    
                    # Cards Individuais
                    m_aderencia = meus_dados.iloc[0]['Aderência (%)']
                    m_conformidade = meus_dados.iloc[0]['Conformidade (%)']
                    m_excecoes = meus_dados.iloc[0]['Exceções']
                    
                    c1, c2, c3 = st.columns(3)
                    
                    # Definindo metas visuais (Ex: verde se > 95%, vermelho se menor)
                    delta_ad = "Na Meta" if m_aderencia >= 95 else "Abaixo da Meta"
                    delta_color_ad = "normal" if m_aderencia >= 95 else "inverse"
                    
                    c1.metric("Minha Aderência", f"{m_aderencia:.2f}%", delta=delta_ad, delta_color=delta_color_ad)
                    c2.metric("Minha Conformidade", f"{m_conformidade:.2f}%")
                    c3.metric("Minhas Exceções", m_excecoes)
                    
                    st.markdown("---")
                    st.subheader("Detalhes dos Registros")
                    
                    # Mostra a tabela apenas do operador
                    colunas_exibicao = ['Agente', 'Aderência (%)', 'Conformidade (%)', 'Exceções', 'Impacto líquido']
                    st.dataframe(meus_dados[colunas_exibicao].style.format({
                        'Aderência (%)': '{:.2f}%',
                        'Conformidade (%)': '{:.2f}%'
                    }), use_container_width=True)
                    
                else:
                    st.warning("Nenhum dado de performance encontrado para este e-mail nesta base.")
            else:
                st.info("👆 Por favor, selecione seu e-mail acima.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os arquivos: {e}")

else:
    st.info("👈 Gestor, por favor, faça o upload dos dois arquivos CSV (Aderência e Usuários) no menu lateral para liberar o sistema.")
