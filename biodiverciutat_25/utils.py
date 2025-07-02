import datetime
import os

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from folium.plugins import HeatMap, MarkerCluster
from markdownlit import mdlit
from mecoda_minka import get_dfs, get_obs

try:
    directory = f"{os.environ['DASHBOARDS']}/biodiverciutat_25"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

exclude_users = [
    "xasalva",
    "admin",
    "aluna",
    "bertinhaco",
    "andrea",
    "laurabiomar",
    "guillermoalvarez_fecdas",
    "mediambient_ajelprat",
    "fecdas_mediambient",
    "planctondiving",
    "marinagm",
    "CEM",
    "uri_domingo",
    "mimo_fecdas",
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "anellides",
    "irodero",
    "manelsalvador",
    "sara_riera",
    "verificador_1",
    "loreto_rodriguez",
]

API_PATH = "https://api.minka-sdg.org/v1"

colors = ["#4aae79", "#007d8a", "#00a3b4"]

main_proj = 233

projects = {
    79: "Begues",
    80: "Viladecans",
    81: "Sant Climent de Llobregat",
    83: "Cervelló",
    85: "Sant Boi de Llobregat",
    86: "Santa Coloma de Cervelló",
    87: "Sant Vicenç dels Horts",
    88: "la Palma de Cervelló",
    89: "Corbera de Llobregat",
    91: "Sant Andreu de la Barca",
    92: "Castellbisbal",
    93: "el Papiol",
    94: "Molins de Rei",
    95: "Sant Feliu de Llobregat",
    97: "Cornellà de Llobregat",
    98: "l'Hospitalet de Llobregat",
    99: "Esplugues de Llobregat",
    100: "Sant Just Desvern",
    101: "Sant Cugat del Vallès",
    102: "Barberà del Vallès",
    103: "Ripollet",
    104: "Montcada i Reixac",
    106: "Sant Adrià de Besòs",
    107: "Badalona",
    108: "Tiana",
    109: "Montgat",
    224: "Barcelona",
    225: "el Prat de Llobregat",
    226: "Pallejà",
    227: "Torrelles de Llobregat",
    228: "Castelldefels",
    229: "Gavà",
    230: "Sant Joan Despí",
    231: "Santa Coloma de Gramenet",
    232: "Àrea marina Barcelona",
}


@st.cache_data(ttl=60)
def get_main_metrics(proj_id):
    species = f"{API_PATH}/observations/species_counts?"
    url1 = f"{species}&project_id={proj_id}"
    total_species = requests.get(url1).json()["total_results"]

    observers = f"{API_PATH}/observations/observers?"
    url2 = f"{observers}&project_id={proj_id}"
    total_participants = requests.get(url2).json()["total_results"]

    observations = f"{API_PATH}/observations?"
    url3 = f"{observations}&project_id={proj_id}"
    total_obs = requests.get(url3).json()["total_results"]

    return total_species, total_participants, total_obs


@st.cache_data(ttl=60)
def get_last_week_metrics(proj_id):
    last_week_date = (datetime.datetime.today() - datetime.timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )

    species = f"{API_PATH}/observations/species_counts?"
    url1 = f"{species}&project_id={proj_id}&created_d1={last_week_date}&order=desc&order_by=created_at"
    lw_spe = requests.get(url1).json()["total_results"]

    observers = f"{API_PATH}/observations/observers?"
    url2 = f"{observers}&project_id={proj_id}&created_d1={last_week_date}&order=desc&order_by=created_at"
    lw_part = requests.get(url2).json()["total_results"]

    observations = f"{API_PATH}/observations?"
    url3 = f"{observations}&project_id={proj_id}&created_d1={last_week_date}&order=desc&order_by=created_at"
    lw_obs = requests.get(url3).json()["total_results"]
    return lw_obs, lw_spe, lw_part


@st.cache_resource(ttl=60)
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
    fig = px.bar(
        df,
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
        title=dict(text=f"{title}", font_size=22),
        showlegend=False,
        yaxis_tickformat=",d",
        xaxis=dict(
            tickmode="array",
            tickvals=df["data"].to_list(),
            ticktext=df["data"].to_list(),
            tickfont=dict(size=14),
            tickangle=-90,
        ),
    )
    return fig


