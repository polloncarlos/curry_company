# ====================================================================
# ==========================BIBLIOTECAS=============================
# ====================================================================

from haversine import haversine

# ====================================================================
# ==========================BIBLIOTECAS NECESSARIAS=============================
# ====================================================================

import pandas as pd
import streamlit as st
from PIL import Image
from datetime import datetime

st.set_page_config( page_title='Visão Entregadores', page_icon='🚴‍♂️', layout='wide')

# ====================================================================
# ==========================IMPORTAR CSV=============================
# ====================================================================

df = pd.read_csv("dataset/train.csv")
df_copy = df

# ====================================================================
# ==========================FUNCOES=============================
# ====================================================================

def clean_code(df):
    """ Esta função tem a responsabilidade de limpar o DataFrame

            Tipos de limpeza:
            
            Remoção dos dados NaN
            Mudança do tipo da coluna
            Remoção dos espaços das variáveis de texto
            Formatação da coluna de datas
            impeza da coluna de tempo (remoção do texto da variável numérica)
            
            Input: DataFrame
            Output: DataFrame  
    """
    # REMOVENDO ESPAÇOS DE TODA COLUNA QUE POSSUA TEXTO
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

    # REMOVENDO NaN DAS COLUNAS QUE IREI TROCAR OS TIPOS
    colunas_limpeza = ['Delivery_person_Age', 'multiple_deliveries', 'Festival', 
                       'Weatherconditions', 'City', 'Time_taken(min)']

    for coluna in colunas_limpeza:
        df = df[df[coluna].str.lower().str.strip() != 'nan']

    # REINICIANDO O INDEX
    df = df.reset_index(drop=True)

    # ALTERANDO OS TIPOS DAS COLUNAS
    df['Delivery_person_Age'] = df['Delivery_person_Age'].astype(int)
    df['Delivery_person_Ratings'] = df['Delivery_person_Ratings'].astype(float)
    df['multiple_deliveries'] = df['multiple_deliveries'].astype(int)
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y')

    # LIMPANDO COLUNA DE TEMPO
    df['Time_taken(min)'] = df['Time_taken(min)'].astype(str).str.extract(r'(\d+)')
    df['Time_taken(min)'] = pd.to_numeric(df['Time_taken(min)'], errors='coerce')

    # ADICIONANDO COLUNA DIA DA SEMANA
    df['week_of_year'] = df['Order_Date'].dt.strftime('%U').astype(int)

    # DISTÂNCIA ENTRE RESTAURANTE E LOCAL DE ENTREGA
    df['distance_delivery'] = df.loc[:, ['Restaurant_latitude', 'Restaurant_longitude', 
                                         'Delivery_location_latitude', 'Delivery_location_longitude']].apply(
        lambda x: haversine((x['Restaurant_latitude'], x['Restaurant_longitude']),
                            (x['Delivery_location_latitude'], x['Delivery_location_longitude'])),
        axis=1
    )

    return df


def top_delivery(df1, top_geral, top_velocidade):
    """ Esta função tem a responsabilidade de calcular os 10 
            entregadores mais rapidos por cidade

            top_geral = será o primeiro ascending, para selecionar os 10 primeiros entregadores
            top_velocidade = será o rank realizado pelo dense

            Resumo: Para os mais rápidos = (True, True)
                    Para os mais lentos = (False, False)
    """
    df2 = df1.loc[:, ['Delivery_person_ID', 'Time_taken(min)', 'City']] \
        .groupby(['City', 'Delivery_person_ID']) \
        .mean() \
        .sort_values(['City', 'Time_taken(min)'], ascending=top_geral) \
        .reset_index()
    
    # Seleciona os 10 primeiros entregadores por cidade
    df_aux01 = df2.loc[df2['City'] == 'Metropolitian', :].head(10)
    df_aux02 = df2.loc[df2['City'] == 'Urban', :].head(10)
    df_aux03 = df2.loc[df2['City'] == 'Semi-Urban'].head(10)
    
    df_aux_final = pd.concat([df_aux01, df_aux02, df_aux03]).reset_index(drop=True)
    
    # Aplica dense rank dentro de cada cidade
    df_aux_final['Rank_fast'] = df_aux_final.groupby('City')['Time_taken(min)'] \
        .rank(method='dense', ascending=top_velocidade).astype(int)
    return df_aux_final

                
# ====================================================================
# ==========================LIMPAR DADOS=============================
# ====================================================================

df = clean_code(df)
df1 = df.copy()


# ====================================================================
# ==========================BARRA LATERAL=============================
# ====================================================================

st.set_page_config(
    layout="wide"  # Isso vai ajustar a largura da área central
)

st.header('Marketplace - Visão Entregadores')

#image_path = 'C:/Users/carlo/OneDrive/Documentos/repos/fast_track_course_python/logo.png'
image = Image.open('logo.png')
st.sidebar.image(image, width=100)

st.sidebar.markdown('# Curry Company')
st.sidebar.markdown('## Fastest Delivery in Town') 
st.sidebar.markdown("""---""")

