import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard do Gestor", page_icon="📈", layout="wide")

st.title("📈 Painel Administrativo do Gestor")
st.markdown("Faça o upload do relatório de Aderência/Conformidade para atualizar os indicadores.")

# 1. ÁREA DE UPLOAD DO ARQUIVO
arquivo_upload = st.file_uploader("📥 Suba o arquivo CSV de Aderência e Conformidade", type=["csv"])

if arquivo_upload is not None:
    # 2. LENDO E TRATANDO OS DADOS
    try:
        # Lê o arquivo que o usuário subiu
        df = pd.read_csv(arquivo_upload)
        
        # Função para limpar as colunas de porcentagem (tira o '%' e troca ',' por '.')
        def limpar_porcentagem(valor):
            if pd.isna(valor):
                return 0.0
            valor_str = str(valor).replace('%', '').replace(',', '.')
            # Trata o caso de vir 'NaN' escrito como texto no seu CSV
            if valor_str.lower() == 'nan':
                return 0.0
            return float(valor_str)

        # Aplicando a limpeza nas colunas
        df['Aderência (%)'] = df['Aderência (%)'].apply(limpar_porcentagem)
        df['Conformidade (%)'] = df['Conformidade (%)'].apply(limpar_porcentagem)
        
        st.success("Arquivo carregado e processado com sucesso!")
        
        # 3. FILTROS
        st.sidebar.header("Filtros de Gestão")
        agentes = ["Todos"] + list(df['Agente'].dropna().unique())
        filtro_agente = st.sidebar.selectbox("Filtrar por Agente:", agentes)
        
        if filtro_agente != "Todos":
            df_filtrado = df[df['Agente'] == filtro_agente]
        else:
            df_filtrado = df.copy()

        # 4. CARDS DE INDICADORES (MÉDIAS)
        st.subheader("🎯 Resumo de Aderência e Conformidade")
        
        media_aderencia = df_filtrado['Aderência (%)'].mean()
        media_conformidade = df_filtrado['Conformidade (%)'].mean()
        total_excecoes = df_filtrado['Exceções'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Média Aderência", value=f"{media_aderencia:.2f}%")
        col2.metric(label="Média Conformidade", value=f"{media_conformidade:.2f}%")
        col3.metric(label="Total de Exceções", value=total_excecoes)
        
        st.markdown("---")
        
        # 5. DETALHAMENTO E GRÁFICOS
        st.subheader("👥 Performance Comparativa da Equipe")
        
        aba1, aba2 = st.tabs(["📊 Gráficos", "📋 Tabela Completa"])
        
        with aba1:
            c1, c2 = st.columns(2)
            with c1:
                fig_aderencia = px.bar(
                    df_filtrado.sort_values(by="Aderência (%)", ascending=False), 
                    x='Agente', y='Aderência (%)',
                    title="Aderência por Agente",
                    text_auto='.2f',
                    color='Aderência (%)',
                    color_continuous_scale="Viridis"
                )
                st.plotly_chart(fig_aderencia, use_container_width=True)
                
            with c2:
                fig_conformidade = px.bar(
                    df_filtrado.sort_values(by="Conformidade (%)", ascending=False), 
                    x='Agente', y='Conformidade (%)',
                    title="Conformidade por Agente",
                    text_auto='.2f',
                    color='Conformidade (%)',
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig_conformidade, use_container_width=True)
                
        with aba2:
            st.dataframe(
                df_filtrado.style.format({
                    'Aderência (%)': '{:.2f}%',
                    'Conformidade (%)': '{:.2f}%'
                }),
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        st.info("Certifique-se de que o CSV possui as colunas 'Agente', 'Aderência (%)' e 'Conformidade (%)'.")

else:
    st.info("👆 Por favor, faça o upload do arquivo CSV na caixa acima para visualizar os dados.")