@st.cache_data(ttl=60)
def get_metrics_cities(projects):

    result = []

    session = requests.Session()

    with requests.Session() as session:
        for k, v in projects.items():
            species = f"{API_PATH}/observations/species_counts?"
            url1 = f"{species}&project_id={k}"
            total_species = session.get(url1).json().get("total_results")

            observers = f"{API_PATH}/observations/observers?"
            url2 = f"{observers}&project_id={k}"
            total_participants = session.get(url2).json().get("total_results")

            observations = f"{API_PATH}/observations?"
            url3 = f"{observations}&project_id={k}"
            total_obs = session.get(url3).json().get("total_results")

            data = {
                "city": v,
                "espècies": total_species,
                "participants": total_participants,
                "observacions": total_obs,
            }
            result.append(data)
    main_metrics_cities = pd.DataFrame(result)
    return main_metrics_cities


@st.cache_resource(ttl=60)
def fig_cities(main_metrics: pd.DataFrame, field: str, title: str) -> px.bar:
    """
    Generate a bar chart of the main metrics for each province.

    Parameters:
    - main_metrics (DataFrame): The main metrics data.
    - field (str): The field to use for sorting the data.
    - title (str): The title of the chart.

    Returns:
    - fig (plotly.graph_objects.Figure): The generated bar chart.
    """
    city_ranking = main_metrics.sort_values(by=field, ascending=False)["city"].to_list()

    fig = px.bar(
        main_metrics.sort_values(by=field, ascending=False).head(5),
        x=field,
        y="city",
        text_auto=",d",
        color="city",
        color_discrete_map={
            city_ranking[0]: "#426A5A",
            city_ranking[1]: "#4AAE79",
            city_ranking[2]: "#4AAE79",
            city_ranking[3]: "#4AAE79",
            city_ranking[4]: "#4AAE79",
        },
    )
    fig.update_traces(
        marker_line_color="#265769",
        marker_line_width=2,
        textfont_size=14,
        textposition="inside",
    )
    fig.update_layout(
        # width=700,
        height=350,
        plot_bgcolor="#F1F9F5",
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white"),
        title=dict(text=f"{title}", font_size=18),
        showlegend=False,
    )
    fig.update_yaxes(tickfont_size=13)

    return fig


