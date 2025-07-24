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
import folium as fo

st.set_page_config( page_title='Visão Empresa', page_icon='📈', layout='wide')

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



def mapa_empresa(df1):
    """     
                Essa funcao é responsável por fazer os filtros para o mapa      
    """
    df_aux = df1[['City', 'Road_traffic_density', 'Delivery_location_latitude', 'Delivery_location_longitude']] \
    .groupby(['City', 'Road_traffic_density']) \
    .median().reset_index()
    
    mapa = fo.Map(location=[df_aux['Delivery_location_latitude'].mean(),
                            df_aux['Delivery_location_longitude'].mean()],
                  zoom_start=5)    
    for _, row in df_aux.iterrows():
        fo.Marker(
            location=[row['Delivery_location_latitude'], row['Delivery_location_longitude']],
            popup=f"{row['City']} - {row['Road_traffic_density']}"
        ).add_to(mapa)
    
    bounds = [[df_aux['Delivery_location_latitude'].min(), df_aux['Delivery_location_longitude'].min()],
              [df_aux['Delivery_location_latitude'].max(), df_aux['Delivery_location_longitude'].max()]]
    
    mapa.fit_bounds(bounds)
    return mapa._repr_html_()  # Cria o HTML do mapa

    

def pedidos_semana(df1):
    """     
                Essa funcao é responsável por filtrar os pedidos feitos na semana e plotar um gráfico de linhas    
    """
    df_aux1 = df1.loc[:, ['ID','week_of_year']].groupby('week_of_year').count().reset_index()
    df_aux2 = df1.loc[:, ['Delivery_person_ID', 'week_of_year']].groupby('week_of_year').nunique().reset_index()
    
    df_aux = pd.merge(df_aux1, df_aux2, how='inner')
    df_aux['Order_by_delivery'] = df_aux['ID'] / df_aux['Delivery_person_ID']
    fig = px.line(df_aux, x='week_of_year', y='Order_by_delivery')
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

st.header('Marketplace - Visão Empresa')

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


tab1, tab2, tab3 = st.tabs( ['Visão Gerencial','Visão Tática','Visão Geográfica'] )

with tab1:
    st.markdown("## 📅 Pedidos diários")
    st.markdown("*Número total de pedidos por data.*")
    df_aux = df1.loc[:, ['ID', 'Order_Date']].groupby(['Order_Date']).count().reset_index()
    fig = px.bar(df_aux, x='Order_Date', y='ID')
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("""---""")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("## 🚦 Pedidos por densidade de tráfego")
        st.markdown("*Distribuição dos pedidos segundo a densidade do trânsito.*")
        df_aux = df1.loc[:, ['ID', 'Road_traffic_density']].groupby('Road_traffic_density').count().reset_index()
        fig = px.pie(df_aux, values='ID', names = 'Road_traffic_density')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("## 🌆 Pedidos por cidade e tráfego")
        st.markdown("*Pedidos agrupados por cidade e densidade de trânsito.*")
        df_aux = df1.loc[:,['ID','City','Road_traffic_density']].groupby(['City','Road_traffic_density']).count().reset_index()
        fig = px.scatter(df_aux, x='City', y='Road_traffic_density', size='ID', color='City')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    with st.container():
        st.markdown("## 📈 Pedidos por semana")
        st.markdown("*Evolução do número total de pedidos ao longo das semanas.*")
        # Quantidade de pedidos por semana.
        df_aux = df1.loc[:,['ID','week_of_year']].groupby('week_of_year').count().reset_index()
        fig = px.line(df_aux, x='week_of_year', y='ID')
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("""---""")
    with st.container():
        st.markdown("## 🛵 Pedidos por entregador por semana")
        st.markdown("*Número médio de pedidos realizados por entregador a cada semana.*")
        fig = pedidos_semana(df1)
        st.plotly_chart(fig, use_container_width=True)

    
with tab3:
    st.markdown("## 🗺️ Mapa das entregas por cidade e tráfego")
    st.markdown("*Localização média das entregas agrupadas por cidade e densidade do trânsito.*")
    map_html = mapa_empresa(df1)
    st.components.v1.html(map_html, height=600)














































