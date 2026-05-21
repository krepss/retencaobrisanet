import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Dashboard de Indicadores", layout="wide")

# 1. Função para carregar os dados do GitHub
# O decorador @st.cache_data faz com que o Streamlit memorize os dados 
# e não baixe o CSV do GitHub toda vez que a tela for atualizada.
@st.cache_data(ttl=600) # ttl=600 atualiza o cache a cada 10 minutos
def carregar_dados():
    # Substitua pela sua URL RAW do GitHub
    url = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPOSITORIO/main/seus_dados.csv"
    
    # Exemplo caso o CSV tenha separador por ponto e vírgula, use sep=';'
    df = pd.read_csv(url) 
    return df

# 2. Carregar os dados
try:
    dados = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# 3. Construindo a Interface
st.title("📊 Painel de Acompanhamento de Indicadores")
st.markdown("---")

# Mostrando uma prévia da tabela (opcional)
with st.expander("Visualizar Dados Brutos"):
    st.dataframe(dados)

# 4. Criando Indicadores (KPIs)
# Supondo que você tenha colunas como 'Faturamento' e 'Clientes' no seu CSV
st.subheader("Resumo do Mês")
col1, col2, col3 = st.columns(3)

with col1:
    # Exemplo genérico: pegando a soma de uma coluna 'Vendas'
    # total_vendas = dados['Vendas'].sum()
    st.metric(label="Total de Vendas", value="R$ 15.000", delta="1.2%")

with col2:
    st.metric(label="Novos Clientes", value="142", delta="-5%")

with col3:
    st.metric(label="NPS", value="85", delta="2 pontos")

# 5. Criando Gráficos
st.markdown("---")
st.subheader("Evolução Diária")

# O Streamlit tem gráficos nativos muito fáceis de usar
# Supondo que você tenha uma coluna 'Data' e 'Valor'
# st.line_chart(dados, x='Data', y='Valor')

# Como não conheço suas colunas, vou deixar um comando genérico
st.info("Aqui você pode inserir seus gráficos usando st.line_chart(), st.bar_chart() ou bibliotecas como Plotly.")
