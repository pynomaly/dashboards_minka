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
import config

try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
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
            # Load only required columns for maps to reduce memory usage
            map_columns = ["latitude", "longitude", "taxon_name", "user_login", "id"]
            df_map = pd.read_csv(
                f"{directory}/data/{proj_id}_df_obs.csv", usecols=map_columns
            )
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
    if session is None:
        session = requests.Session()

    # Prepare all URLs at once
    urls = {
        "species": f"{api_path}/observations/species_counts?project_id={proj_id}",
        "observers": f"{api_path}/observations/observers?project_id={proj_id}",
        "observations": f"{api_path}/observations?project_id={proj_id}",
    }

    # Make concurrent requests would be ideal, but for simplicity we'll batch process
    results = {}
    for key, url in urls.items():
        response = session.get(url)
        response.raise_for_status()  # Better error handling
        results[key] = response.json()["total_results"]

    return results["species"], results["observers"], results["observations"]


@st.cache_data(ttl=300)
def get_last_week_metrics(proj_id, session=None):
    last_week_date = (datetime.datetime.today() - datetime.timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )
    if session is None:
        session = requests.Session()

    # Common parameters
    common_params = (
        f"project_id={proj_id}&d2={last_week_date}&order=desc&order_by=created_at"
    )

    # Prepare all URLs at once
    urls = {
        "species": f"{api_path}/observations/species_counts?{common_params}",
        "observers": f"{api_path}/observations/observers?{common_params}",
        "observations": f"{api_path}/observations?{common_params}",
    }

    results = {}
    for key, url in urls.items():
        response = session.get(url)
        response.raise_for_status()
        results[key] = response.json()["total_results"]

    return results["observations"], results["species"], results["observers"]


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

    # Pre-calculate tick values for better performance
    tick_values = grouped["data"].tolist()

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
        title=dict(text=title, font_size=18),
        showlegend=False,
        yaxis_tickformat=",d",
        xaxis=dict(
            tickmode="array",
            tickvals=tick_values,
            ticktext=tick_values,
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
    # Define columns to keep from last_obs to reduce memory usage
    obs_columns = [
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

    last_obs = pd.read_csv(
        f"{directory}/data/{proj_id}_df_obs.csv", usecols=obs_columns
    )
    last_photos = pd.read_csv(f"{directory}/data/{proj_id}_df_photos.csv")

    # Merge with more efficient left join
    total = pd.merge(last_photos, last_obs, on="id", how="left")

    # Filter and process in a single chain operation
    excluded_logins = {"xasalva", "mediambient_ajelprat"}  # Use set for faster lookup
    last_total = (
        total[
            (~total.user_login.isin(excluded_logins))
            & (total.quality_grade == "research")
        ]
        .drop_duplicates(subset="id")
        .sort_values(by="id", ascending=False)
        .reset_index(drop=True)
    )

    return last_total


@st.cache_resource(ttl=3600)
def create_heatmap(df):
    # Create a copy to avoid modifying original dataframe
    df_clean = df.dropna(subset=["latitude", "longitude"]).copy()

    if df_clean.empty:
        # Return empty map if no valid coordinates
        return folium.Map(location=[0, 0], tiles="cartodb positron", zoom_start=2)

    # More efficient location extraction using numpy
    locations = df_clean[["latitude", "longitude"]].values.tolist()
    center = df_clean[["latitude", "longitude"]].mean().tolist()

    m = folium.Map(location=center, tiles="cartodb positron", zoom_start=5)
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
    # Create a copy to avoid modifying original dataframe
    df_clean = df.dropna(subset=["latitude", "longitude"]).copy()

    if df_clean.empty:
        return folium.Map(location=[0, 0], tiles="cartodb positron", zoom_start=2)

    # More efficient coordinate extraction
    coords = df_clean[["latitude", "longitude"]].values
    center = coords.mean(axis=0).tolist()

    attr = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
    tiles2 = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

    m = folium.Map(location=center, tiles=tiles2, attr=attr, zoom_start=5)
    marker_cluster = MarkerCluster().add_to(m)

    # More efficient iteration using iterrows
    for _, row in df_clean.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(
                f"<b>Taxon: </b>{row['taxon_name']}<br><b>User: </b>{row['user_login']}<br><a href='https://minka-sdg.org/observations/{row['id']}' target='_blank'>Minka Observation</a>",
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
    meses = {
        f"{year}-05": ["01", "31"],
        f"{year}-06": ["01", "30"],
        f"{year}-07": ["01", "31"],
        f"{year}-08": ["01", "31"],
        f"{year}-09": ["01", "30"],
        f"{year}-10": ["01", "15"],
    }

    # Define base URLs once
    base_urls = {
        "observations": f"{api_path}/observations",
        "species": f"{api_path}/observations/species_counts",
        "observers": f"{api_path}/observations/observers",
    }

    results_by_month = []

    with requests.Session() as session:
        for mes, limits in meses.items():
            params = {
                "project_id": project_id,
                "d1": f"{mes}-{limits[0]}",
                "d2": f"{mes}-{limits[1]}",
            }

            # Batch API calls with error handling
            month_data = {"data": mes}

            for key, url in base_urls.items():
                try:
                    response = session.get(url, params=params)
                    response.raise_for_status()
                    result = response.json()["total_results"]
                except (requests.RequestException, KeyError) as e:
                    print(f"Error fetching {key} for {mes}: {e}")
                    result = 0

                if key == "observations":
                    month_data["observações"] = result
                elif key == "species":
                    month_data["espécies"] = result
                elif key == "observers":
                    month_data["participantes"] = result

            results_by_month.append(month_data)

    return pd.DataFrame(results_by_month)


# Toma dataframe de main_metrics hasta día actual
def get_previous_years(main_metrics_filtered, year):
    # Datos de 2024
    df_2024 = pd.read_csv(f"{directory}/data/{year}_main_metrics.csv")
    df_2024_filtered = df_2024.loc[: len(main_metrics_filtered) - 1, :].copy()
    df_2024_filtered.rename(
        columns={
            "date": "data",
            "observations": "observações",
            "species": "espécies",
            "participants": "participantes",
        },
        inplace=True,
    )

    return df_2024_filtered


def fig_multi_year_comparison(df_list, years, field, colors):
    """
    Compara múltiples años alineados por posición (día 1 vs día 1, etc.).

    Parámetros:
    - df_list: Lista de DataFrames [df_2022, df_2023, df_2024, df_2025].
    - years: Lista de etiquetas para los años (ej: ["2022", "2023", "2024", "2025"]).
    - field: Columna a comparar (ej: "ventas").
    - colors: Lista de colores para cada año (ej: ["#FF9E4A", "#1F77B4", "#2CA02C", "#D62728"]).
    """
    if len(df_list) != len(years) or len(df_list) != len(colors):
        raise ValueError(
            "Las listas de DataFrames, años y colores deben tener la misma longitud."
        )

    # Crear secuencia de posiciones (ej: Día 1, Día 2, ...) - optimized
    max_length = max(len(df) for df in df_list)
    positions = [f"Dia {i+1}" for i in range(max_length)]

    fig = px.area()  # Figura vacía

    # Añadir cada año como un área - optimized loop
    for df, year, color in zip(df_list, years, colors):
        df_reset = df.reset_index(drop=True)  # Avoid modifying original
        df_length = len(df_reset)

        # Create line trace more efficiently
        line_fig = px.line(
            df_reset,
            x=positions[:df_length],
            y=field,
            markers=False,
            color_discrete_sequence=[color],
        )

        trace = line_fig.data[0]
        trace.update(
            name=year,
            showlegend=True,
            line_width=3,
            hovertemplate=f"<b>{year}</b>=%{{y:,}}<extra></extra>",
        )

        fig.add_trace(trace)

    # Personalización optimizada
    fig.update_layout(
        plot_bgcolor="white",
        yaxis_title=field,
        yaxis_tickformat=",d",
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=0.5,
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=0.1,
            tickangle=-45,
        ),
        title=dict(text=field, font_size=18),
        legend_title_text="Any",
        hovermode="x unified",
        height=450,
    )

    return fig
