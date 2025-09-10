import datetime
import os

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components
from folium.plugins import HeatMap, MarkerCluster

try:
    directory = f"{os.environ['DASHBOARDS']}/biomarato_25"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


base_url = "https://minka-sdg.org"
api_path = f"https://api.minka-sdg.org/v1"


projects = [
    {"id": 418, "name": "Girona"},
    {"id": 419, "name": "Tarragona"},
    {"id": 420, "name": "Barcelona"},
    {"id": 417, "name": "Catalunya"},
]


def load_maps():
    # Layout for title and selector
    with st.container():
        col1, col2 = st.columns([1, 25])
        with col1:
            st.image(f"{directory}/images/Biomarato_logo_100.png")
        with col2:
            st.header(":orange[Mapes]")

    # Project selection
    project_name = st.selectbox(
        label="Projecte per mostrar al mapa",
        options=("Tarragona", "Barcelona", "Girona", "Catalunya"),
        key="project_selector",  # Add a key for the selectbox
    )

    # Map id mapping
    project_ids = {"Barcelona": 420, "Tarragona": 419, "Girona": 418, "Catalunya": 417}
    proj_id = project_ids[project_name]

    # Create a unique key for each project
    map_key = f"maps_{proj_id}"

    # Only load maps if they don't exist in session_state or if project changed
    if map_key not in st.session_state:
        try:
            df_map = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")
            # Store both maps in a dictionary with this project's key
            st.session_state[map_key] = {
                "heatmap": create_heatmap(df_map),
                "markermap": create_markercluster(df_map),
            }
        except FileNotFoundError:
            st.error(f"No s'han trobat dades per {project_name}")
            return

    # Display the maps (from cache if available)
    if map_key in st.session_state:
        map1, map2 = st.columns(2)

        with map1:
            st.subheader("Mapa de calor")
            if st.session_state[map_key]["heatmap"]:
                map_html1 = st.session_state[map_key]["heatmap"]._repr_html_()
                components.html(map_html1, height=600)

        with map2:
            st.subheader("Mapa de marcadors")
            markermap = st.session_state[map_key]["markermap"]

            # Handle different map types (folium object vs HTML string)
            if isinstance(markermap, str):
                # Pure HTML/JavaScript map
                components.html(markermap, height=600)
            else:
                # Folium map object
                map_html2 = markermap._repr_html_()
                components.html(map_html2, height=600)


@st.cache_data(ttl=300)
def get_main_metrics(proj_id, session=None):
    species = f"{api_path}/observations/species_counts?"
    url1 = f"{species}&project_id={proj_id}"
    if session is None:
        session = requests.Session()
    total_species = session.get(url1).json()["total_results"]

    observers = f"{api_path}/observations/observers?"
    url2 = f"{observers}&project_id={proj_id}"
    total_participants = session.get(url2).json()["total_results"]

    observations = f"{api_path}/observations?"
    url3 = f"{observations}&project_id={proj_id}"
    total_obs = session.get(url3).json()["total_results"]

    return total_species, total_participants, total_obs


@st.cache_data(ttl=300)
def get_last_week_metrics(proj_id, session=None):
    last_week_date = (datetime.datetime.today() - datetime.timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )
    if session is None:
        session = requests.Session()
    species = f"{api_path}/observations/species_counts?"
    url1 = f"{species}&project_id={proj_id}&d2={last_week_date}&order=desc&order_by=created_at"
    lw_spe = session.get(url1).json()["total_results"]

    observers = f"{api_path}/observations/observers?"
    url2 = f"{observers}&project_id={proj_id}&d2={last_week_date}&order=desc&order_by=created_at"
    lw_part = session.get(url2).json()["total_results"]

    observations = f"{api_path}/observations?"
    url3 = f"{observations}&project_id={proj_id}&d2={last_week_date}&order=desc&order_by=created_at"
    lw_obs = session.get(url3).json()["total_results"]
    return lw_obs, lw_spe, lw_part