# Criação do slider
date_slider = st.sidebar.slider(
    'Selecione uma data limite',
    value=datetime(2022, 4, 6),  
    min_value=datetime(2022, 2, 11),  
    max_value=datetime(2022, 4, 6),   
    format='DD-MM-YYYY')

st.sidebar.markdown("""---""")

# Criação da multi selecao
traffic_options = st.sidebar.multiselect(
    'Selecione as condições de trânsito',
    ['High','Jam','Medium','Low'],
    default=['High','Jam','Medium','Low'])

# Verificando se o usuário removeu todas as opções
if not traffic_options:
    st.sidebar.error("Você precisa selecionar pelo menos uma condição de trânsito.")
    # Definindo um valor padrão caso o usuário não selecione nada
    traffic_options = ['High', 'Jam', 'Medium', 'Low']

# Criação da multi selecao
city_options = st.sidebar.multiselect(
    'Selecione as cidades desejadas',
    ['Metropolitian','Urban','Semi-Urban'],
    default=['Metropolitian','Urban','Semi-Urban'])

# Verificando se o usuário removeu todas as opções
if not city_options:
    st.sidebar.error("Você precisa selecionar pelo menos uma cidade.")
    # Definindo um valor padrão caso o usuário não selecione nada
    city_options = ['Metropolitian','Urban','Semi-Urban']
    
st.sidebar.markdown("""---""")
st.sidebar.markdown('### Powered by Comunidade DS')

# FILTRO DE DATA
linhas_selecionadas = df1['Order_Date'] < date_slider
df1 = df1.loc[linhas_selecionadas, :]
# FILTRO DE TRANSTITO
linhas_selecionadas = df1['Road_traffic_density'].isin(traffic_options)
df1 = df1.loc[linhas_selecionadas, :]
# FILTRO DE CIDADE
linhas_selecionadas = df1['City'].isin(city_options)
df1 = df1.loc[linhas_selecionadas, :]


# ====================================================================
# =========================LAYOUT NO STREAMLIT=======================#
# ====================================================================

tab1, tab2, tab3 = st.tabs( ['Visão Gerencial','_','_'] )

with tab1:
    with st.container():
        st.markdown("## 🕰️ Idades dos entregadores e condições dos veículos")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
              st.metric(
                label="🧒 Menor idade entregador", 
                value=str(df1['Delivery_person_Age'].min())
            )
        with col2:
              st.metric(
                label="👴 Maior idade entregador", 
                value=str(df1['Delivery_person_Age'].max())
            )
        with col3:
            st.metric(
                label='🚗 Pior condição veículo',
                value=str(df1['Vehicle_condition'].min())
            )
        with col4:
            st.metric(
                label='🚙 Melhor condição veículo',
                value=str(df1['Vehicle_condition'].max())
            )
    with st.container():
        st.markdown("""---""")
        st.markdown("## 📝 Análise das avaliações")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("*⭐ Avaliação média por entregador*")
            # A avaliação médida por entregador.
            df_aux = df1.loc[:,['Delivery_person_ID','Delivery_person_Ratings']].groupby('Delivery_person_ID').mean().reset_index()
            st.dataframe(df_aux)
        with col2:
            st.markdown("*🚦 Avaliação média e desvio padrão por tipo de tráfego*")
            # A avaliação média e o desvio padrão por tipo de tráfego.
            df_aux = df1.loc[:,['Road_traffic_density','Delivery_person_Ratings']].groupby('Road_traffic_density').agg({'Delivery_person_Ratings': ['mean', 'std']})
            # Mudar nome coluna
            df_aux.columns = ['rating_traffic_mean', 'rating_traffic_std']
            # resetar index
            df_aux.reset_index()
            st.dataframe(df_aux)

            st.markdown("*🌤 Avaliação média e desvio padrão por condições climáticas*")
            #A avaliação média e o desvio padrão por condições climáticas
            df_aux = df1.loc[:,['Weatherconditions','Delivery_person_Ratings']].groupby('Weatherconditions').agg({'Delivery_person_Ratings': ['mean', 'std']})
            # Mudar nome coluna
            df_aux.columns = ['rating_weather_mean', 'rating_weather_std']
            # resetar index
            df_aux.reset_index()
            st.dataframe(df_aux)

                    
    with st.container():
        st.markdown("""---""")
        st.markdown("## 🚴‍♂️ Top 10 Entregadores por velocidade e por cidade")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("*⚡ Top 10 entregadores mais rápidos por cidade*")
            # Os 10 entregadores mais rápidos por cidade
            df_top10_rapidos = top_delivery(df1, top_geral=True, top_velocidade=True)
            st.dataframe(df_top10_rapidos)

        with col2:
            st.markdown("*🐢 Top 10 entregadores mais lentos por cidade*")
            # Os 10 entregadores mais lentos por cidade
            df_top10_lentos = top_delivery(df1, top_geral=False, top_velocidade=False)
            st.dataframe(df_top10_lentos)































