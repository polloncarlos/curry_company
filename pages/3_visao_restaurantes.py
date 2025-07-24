# ====================================================================
# ==========================BIBLIOTECAS=============================
# ====================================================================

import plotly.express as px
from haversine import haversine

# ====================================================================
# ==========================BIBLIOTECAS NECESSARIAS=============================
# ====================================================================

import pandas as pd
import streamlit as st
from PIL import Image
from datetime import datetime
import plotly.graph_objects as go
import numpy as np

st.set_page_config( page_title='Visão Restaurantes', page_icon='🍽️', layout='wide')

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

    

def status_dia(df, festival):
    """ Esta função tem a responsabilidade de calcular
            o desvio padrao e a média das entregas
                realizadas durante o festival

                Orientacoes:
                     Na condicional festival é necessário retornar duas condicoes possiveis, 'Yes' ou 'No'.
                        dessa forma selecionará entre dias comuns e dias festivos
    """
    df_festival = (
        df.loc[:, ['Time_taken(min)', 'Festival']]
        .groupby('Festival')
        .agg({'Time_taken(min)': ['mean', 'std']})
    )
    df_festival.columns = ['festival_mean', 'festival_std']
    df_festival = df_festival.reset_index()

    row = df_festival[df_festival['Festival'] == festival]
    media = row['festival_mean'].values[0]
    std = row['festival_std'].values[0]

    return round(media, 2), round(std, 2)



def mean_std_city(df1):
    """ Esta função tem a responsabilidade de calcular
            o tempo médio e variabilidade de entrega 
                por cidade e tipo de pedido
    """
    df_aux = df1.loc[:,['City', 'Time_taken(min)']].groupby('City').agg({'Time_taken(min)': ('mean','std')})
    # Mudar nome coluna
    df_aux.columns = ['time_city_mean', 'time_city_std']
    # resetar index
    df_aux = df_aux.reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar( name='Control', x=df_aux['City'], y=df_aux['time_city_mean'], error_y=dict(type='data', array=df_aux['time_city_std']),
    text=[f"{v:.2f}" for v in df_aux['time_city_mean']],
    textposition='inside',
    insidetextanchor='start'))
    # Agora o texto para o std acima da barra de erro
    fig.add_trace(go.Scatter(
        x=df_aux['City'],
        y=df_aux['time_city_mean'] + df_aux['time_city_std'] + 0.5,  # ajusta para ficar acima da barra de erro
        text=[f"±{v:.2f}" for v in df_aux['time_city_std']],
        mode='text',
        showlegend=False,
    ))
    
    fig.update_layout(barmode='group')
    fig.update_layout(showlegend=False)
    return fig


def percent_distance(df1):
    """ Esta função tem a responsabilidade de calcular
            a distribuição percentual da distância média de entregas 
                por cidade em relação ao total.
    """
# Calcular distância usando Haversine
    df1['distance'] = df1.apply(
        lambda x: haversine(
            (x['Restaurant_latitude'], x['Restaurant_longitude']),
            (x['Delivery_location_latitude'], x['Delivery_location_longitude'])
        ),
        axis=1
    )
    
    # Distância média por cidade
    avg_distance = df1[['City', 'distance']].groupby('City').mean().reset_index()
    
    # Gráfico de pizza
    fig = go.Figure(data=[
        go.Pie(labels=avg_distance['City'], values=avg_distance['distance'], pull=[0, 0.1, 0])
    ])
    fig.update_layout(width=600, height=600)
    return fig



def mean_std_road_traffic_density(df1):
    """ Esta função tem a responsabilidade de calcular
            a distribuição percentual da distância média de entregas 
                por cidade em relação ao total.
    """
    df_aux = df1.loc[:, ['City','Time_taken(min)','Road_traffic_density']] \
                 .groupby(['City','Road_traffic_density']) \
                 .agg({'Time_taken(min)': ['mean','std']})
    
    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()
    
    fig = px.sunburst(
        df_aux,
        path=['City','Road_traffic_density'],
        values='avg_time',
        color='std_time',
        color_continuous_scale='RdBu_r',
        color_continuous_midpoint=np.average(df_aux['std_time'])
    )
    fig.update_layout(width=600, height=600)
    return fig

                
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

st.header('Marketplace - Visão Restaurantes')

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
        st.markdown("## 📊 Métricas de entrega")
        st.markdown("*Principais indicadores do desempenho das entregas.*")
        col1, col2, col3 = st.columns(3)
        with col1:
            # Quantidade de entregas únicas
            st.metric(
                label="📦 Entregadores distintos", 
                value=str(df1['Delivery_person_ID'].nunique()))
            # Distancia média das entregas
            st.metric(
                label="🛣️ Distância média das entregas", 
                value=f"{round(df1['distance_delivery'].mean(), 2)} km")
        with col2:
            # Mean e std durante os Festivais.
            media, std = status_dia(df1, 'Yes')
            st.metric(label="🎉 Tempo médio (Festival)", value=f"{media}")
            st.metric(label="🎉 Desvio padrão (Festival)", value=f"{std}")
            
        with col3:
            # Mean e std em dias comuns.
            media, std = status_dia(df1, 'No')
            st.metric(label="📅 Tempo médio (Dia comum)", value=str(media))
            st.metric(label="📅 Desvio padrão (Dia comum)", value=str(std))

    
    with st.container():
        st.markdown("""---""")
        st.markdown("## ⏱️ Tempo médio e variabilidade de entrega por cidade e tipo de pedido")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("*Tempo médio de entrega e seu desvio padrão por cidade.*")
            fig = mean_std_city(df1)          
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("*Tempo médio de entrega e seu desvio padrão por cidade e tipo de pedido.*")
            df_aux = df1.loc[:,['ID','City','Type_of_order','Time_taken(min)']].groupby(['City','Type_of_order']).agg({'Time_taken(min)':['mean','std']})
            # Mudar nome coluna
            df_aux.columns = ['time_city_order_mean', 'time_city_order_std']
            # resetar index
            df_aux = df_aux.reset_index()
            st.dataframe(df_aux, use_container_width=True)

    
    with st.container():
        st.markdown("""---""")
        col1, col2 = st.columns(2)
        with col1: 
            st.markdown("## 🏙️ Distância média por cidade")
            st.markdown("*Distribuição percentual da distância média de entregas por cidade em relação ao total.*")
            fig = percent_distance(df1)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("## ⏱️ Tempo médio de entrega por cidade e tráfego")
            st.markdown("*Azul = baixo desvio padrão; vermelho = alto desvio padrão.*")
            fig = mean_std_road_traffic_density(df1)
            st.plotly_chart(fig, use_container_width=True)

