@st.cache_data(ttl=300)
def get_metrics_province():
    prov = {
        projects[0]["name"]: projects[0]["id"],
        projects[1]["name"]: projects[1]["id"],
        projects[2]["name"]: projects[2]["id"],
    }

    result = []

    with requests.Session() as session:
        for k, v in prov.items():

            species = f"{api_path}/observations/species_counts?"
            url1 = f"{species}&project_id={v}"

            response1 = session.get(url1)

            if response1.status_code == 200:
                total_species = response1.json().get("total_results")

            else:
                total_species = None

            observers = f"{api_path}/observations/observers?"
            url2 = f"{observers}&project_id={v}"

            response2 = session.get(url2)

            if response2.status_code == 200:
                total_participants = response2.json().get("total_results")

            else:
                total_participants = None

            observations = f"{api_path}/observations?"
            url3 = f"{observations}&project_id={v}"

            response3 = session.get(url3)

            if response3.status_code == 200:
                total_obs = response3.json().get("total_results")

            else:
                total_obs = None

            # Only add to result if we got valid data
            if (
                total_species is not None
                and total_participants is not None
                and total_obs is not None
            ):
                data = {
                    "provincia": k,
                    "espècies": total_species,
                    "participants": total_participants,
                    "observacions": total_obs,
                }
                result.append(data)
            else:
                print(f"Skipping {k} due to API errors")

    main_metrics = pd.DataFrame(result)
    return main_metrics


@st.cache_resource(ttl=3600)
def fig_area_evolution(df, field, title, color):
    """
    Generate an area plot to visualize the evolution of a specific field in a dataframe.

    Parameters:
    - df: The input dataframe.
    - field: The field to be plotted.
    - title: The title of the plot.
    - color: The color of the markers and lines in the plot.
    """
    if df.empty:
        raise ValueError("Input dataframe is empty.")
    fig = px.area(
        df,
        x="data",
        y=field,
        markers=False,
    )
    fig.update_traces(
        marker_color=color,
        line_color=color,
    )
    fig.update_layout(
        plot_bgcolor="white",
        xaxis_title="",
        yaxis_tickformat=",d",
        separators=". ",
        title=dict(text=title, font_size=18),
    )
    return fig


@st.cache_resource(ttl=3600)
def fig_bars_months(grouped: pd.DataFrame, field: str, title: str, color: str):
    """
    Generate a bar chart using Plotly Express.

    Parameters:
    - grouped (pandas.DataFrame): The grouped data for the chart.
    - field (str): The field to be plotted on the y-axis.
    - title (str): The title of the chart.
    - color (str): The color of the bars.

    Returns:
    - fig (plotly.graph_objects.Figure): The generated bar chart figure.
    """
    if field not in grouped.columns:
        raise ValueError(f"Invalid field: {field}")
    fig = px.bar(
        grouped,
        x="data",
        y=field,
        text_auto=True,
    )
    fig.update_traces(
        marker_color=color,
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=14,
        textposition="inside",
    )
    fig.update_layout(
        width=600,
        height=400,
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white"),
        title=dict(text=f"{title}", font_size=18),
        showlegend=False,
        yaxis_tickformat=",d",
        xaxis=dict(
            tickmode="array",
            tickvals=grouped["data"].to_list(),
            ticktext=grouped["data"].to_list(),
            tickfont=dict(size=14),
            tickangle=-45,
        ),
    )
    return fig


@st.cache_resource(ttl=300)
def fig_provinces(main_metrics: pd.DataFrame, field: str, title: str) -> px.bar:
    """
    Generate a bar chart of the main metrics for each province.

    Parameters:
    - main_metrics (DataFrame): The main metrics data.
    - field (str): The field to use for sorting the data.
    - title (str): The title of the chart.

    Returns:
    - fig (plotly.graph_objects.Figure): The generated bar chart.

    """

    fig = px.bar(
        main_metrics.sort_values(by=field, ascending=False),
        x=field,
        y="provincia",
        text_auto=",d",
        color="provincia",
        color_discrete_map={
            "Girona": "#f9b853",
            "Tarragona": "#dc6619",
            "Barcelona": "#089aa2",
        },
    )
    fig.update_traces(
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=14,
        textposition="inside",
    )
    fig.update_layout(
        width=600,
        height=400,
        plot_bgcolor="#FEF7EB",
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white"),
        title=dict(text=f"{title}", font_size=22),
        showlegend=False,
    )
    fig.update_yaxes(tickfont_size=16)

    return fig


@st.cache_data(ttl=3600)
def get_last_obs(proj_id):
    last_obs = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")
    last_photos = pd.read_csv(f"{directory}/data/{proj_id}_df_photos.csv")
    total = pd.merge(
        last_photos,
        last_obs[
            [
                "id",
                "observed_on",
                "quality_grade",
                "kingdom",
                "phylum",
                "class",
                "order",
                "family",
                "genus",
            ]
        ],
        on="id",
        how="left",
    )

    excluded_logins = ["xasalva", "mediambient_ajelprat"]
    last_total = total[
        (~total.user_login.isin(excluded_logins)) & (total.quality_grade == "research")
    ].reset_index(drop=True)
    last_total.drop_duplicates(subset="id", inplace=True)
    last_total = last_total.sort_values(by="id", ascending=False).reset_index(drop=True)

    return last_total


