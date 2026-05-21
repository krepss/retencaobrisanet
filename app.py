import streamlit as st
import pandas as pd
import plotly.express as px  # Usaremos para gráficos dinâmicos

# 1. Configuração da Página
st.set_page_config(page_title="Dashboard do Gestor", page_icon="📈", layout="wide")

st.title("📈 Painel Administrativo do Gestor")
st.markdown("Acompanhamento de Indicadores de Qualidade, Aderência e Taxas de Retenção.")

# 2. Link do seu CSV no GitHub (Substitua pelo seu link RAW)
URL_DO_CSV = "https://raw.githubusercontent.com/seu_usuario/seu_repositorio/main/seuarquivo.csv"

@st.cache_data
def carregar_dados(url):
    # Em produção, use a linha abaixo:
    # return pd.read_csv(url)
    
    # --- SIMULAÇÃO DE DADOS (Remova este bloco quando colocar o link real) ---
    import numpy as np
    np.random.seed(42)
    dados_mock = {
        'responsavel': ['Ana Silva', 'Bruno Costa', 'Carlos Souza', 'Daniela Lima'] * 25,
        'IR': np.random.uniform(85, 98, 100),
        'CSAT': np.random.uniform(70, 95, 100),
        'ADERENCIA': np.random.uniform(80, 100, 100),
        'CONFORMIDADE': np.random.uniform(90, 100, 100),
        'RT_fibra_FWA_5G': np.random.randint(50, 150, 100),
        'RT_fibra_FWA_5G_validas': np.random.randint(40, 140, 100),
        'RT_de_adicional': np.random.randint(30, 90, 100),
        'RT_de_adicional_Validas': np.random.randint(25, 85, 100),
        'RT_geral': np.random.randint(100, 300, 100),
        'RT_geral_valido': np.random.randint(80, 280, 100),
    }
    df = pd.DataFrame(dados_mock)
    # Cálculo da porcentagem de retenção geral (Válidos / Total)
    df['% de retenção'] = (df['RT_geral_valido'] / df['RT_geral']) * 100
    return df
    # ------------------------------------------------------------------------

# Carregando dados
try:
    df_original = carregar_dados(URL_DO_CSV)
    
    # 3. BARRA LATERAL (Filtros Administrativos)
    st.sidebar.header("Filtros de Gestão")
    
    # Filtro de Responsável
    responsaveis = ["Todos"] + list(df_original['responsavel'].unique())
    filtro_resp = st.sidebar.selectbox("Filtrar por Responsável/Supervisor:", responsaveis)
    
    # Aplicando o filtro no DataFrame
    if filtro_resp != "Todos":
        df_filtrado = df_original[df_original['responsavel'] == filtro_resp]
    else:
        df_filtrado = df_original.copy()

    # 4. CARDs - INDICADORES PRINCIPAIS (MÉDIAS GERAIS)
    st.subheader("🎯 Principais Indicadores de Performance")
    
    # Calculando métricas agrupadas para os cards
    media_ir = df_filtrado['IR'].mean()
    media_csat = df_filtrado['CSAT'].mean()
    media_aderencia = df_filtrado['ADERENCIA'].mean()
    media_conformidade = df_filtrado['CONFORMIDADE'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Média IR (Índice de Resolução)", value=f"{media_ir:.2f}%")
    col2.metric(label="Média CSAT", value=f"{media_csat:.2f}%")
    col3.metric(label="Média Aderência", value=f"{media_aderencia:.2f}%")
    col4.metric(label="Média Conformidade", value=f"{media_conformidade:.2f}%")
    
    st.markdown("---")
    
    # 5. BLOCO DE RETENÇÃO (Volume e Taxas)
    st.subheader("📊 Taxas Referentes à Retenção")
    
    # Consolidação dos volumes de retenção
    tot_fibra = df_filtrado['RT_fibra_FWA_5G'].sum()
    tot_fibra_val = df_filtrado['RT_fibra_FWA_5G_validas'].sum()
    tot_adic = df_filtrado['RT_de_adicional'].sum()
    tot_adic_val = df_filtrado['RT_de_adicional_Validas'].sum()
    tot_geral = df_filtrado['RT_geral'].sum()
    tot_geral_val = df_filtrado['RT_geral_valido'].sum()
    
    # Taxa de retenção consolidada do período/filtro
    tx_retencao_total = (tot_geral_val / tot_geral) * 100 if tot_geral > 0 else 0
    
    # Exibição em colunas dos volumes e taxa final
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.write("**Fibra / FWA / 5G**")
        st.write(f"Total: {tot_fibra}")
        st.write(f"Válidas: {tot_fibra_val}")
        st.caption(f"Aproveitamento: {(tot_fibra_val/tot_fibra)*100:.1f}%" if tot_fibra > 0 else "0%")
        
    with c2:
        st.write("**Adicional**")
        st.write(f"Total: {tot_adic}")
        st.write(f"Válidas: {tot_adic_val}")
        st.caption(f"Aproveitamento: {(tot_adic_val/tot_adic)*100:.1f}%" if tot_adic > 0 else "0%")
        
    with c3:
        st.write("**Volume Geral**")
        st.write(f"Total Geral: {tot_geral}")
        st.write(f"Geral Válido: {tot_geral_val}")
        
    with c4:
        # Card de destaque para a Porcentagem de Retenção
        st.metric(label="🔥 % de Retenção Geral", value=f"{tx_retencao_total:.2f}%")

    st.markdown("---")

    # 6. DETALHAMENTO POR RESPONSÁVEL (Visão Tabela e Gráfico)
    st.subheader("👥 Performance Comparativa por Responsável")
    
    # Agrupando os dados por responsável para o gestor comparar a equipe
    df_gestor = df_original.groupby('responsavel').agg({
        'IR': 'mean',
        'CSAT': 'mean',
        'ADERENCIA': 'mean',
        'CONFORMIDADE': 'mean',
        'RT_fibra_FWA_5G': 'sum',
        'RT_fibra_FWA_5G_validas': 'sum',
        'RT_de_adicional': 'sum',
        'RT_de_adicional_Validas': 'sum',
        'RT_geral': 'sum',
        'RT_geral_valido': 'sum'
    }).reset_index()
    
    df_gestor['% de Retenção Geral'] = (df_gestor['RT_geral_valido'] / df_gestor['RT_geral']) * 100

    aba_tab, aba_graf = st.tabs(["📋 Tabela Consolidada", "📊 Gráfico de Retenção"])
    
    with aba_tab:
        # Exibe a tabela formatada para o gestor
        st.dataframe(
            df_gestor.style.format({
                'IR': '{:.2f}%', 'CSAT': '{:.2f}%', 'ADERENCIA': '{:.2f}%', 
                'CONFORMIDADE': '{:.2f}%', '% de Retenção Geral': '{:.2f}%'
            }), 
            use_container_width=True
        )
        
    with aba_graf:
        # Gráfico comparando a % de retenção de cada responsável
        fig = px.bar(
            df_gestor, 
            x='responsavel', 
            y='% de Retenção Geral',
            title="Porcentagem de Retenção Geral por Responsável",
            text_auto='.2f',
            color='% de Retenção Geral',
            color_continuous_scale=px.colors.sequential.Bluered
        )
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao estruturar o painel do gestor: {e}")
