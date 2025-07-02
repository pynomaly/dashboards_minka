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
            map_html1 = st.session_state[map_key]["heatmap"]._repr_html_()
            components.html(map_html1, height=600)

        with map2:
            map_html2 = st.session_state[map_key]["markermap"]._repr_html_()
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


@st.cache_data(ttl=3600)
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
            total_species = session.get(url1).json().get("total_results")

            observers = f"{api_path}/observations/observers?"
            url2 = f"{observers}&project_id={v}"
            total_participants = session.get(url2).json().get("total_results")

            observations = f"{api_path}/observations?"
            url3 = f"{observations}&project_id={v}"
            total_obs = session.get(url3).json().get("total_results")

            data = {
                "provincia": k,
                "espècies": total_species,
                "participants": total_participants,
                "observacions": total_obs,
            }
            result.append(data)
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
        markers=True,
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


@st.cache_resource(ttl=3600)
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
    df.dropna(subset=["latitude", "longitude"], inplace=True)
    locations = [(lat, lon) for lat, lon in zip(df["latitude"], df["longitude"])]

    center = df[["latitude", "longitude"]].mean().tolist()

    m = folium.Map(location=center, tiles="cartodb positron", zoom_start=6)
    HeatMap(
        locations,
        radius=10,
        gradient={
            "0.1": "blue",
            "0.2": "cyan",
            "0.4": "lime",
            "0.6": "orange",
            "0.8": "red",
            "0.99": "purple",
        },
        min_opacity=0.7,
        max_opacity=0.9,
        use_local_extrema=False,
    ).add_to(m)
    return m


@st.cache_resource(ttl=3600)
def create_markercluster(df):
    df.dropna(subset=["latitude", "longitude"], inplace=True)

    lats = df["latitude"].to_list()
    lons = df["longitude"].to_list()

    locations = list(zip(lats, lons))

    # Define coordinates of where we want to center our map
    center = [np.mean(lats), np.mean(lons)]

    # tiles1 = "cartodb positron"
    attr = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
    tiles2 = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

    m = folium.Map(location=center, tiles=tiles2, attr=attr, zoom_start=6)

    marker_cluster = MarkerCluster().add_to(m)

    for i in range(len(df)):
        folium.Marker(
            location=locations[i],
            popup=folium.Popup(
                f"<b>Taxon: </b>{df['taxon_name'].values[i]}<br><b>User: </b>{df['user_login'].values[i]}<br><a href='https://minka-sdg.org/observations/{df['id'].values[i]}' target='_blank'>Minka Observation</a>",
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