@st.cache_resource(ttl=3600)
def create_heatmap(df):
    """Create heatmap with same HTML structure as markercluster for consistent height"""
    df_clean = df.dropna(subset=["latitude", "longitude"]).copy()

    if df_clean.empty:
        return None

    # Get coordinates and center
    coordinates = df_clean[["latitude", "longitude"]].values
    center = coordinates.mean(axis=0).tolist()

    # Convert coordinates to JavaScript format
    import json

    locations = [[float(lat), float(lng)] for lat, lng in coordinates]

    # Create HTML with same structure as markercluster
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
        <title>Mapa de Calor - {len(locations):,} punts</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; }}
            #map {{ 
                height: 600px !important; 
                width: 100% !important; 
                position: relative;
                aspect-ratio: 16/9;
                min-width: 800px;
                max-height: 600px;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
        
        <script>
            var map = L.map('map', {{
                crs: L.CRS.EPSG3857,
                zoomControl: true
            }}).setView([{center[0]}, {center[1]}], 6);
            
            // Force map resize after initialization
            setTimeout(function() {{
                map.invalidateSize();
            }}, 100);
            
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                maxZoom: 18
            }}).addTo(map);
            
            // Create heatmap with same configuration as folium version
            var heat = L.heatLayer({json.dumps(locations)}, {{
                radius: 10,
                blur: 15,
                maxZoom: 18,
                max: 1.0,
                minOpacity: 0.7,
                gradient: {{
                    0.1: 'blue',
                    0.2: 'cyan', 
                    0.4: 'lime',
                    0.6: 'orange',
                    0.8: 'red',
                    0.99: 'purple'
                }}
            }}).addTo(map);
            
            // Force final map resize for heatmap
            setTimeout(function() {{
                map.invalidateSize();
            }}, 200);
            
            console.log('Heatmap loaded with ' + {len(locations)} + ' points');
        </script>
    </body>
    </html>
    """

    return html_content


@st.cache_resource(ttl=3600)
def create_markercluster(df):
    """Ultra-fast marker clustering with multiple strategies"""
    df_clean = df.dropna(subset=["latitude", "longitude"]).copy()

    if df_clean.empty:
        return None

    coordinates = df_clean[["latitude", "longitude"]].values
    center = coordinates.mean(axis=0).tolist()

    # Use JavaScript implementation for all datasets for consistency
    return _create_javascript_map(df_clean, center)


def _create_javascript_map(df, center):
    """Pure JavaScript/Leaflet implementation for massive datasets"""
    required_cols = ["taxon_name", "user_login", "id", "latitude", "longitude"]
    if not all(col in df.columns for col in required_cols):
        st.error("Missing required columns for map")
        return None

    # Convert to compact JSON format
    import json

    markers_data = []
    for row in df.itertuples():
        markers_data.append(
            {
                "lat": float(row.latitude),
                "lng": float(row.longitude),
                "taxon": str(row.taxon_name)[:50],  # Truncate for performance
                "user": str(row.user_login)[:30],
                "id": int(row.id),
            }
        )

    # Create optimized HTML with chunked loading
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
        <title>Mapa Biomarató - {len(markers_data):,} punts</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; }}
            #map {{ 
                height: 600px !important; 
                width: 100% !important; 
                position: relative;
                aspect-ratio: 16/9;
                min-width: 800px;
                max-height: 600px;
            }}
            .loading {{ 
                position: absolute; top: 10px; right: 10px; z-index: 1000; 
                background: white; padding: 5px 10px; border-radius: 5px; 
                font-family: Arial; font-size: 12px; 
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="loading" class="loading">Carregant {len(markers_data):,} punts...</div>
        
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>
        
        <script>
            var map = L.map('map', {{
                crs: L.CRS.EPSG3857,
                zoomControl: true
            }}).setView([{center[0]}, {center[1]}], 6);
            
            // Force map resize after initialization
            setTimeout(function() {{
                map.invalidateSize();
            }}, 100);
            
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                attribution: 'Tiles &copy; Esri',
                maxZoom: 18
            }}).addTo(map);
            
            // Ultra-optimized cluster settings
            var markers = L.markerClusterGroup({{
                maxClusterRadius: 60,
                disableClusteringAtZoom: 15,
                spiderfyOnMaxZoom: false,
                showCoverageOnHover: false,
                zoomToBoundsOnClick: true,
                chunkedLoading: true,
                chunkInterval: 100,
                chunkDelay: 10,
                animate: false
            }});
            
            // Load markers in ultra-small chunks for responsiveness
            var markerData = {json.dumps(markers_data)};
            var batchSize = 500;
            var index = 0;
            var loadingDiv = document.getElementById('loading');
            
            function addBatch() {{
                var batch = markerData.slice(index, index + batchSize);
                var tempMarkers = [];
                
                batch.forEach(function(point) {{
                    // Create custom green icon with binoculars using DivIcon
                    var binocularsIcon = L.divIcon({{
                        html: '<div style="background-color: #4CAF50; width: 24px; height: 24px; border-radius: 3px; border: 2px solid #fff; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(0,0,0,0.4);"><i class="fas fa-binoculars" style="color: white; font-size: 12px;"></i></div>',
                        iconSize: [24, 24],
                        iconAnchor: [12, 24],
                        popupAnchor: [0, -24],
                        className: 'custom-binoculars-icon'
                    }});
                    
                    var marker = L.marker([point.lat, point.lng], {{
                        icon: binocularsIcon
                    }});
                    marker.bindPopup(
                        '<b>Taxon:</b> ' + point.taxon + 
                        '<br><b>User:</b> ' + point.user + 
                        '<br><a href="https://minka-sdg.org/observations/' + point.id + '" target="_blank">🔗 Minka</a>'
                    );
                    tempMarkers.push(marker);
                }});
                
                markers.addLayers(tempMarkers);
                
                index += batchSize;
                var progress = Math.min(100, Math.round((index / markerData.length) * 100));
                loadingDiv.innerHTML = 'Carregant ' + progress + '% (' + Math.min(index, markerData.length) + '/' + markerData.length + ')';
                
                if (index < markerData.length) {{
                    setTimeout(addBatch, 1); // Very small delay
                }} else {{
                    map.addLayer(markers);
                    loadingDiv.style.display = 'none';
                    // Force map resize after all markers are loaded
                    setTimeout(function() {{
                        map.invalidateSize();
                    }}, 200);
                    console.log('Loaded ' + markerData.length + ' markers successfully');
                }}
            }}
            
            // Start loading
            setTimeout(addBatch, 100);
        </script>
    </body>
    </html>
    """

    return html_content