@st.cache_resource(ttl=60)
def create_heatmap(df, center=None, zoom=10.5):
    df.dropna(subset=["latitude", "longitude"], inplace=True)
    lats = df["latitude"].to_list()
    lons = df["longitude"].to_list()

    locations = list(zip(lats, lons))
    if center is None:
        center = [np.mean(lats), np.mean(lons)]

    m = folium.Map(location=center, tiles="cartodb positron", zoom_start=zoom)
    HeatMap(
        locations,
        radius=10,
        gradient={
            "0.1": "blue",
            "0.2": "blue",
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


@st.cache_resource(ttl=60)
def create_markercluster(df, center=None, zoom=10.5):
    df.dropna(subset=["latitude", "longitude"], inplace=True)

    lats = df["latitude"].to_list()
    lons = df["longitude"].to_list()

    locations = list(zip(lats, lons))

    # Define coordinates of where we want to center our map
    if center is None:
        center = [np.mean(lats), np.mean(lons)]

    # tiles1 = "cartodb positron"
    attr = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
    tiles2 = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

    m = folium.Map(location=center, tiles=tiles2, attr=attr, zoom_start=zoom)

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


@st.cache_resource(ttl=60)
def get_photo_from_ob(df, id_obs):
    image = df.loc[df["id"] == id_obs, "photos_medium_url"].values[0]
    response = requests.get(image)
    st.image(response.content)
    mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")


@st.cache_data(ttl=60)
def get_number_species(df):
    cols = ["kingdom", "phylum", "class", "order", "family", "genus", "taxon_name"]
    df_total = pd.DataFrame(columns=["name", "rank", "parent", "number"])

    for i in range(len(cols)):
        group_cols = cols[: i + 1]
        group_name = cols[i]
        parent_name = cols[i - 1] if i > 0 else None
        rank_name = group_name.capitalize()

        group_data = df.groupby(group_cols).size().reset_index(name="number")
        group_data.columns = group_cols + ["number"]
        group_data["name"] = group_data[group_name]
        group_data["parent"] = group_data[parent_name] if parent_name else "Life"
        group_data["rank"] = rank_name
        group_data.drop(group_name, axis=1, inplace=True)

        df_total = pd.concat([df_total, group_data])

    df_total = df_total[["name", "rank", "parent", "number"]].reset_index(drop=True)
    return df_total


@st.cache_data(ttl=60)
def get_marine_terrestrial(df_obs):
    terrestrial_species = (
        df_obs[df_obs.marine == False][["taxon_name", "taxon_id"]]
        .value_counts()
        .to_frame()
        .reset_index()
    )
    terrestrial_species["taxa_url"] = terrestrial_species.taxon_id.apply(
        lambda x: f"https://minka-sdg.org/taxa/{int(x)}"
    )
    terrestrial_species.drop(columns="taxon_id", inplace=True)

    marine_species = (
        df_obs[df_obs.marine == True][["taxon_name", "taxon_id"]]
        .value_counts()
        .to_frame()
        .reset_index()
    )
    marine_species["taxa_url"] = marine_species.taxon_id.apply(
        lambda x: f"https://minka-sdg.org/taxa/{int(x)}"
    )
    marine_species.drop(columns="taxon_id", inplace=True)
    return marine_species, terrestrial_species


@st.cache_data(ttl=60)
def _get_species(user_name, proj_id):
    species = f"{API_PATH}/observations/species_counts"
    params = {"project_id": proj_id, "user_login": user_name}
    return requests.get(species, params=params).json()["total_results"]


@st.cache_data(ttl=60)
def _get_identifiers(user_name, proj_id):
    identifiers = f"{API_PATH}/observations/identifiers"
    params = {"project_id": proj_id, "user_login": user_name}
    return requests.get(identifiers, params=params).json()["total_results"]


@st.cache_data(ttl=60)
def get_participation_df(df_obs, proj_id):
    pt_users = (
        df_obs["user_login"]
        .value_counts()
        .to_frame()
        .reset_index(drop=False)
        .rename(columns={"user_login": "participant", "count": "observacions"})
    )
    pt_users["identificacions"] = pt_users["participant"].apply(
        lambda x: _get_identifiers(x, proj_id)
    )
    pt_users["espècies"] = pt_users["participant"].apply(
        lambda x: _get_species(x, proj_id)
    )
    return pt_users


@st.cache_data(ttl=60)
def get_count_per_day(df_obs, mode=None):
    dias_semana = {
        "Monday": "dilluns",
        "Tuesday": "dimarts",
        "Wednesday": "dimecres",
        "Thursday": "dijous",
        "Friday": "divendres",
        "Saturday": "dissabte",
        "Sunday": "diumenge",
    }
    df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])
    df_obs["day_of_week"] = df_obs["observed_on"].dt.day_name().map(dias_semana)
    if mode == None:
        counts_per_day = df_obs["day_of_week"].value_counts().reset_index()
    elif mode == "users":
        counts_per_day = (
            df_obs.groupby("day_of_week")["user_login"].nunique().reset_index()
        )
    counts_per_day.columns = ["day_of_week", "count"]

    # Reindexar para asegurar que aparezcan todos los días de la semana
    dias_semana_ordenados = [
        "divendres",
        "dissabte",
        "diumenge",
        "dilluns",
    ]
    counts_per_day = (
        counts_per_day.set_index("day_of_week")
        .reindex(dias_semana_ordenados, fill_value=0)
        .reset_index()
    )

    # counts_per_day = counts_per_day.rename(columns={"count": "observacions"})

    return counts_per_day


