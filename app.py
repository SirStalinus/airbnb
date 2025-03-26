import pandas as pd
import streamlit as st
import plotly.express as px
import geopandas as gpd
import folium
import requests
from streamlit_folium import folium_static

# =============================================================================
# Configuration de la page
# =============================================================================
st.set_page_config(
    page_title="AirBnB à Paris - Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS personnalisé
# =============================================================================
st.markdown(
    """
    <style>
    /* Fond et typographie */
    body {
        background-color: #f5f5f5;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Encadre le titre principal */
    .main > .block-container {
        padding-top: 2rem;
    }
    /* Style pour les conteneurs de texte */
    .stMarkdown, .css-1d391kg {
        font-size: 1.1rem;
        line-height: 1.6;
    }
    /* Customisation du sidebar */
    .css-1d391kg {
        font-weight: 500;
    }
    .stSidebar {
        background-color: #ffffff;
    }
    /* Style des boutons */
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5em 1em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =============================================================================
# Création des onglets principaux (Page d'accueil + 3 Dashboard)
# =============================================================================
tabs = st.tabs(["Accueil", "Dashboard 1", "Dashboard 2", "Dashboard 3"])

# =============================================================================
# Onglet Accueil
# =============================================================================
with tabs[0]:
    st.title("Bienvenue sur le Dashboard AirBnB à Paris")
    st.markdown(
        """
        ## Accueil
        Cette application interactive vous permet d'explorer les données des logements AirBnB à Paris.
        
        **Onglets disponibles :**
        - **Dashboard 1 :** Analyse générale, carte choroplèthe et small multiples (avec données géographiques).
        - **Dashboard 2 :** Analyse des types de logements avec histogramme, box plot et carte Folium.
        - **Dashboard 3 :** Analyse cartographique détaillée avec carte choroplèthe interactive et graphique de classement.
        
        Sélectionnez un onglet ci-dessus pour débuter l'exploration !
        """
    )

# =============================================================================
# Dashboard 1 : Code 1 - Analyse générale, carte choroplèthe et small multiples
# =============================================================================
with tabs[1]:
    st.header("Dashboard 1 : Analyse générale et Small Multiples")
    
    @st.cache_data
    def load_data_dashboard1():
        listings = pd.read_csv('https://data.insideairbnb.com/france/ile-de-france/paris/2024-09-06/visualisations/listings.csv')
        geo_data = gpd.read_file('https://data.insideairbnb.com/france/ile-de-france/paris/2024-09-06/visualisations/neighbourhoods.geojson')
        return listings, geo_data

    listings1, geo_data1 = load_data_dashboard1()
    
    # Création d'onglets internes pour Dashboard 1
    d1_tabs = st.tabs(["Small multiples"])

    
    with d1_tabs[0]:
        st.subheader("Small multiples : Parts de type de logement par arrondissement")
        # Préparation des données
        room_type_counts = listings1.groupby(['room_type', 'neighbourhood']).size().reset_index(name='count')
        # Identification des colonnes non utilisées dans listings1
        unused_columns = [col for col in listings1.columns if col not in ['room_type', 'neighbourhood']]
        # Sélection de la variable (utilisation ici de st.selectbox dans l'onglet principal)
        column_variable = st.selectbox(
            "Choisissez une variable pour les colonnes du graphique",
            options=[col for col in unused_columns if col in room_type_counts.columns],
            index=0
        )
        # Détermination de la variable pour les small multiples
        facet_row_variable = "neighbourhood" if column_variable == "room_type" else "room_type"
        unique_facet_rows = room_type_counts[facet_row_variable].unique()
        
        for row_value in unique_facet_rows:
            filtered_data = room_type_counts[room_type_counts[facet_row_variable] == row_value]
            fig_small = px.bar(
                filtered_data,
                x=column_variable,
                y="count",
                color=column_variable,
                title=f"Nombre de {row_value} par quartier parisien",
                hover_data=['neighbourhood'],
                height=400
            )
            fig_small.update_layout(
                dragmode=False,
                title=dict(text=f"Nombre de {row_value} par quartier parisien", x=0.5),
                margin=dict(l=20, r=20, t=50, b=50)
            )
            fig_small.update_traces(
                hovertemplate='Count: %{y}<br>Neighbourhood: %{customdata[0]}<extra></extra>'
            )
            st.plotly_chart(fig_small, use_container_width=True)

# =============================================================================
# Dashboard 2 : Code 2 - Histogramme, box plot et carte Folium
# =============================================================================
with tabs[2]:
    st.header("Dashboard 2 : Analyse des types de logements et carte Folium")
    # Chargement des données depuis la même source (URL)
    data2 = pd.read_csv("https://data.insideairbnb.com/france/ile-de-france/paris/2024-09-06/visualisations/listings.csv")
    
    st.subheader("Répartition des types de logements")
    fig_hist = px.histogram(data2, x="room_type", title="Répartition des types de logements")
    fig_hist.update_xaxes(
        ticktext=["Maison/Appartement", "Chambre privée", "Chambre partagée", "Chambre d'hotel"],
        tickvals=["Entire home/apt", "Private room", "Shared room", "Hotel room"]
    )
    st.plotly_chart(fig_hist)
    
    room_types = data2["room_type"].unique()
    selected_room_type = st.selectbox("Sélectionnez le type de logement", room_types)
    filtered_data2 = data2[data2["room_type"] == selected_room_type]
    price_90th_percentile = filtered_data2["price"].quantile(0.9)
    filtered_data2 = filtered_data2[filtered_data2["price"] <= price_90th_percentile]
    
    st.subheader(f"Distribution des prix pour {selected_room_type}")
    fig_box = px.box(filtered_data2, y="price", title=f"Distribution des prix pour {selected_room_type}",
                     labels={"price": "Prix (€)"})
    st.plotly_chart(fig_box)
    
    nb_points = st.slider("Nombre de logements affichés sur la carte", 10, len(data2), 50)
    st.subheader("Carte des logements Airbnb à Paris")
    carte2 = folium.Map(location=[48.8566, 2.3522], zoom_start=12)
    data_map2 = data2.head(nb_points)
    for _, row in data_map2.iterrows():
        popup_content = f"""
        <strong>{row['name']}</strong><br>
        Type: {row['room_type']}<br>
        Prix: {row['price']} €<br>
        """
        folium.CircleMarker(
            [row["latitude"], row["longitude"]],
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=0.6,
            popup=folium.Popup(popup_content, max_width=300)
        ).add_to(carte2)
    folium_static(carte2)

# =============================================================================
# Dashboard 3 : Code 3 - Analyse cartographique détaillée
# =============================================================================
with tabs[3]:
    st.header("Dashboard 3 : Analyse cartographique détaillée")
    
    @st.cache_data
    def charger_donnees_dashboard3():
        url_listings = "https://data.insideairbnb.com/france/ile-de-france/paris/2024-09-06/visualisations/listings.csv"
        url_geojson = "https://data.insideairbnb.com/france/ile-de-france/paris/2024-09-06/visualisations/neighbourhoods.geojson"
        df3 = pd.read_csv(url_listings)
        response = requests.get(url_geojson)
        geojson3 = response.json()
        return df3, geojson3

    df3, geojson3 = charger_donnees_dashboard3()
    
    # Agrégation des données par quartier
    agg = df3.groupby("neighbourhood").agg(
        count=("id", "count"),
        avg_price=("price", "mean"),
        entire_count=("room_type", lambda x: (x == "Entire home/apt").sum())
    ).reset_index()
    agg["part_entier"] = agg["entire_count"] / agg["count"] * 100
    max_logements = int(agg["count"].max())
    
    # Barre latérale pour filtres spécifiques à Dashboard 3
    st.sidebar.header("Filtres et options Dashboard 3")
    statistique = st.sidebar.selectbox(
        "Sélectionnez la statistique à afficher",
        ("Nombre de logements", "Prix moyen", "Part de logement entier")
    )
    min_logements = st.sidebar.slider(
        "Nombre minimum de logements par quartier",
        min_value=0, max_value=max_logements, value=0, step=5,
        help="Filtrer les quartiers ayant moins de logements que ce seuil."
    )
    styles_carte = {
        "Carto Positron": "carto-positron",
        "Open Street Map": "open-street-map",
    }
    style_nom = st.sidebar.selectbox("Choisissez le style de la carte", list(styles_carte.keys()))
    style_carte = styles_carte[style_nom]
    
    if statistique == "Nombre de logements":
        col_couleur = "count"
        libelle = "Nombre de logements"
    elif statistique == "Prix moyen":
        col_couleur = "avg_price"
        libelle = "Prix moyen (€)"
    elif statistique == "Part de logement entier":
        col_couleur = "part_entier"
        libelle = "Pourcentage de logements entiers (%)"
    
    agg_filtré = agg[agg["count"] >= min_logements]
    
    st.subheader("Carte Interactive")
    fig_carte = px.choropleth_map(
        agg_filtré,
        geojson=geojson3,
        locations="neighbourhood",
        featureidkey="properties.neighbourhood",
        color=col_couleur,
        color_continuous_scale="Viridis",
        map_style=style_carte,
        center={"lat": 48.8566, "lon": 2.3522},
        zoom=10,
        opacity=0.7,
        labels={col_couleur: libelle},
        hover_data={
            "count": True,
            "avg_price": ':.2f',
            "part_entier": ':.2f'
        }
    )
    fig_carte.update_layout(
        margin={"r":0, "t":0, "l":0, "b":0},
        title_font=dict(size=20, family='Segoe UI'),
        font=dict(family='Segoe UI'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_carte, use_container_width=True)
    
    st.subheader("Graphique de Classement")
    agg_trié = agg_filtré.sort_values(by=col_couleur, ascending=False)
    fig_barres = px.bar(
        agg_trié,
        x="neighbourhood",
        y=col_couleur,
        labels={"neighbourhood": "Quartier", col_couleur: libelle},
        title=f"Classement des quartiers par {libelle}"
    )
    fig_barres.update_layout(
        xaxis_tickangle=-45,
        title_font=dict(size=18, family='Segoe UI'),
        font=dict(family='Segoe UI'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_barres, use_container_width=True)
    
    st.markdown("### Résumé des Statistiques")
    col1, col2 = st.columns(2)
    with col1:
        nb_quartiers = len(agg_filtré)
        st.metric("Quartiers affichés", nb_quartiers)
    with col2:
        total_logements = agg_filtré["count"].sum()
        st.metric("Total des logements", total_logements)
    
    with st.expander("Afficher les données agrégées"):
        st.dataframe(agg_filtré)