def _create_sampled_folium_map(df, center, max_points=5000):
    """Folium with intelligent sampling"""
    # Stratified sampling to maintain spatial distribution
    sampled_df = df.sample(n=min(max_points, len(df)), random_state=42)

    attr = "Tiles &copy; Esri"
    tiles2 = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

    m = folium.Map(
        location=center, tiles=tiles2, attr=attr, zoom_start=6, prefer_canvas=True
    )

    marker_cluster = MarkerCluster(
        options={
            "maxClusterRadius": 60,
            "disableClusteringAtZoom": 16,
            "animate": False,
            "showCoverageOnHover": False,
        }
    ).add_to(m)

    # Simple green markers (faster than FontAwesome)
    for row in sampled_df.itertuples():
        folium.Marker(
            location=[row.latitude, row.longitude],
            popup=folium.Popup(
                f"<b>Taxon:</b> {row.taxon_name}<br><b>User:</b> {row.user_login}<br><a href='https://minka-sdg.org/observations/{row.id}' target='_blank'>🔗 Minka</a>",
                min_width=150,
                max_width=200,
            ),
            icon=folium.Icon(color="green"),  # Simplified icon
        ).add_to(marker_cluster)

    st.info(
        f"Mostrant {len(sampled_df):,} de {len(df):,} observacions (mostreig optimitzat)"
    )
    return m


def _create_original_folium_map(df, center):
    """Original folium implementation for small datasets"""
    attr = "Tiles &copy; Esri"
    tiles2 = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

    m = folium.Map(location=center, tiles=tiles2, attr=attr, zoom_start=6)
    marker_cluster = MarkerCluster().add_to(m)

    for row in df.itertuples():
        folium.Marker(
            location=[row.latitude, row.longitude],
            popup=folium.Popup(
                f"<b>Taxon:</b> {row.taxon_name}<br><b>User:</b> {row.user_login}<br><a href='https://minka-sdg.org/observations/{row.id}' target='_blank'>Minka Observation</a>",
                min_width=150,
                max_width=150,
            ),
            icon=folium.Icon(color="green", icon="fa-solid fa-binoculars", prefix="fa"),
        ).add_to(marker_cluster)

    return m


def reindex(df):
    df.index = range(df.index.start + 1, df.index.stop + 1)
    return df