@st.cache_data(ttl=60)
def get_count_by_hour(df_obs, mode=None):
    # Convertimos la columna a time
    df_obs["observed_on_time"] = pd.to_datetime(
        df_obs["observed_on_time"], format="%H:%M:%S"
    ).dt.time

    # Seleccionamos observaciones con hora registrada
    df_with_time = df_obs[df_obs.observed_on_time.notnull()].copy()

    # Extraer la hora del día como una cadena de texto
    df_with_time["hour_of_day"] = df_with_time["observed_on_time"].apply(
        lambda x: x.strftime("%H")
    )

    # Calcular el recuento de observaciones por hora del día
    if mode == None:
        counts_per_hour = df_with_time["hour_of_day"].value_counts().reset_index()
    elif mode == "users":
        counts_per_hour = (
            df_with_time.groupby("hour_of_day")["user_login"].nunique().reset_index()
        )
    counts_per_hour.columns = ["hour_of_day", "count"]

    # Ordenar por hora del día
    counts_per_hour = counts_per_hour.sort_values(by="hour_of_day")

    # Crear un DataFrame con todas las horas del día
    all_hours = pd.DataFrame({"hour_of_day": [str(i).zfill(2) for i in range(24)]})

    # Unir este DataFrame con el DataFrame que contiene el recuento de observaciones por hora
    counts_per_hour = pd.merge(all_hours, counts_per_hour, on="hour_of_day", how="left")

    # Rellenar los valores de recuento faltantes con 0
    counts_per_hour["count"] = counts_per_hour["count"].fillna(0)

    # Ordenar por hora del día
    counts_per_hour = counts_per_hour.sort_values(by="hour_of_day")

    # counts_per_hour = counts_per_hour.rename(columns={"count": "nombre"})

    return counts_per_hour


@st.cache_resource(ttl=60)
def fig_cols(df, x_field, y_field, title, color_field):
    # gradiente personalizado de azules
    # colors_custom = ["#47EDFF", "#00a3b4", "#007d8a", "#265769"]
    colors_custom = ["#8DCEAB", "#4AAE79", "#426A5A"]

    fig = px.bar(
        df,
        x=x_field,
        y=y_field,
        text=y_field,
        color=color_field,  # Usar el campo de color para definir el gradiente
        color_continuous_scale=colors_custom,
    )
    fig.update_traces(
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=12,
        textposition="outside",
    )
    fig.update_layout(
        # width=600,
        # height=300,
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white"),
        title=dict(text=f"{title}", font_size=18),
        coloraxis_showscale=False,
        yaxis_tickformat=",d",
        xaxis=dict(
            tickmode="array",
            tickvals=df[x_field].to_list(),
            ticktext=df[x_field].to_list(),
            tickfont=dict(size=14),
        ),
    )
    fig.update_xaxes(tickangle=0)
    fig.update_yaxes(range=[0, df[y_field].max() + 10])
    return fig


@st.cache_data(ttl=60)
def get_introduced_species(project_id, date=None):
    species = "https://api.minka-sdg.org/v1/observations/species_counts?"
    if date is None:
        url = f"{species}project_id={project_id}&introduced=true"
    else:
        url = f"{species}project_id={project_id}&introduced=true&d2={date}"
    total_species = requests.get(url).json()["total_results"]
    return total_species


@st.cache_data(ttl=60)
def get_introduced_df(project_id):
    obs = get_obs(id_project=project_id, introduced=True)
    if len(obs) > 0:
        df_obs, df_photos = get_dfs(obs)
        return df_obs, df_photos
    else:
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(ttl=60)
def create_geo_df() -> pd.DataFrame:
    archivo_geojson = f"{directory}/data/divisions-administratives-cat-20240118/divisions-administratives-municipis-20240118.json"

    # Lee el archivo GeoJSON
    datos_geojson = gpd.read_file(archivo_geojson)

    df_projects = pd.read_csv(f"{directory}/data/233_main_metrics_projects.csv")

    datos_completos = pd.merge(
        datos_geojson, df_projects, left_on="NOMMUNI", right_on="city", how="right"
    )

    datos_completos.rename(
        columns={
            "AREAM5000": "Area",
            "observations": "Observacions",
            "species": "Espècies",
            "participants": "Participants",
        },
        inplace=True,
    )

    datos_completos["Area"] = round(datos_completos["Area"], 2)

    datos_completos.index = datos_completos.Area.astype(str)
    return datos_completos