@st.cache_data(ttl=3600)
def get_grouped_monthly(project_id: int, year) -> pd.DataFrame:

    session = requests.Session()

    meses = {
        f"{year}-05": ["01", "31"],
        f"{year}-06": ["01", "30"],
        f"{year}-07": ["01", "31"],
        f"{year}-08": ["01", "31"],
        f"{year}-09": ["01", "30"],
        f"{year}-10": ["01", "15"],
    }

    results_by_month = []

    for mes, limits in meses.items():
        month = {}

        url_obs = f"{api_path}/observations"
        url_spe = f"{api_path}/observations/species_counts"
        url_observers = f"{api_path}/observations/observers"

        params = {
            "project_id": project_id,
            "d1": f"{mes}-{limits[0]}",
            "d2": f"{mes}-{limits[1]}",
        }

        month["data"] = mes
        month["observacions"] = session.get(url_obs, params=params).json()[
            "total_results"
        ]
        month["espècies"] = session.get(url_spe, params=params).json()["total_results"]
        month["participants"] = session.get(url_observers, params=params).json()[
            "total_results"
        ]

        results_by_month.append(month)

    return pd.DataFrame(results_by_month)


# Toma dataframe de main_metrics hasta día actual
def get_previous_years(main_metrics_filtered):
    df_2022 = pd.read_csv(f"{directory}/data/2022_main_metrics.csv")
    df_2022_filtered = df_2022.loc[: len(main_metrics_filtered) - 1, :].copy()
    df_2022_filtered.rename(
        columns={
            "date": "data",
            "observations": "observacions",
            "species": "espècies",
        },
        inplace=True,
    )

    # Datos de 2023
    df_2023 = pd.read_csv(f"{directory}/data/2023_main_metrics.csv")
    df_2023_filtered = df_2023.loc[: len(main_metrics_filtered) - 1, :].copy()
    df_2023_filtered.rename(
        columns={
            "date": "data",
            "observations": "observacions",
            "species": "espècies",
        },
        inplace=True,
    )

    # Datos de 2023
    df_2024 = pd.read_csv(f"{directory}/data/2024_main_metrics.csv")
    df_2024_filtered = df_2024.loc[: len(main_metrics_filtered) - 1, :].copy()
    df_2024_filtered.rename(
        columns={
            "date": "data",
            "observations": "observacions",
            "species": "espècies",
        },
        inplace=True,
    )

    return df_2022_filtered, df_2023_filtered, df_2024_filtered


def fig_multi_year_comparison(df_list, years, field, colors):
    """
    Compara múltiples años alineados por posición (día 1 vs día 1, etc.).

    Parámetros:
    - df_list: Lista de DataFrames [df_2022, df_2023, df_2024, df_2025].
    - years: Lista de etiquetas para los años (ej: ["2022", "2023", "2024", "2025"]).
    - field: Columna a comparar (ej: "ventas").
    - title: Título del gráfico.
    - colors: Lista de colores para cada año (ej: ["#FF9E4A", "#1F77B4", "#2CA02C", "#D62728"]).
    """
    if len(df_list) != len(years) or len(df_list) != len(colors):
        raise ValueError(
            "Las listas de DataFrames, años y colores deben tener la misma longitud."
        )

    # Crear secuencia de posiciones (ej: Día 1, Día 2, ...)
    max_length = max(len(df) for df in df_list)
    positions = [f"Dia {i+1}" for i in range(max_length)]

    fig = px.area()  # Figura vacía

    # Añadir cada año como un área
    for df, year, color in zip(df_list, years, colors):
        df = df.reset_index(drop=True)  # Ignorar fechas
        fig.add_trace(
            px.line(
                df,
                x=positions[: len(df)],
                y=field,
                markers=False,
                color_discrete_sequence=[color],
            )
            .update_traces(
                name=year,
                showlegend=True,
                line_width=2,
                # marker_size=4,
                hovertemplate=(
                    f"<b>{year}</b>=%{{y:,}}<extra></extra>"  # Año en negrita
                ),
            )
            .data[0]
        )

    # Personalización
    fig.update_layout(
        plot_bgcolor="white",
        yaxis_title=field,
        yaxis_tickformat=",d",
        yaxis=dict(
            showgrid=True,  # Activar grid
            gridcolor="lightgray",  # Color del grid
            gridwidth=0.5,  # Grosor de las líneas
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=0.3,  # Más delgado que el horizontal
            tickangle=-45,
        ),
        title=dict(text=field, font_size=18),
        legend_title_text="Any",
        hovermode="x unified",
        height=450,  # Altura ajustable
    )

    return fig
