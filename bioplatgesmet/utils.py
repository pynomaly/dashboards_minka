import datetime
import math
import os

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from folium.plugins import HeatMap, MarkerCluster
from geopy.geocoders import Nominatim
from markdownlit import mdlit
from mecoda_minka import get_dfs, get_obs

try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

base_url = "https://minka-sdg.org"
api_path = f"https://api.minka-sdg.org/v1"


codes = {
    163: "Montgat",
    164: "Castelldefels",
    165: "Barcelona",
    166: "Viladecans",
    167: "Gavà",
    168: "El Prat",
    169: "Sant Adrià",
    170: "Badalona",
}


# Definición de funciones
@st.cache_data(ttl=360)
def get_main_metrics(proj_id):
    observations = "https://api.minka-sdg.org/v1/observations?"
    url3 = f"{observations}&project_id={proj_id}"
    total_obs = requests.get(url3).json()["total_results"]

    species = "https://api.minka-sdg.org/v1/observations/species_counts?"
    url1 = f"{species}&project_id={proj_id}"
    total_species = requests.get(url1).json()["total_results"]

    observers = "https://api.minka-sdg.org/v1/observations/observers?"
    url2 = f"{observers}&project_id={proj_id}"
    total_participants = requests.get(url2).json()["total_results"]

    identifiers = "https://api.minka-sdg.org/v1/observations/identifiers?"
    url4 = f"{identifiers}&project_id={proj_id}"
    total_identifiers = requests.get(url4).json()["total_results"]

    return total_obs, total_species, total_participants, total_identifiers


@st.cache_data(ttl=360)
def get_last_week_metrics(proj_id):
    last_week_date = (datetime.datetime.today() - datetime.timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )

    species = "https://api.minka-sdg.org/v1/observations/species_counts?"
    url1 = f"{species}&project_id={proj_id}&d2={last_week_date}&order=desc&order_by=created_at"
    lw_spe = requests.get(url1).json()["total_results"]

    observers = "https://api.minka-sdg.org/v1/observations/observers?"
    url2 = f"{observers}&project_id={proj_id}&d2={last_week_date}&order=desc&order_by=created_at"
    lw_part = requests.get(url2).json()["total_results"]

    observations = "https://api.minka-sdg.org/v1/observations?"
    url3 = f"{observations}&project_id={proj_id}&d2={last_week_date}&order=desc&order_by=created_at"
    lw_obs = requests.get(url3).json()["total_results"]

    identifiers = f"https://api.minka-sdg.org/v1/observations/identifiers?"
    url4 = f"{identifiers}project_id={proj_id}&d2={last_week_date}"
    lw_ident = requests.get(url4).json()["total_results"]

    return lw_obs, lw_spe, lw_part, lw_ident


@st.cache_data(ttl=360)
def get_metrics_cities(codes):
    result = []

    for k, v in codes.items():
        species = "https://api.minka-sdg.org/v1/observations/species_counts?"
        url1 = f"{species}&project_id={k}"
        total_species = requests.get(url1).json()["total_results"]

        observers = "https://api.minka-sdg.org/v1/observations/observers?"
        url2 = f"{observers}&project_id={k}"
        total_participants = requests.get(url2).json()["total_results"]

        observations = "https://api.minka-sdg.org/v1/observations?"
        url3 = f"{observations}&project_id={k}"
        total_obs = requests.get(url3).json()["total_results"]

        data = {
            "ciutat": v,
            "espècies": total_species,
            "participants": total_participants,
            "observacions": total_obs,
        }
        result.append(data)
    main_metrics = pd.DataFrame(result)
    return main_metrics


@st.cache_resource(ttl=360)
def fig_provinces(main_metrics, field, title, color):
    fig = px.bar(
        main_metrics.sort_values(by=field, ascending=False),
        x=field,
        y="ciutat",
        text_auto=",d",
        color="ciutat",
        color_discrete_map={
            "Barcelona": color,
            "El Prat de Llobregat": color,
            "Badalona": color,
            "Gavà": color,
            "Sant Adrià del Besòs": color,
            "Viladecans": color,
            "Castelldefels": color,
            "Montgat": color,
        },
    )
    fig.update_traces(
        # marker_color=["#f9b853", "#dc6619", "#089aa2"],
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=13,
        textposition="inside",
    )
    fig.update_layout(
        width=600,
        height=400,
        plot_bgcolor="#F3F5F7",
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white", font_size=15),
        title=dict(text=f"{title}", font_size=20),
        showlegend=False,
    )
    fig.update_yaxes(tickfont_size=12, automargin=True)

    return fig


@st.cache_resource(ttl=360)
def fig_bars_months(grouped, field, title, color, start_date=None, end_date=None):
    # Convertimos las fechas en el DataFrame a tipo datetime si no lo están
    # grouped["data"] = pd.to_datetime(grouped["data"])

    # Si no se proporciona start_date o end_date, tomamos el primer y último valor de la columna 'data'
    if start_date is None:
        start_date = grouped["data"].min()
    if end_date is None:
        end_date = grouped["data"].max()

    # Filtramos el DataFrame según el rango de fechas
    filtered_grouped = grouped[
        (grouped["data"] >= start_date) & (grouped["data"] <= end_date)
    ]

    # Creación de la gráfica usando el DataFrame filtrado
    fig = px.bar(
        filtered_grouped,
        x="data",
        y=field,
        text_auto=True,
    )
    fig.update_traces(
        marker_color=color,
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=13,
        textposition="outside",
    )
    fig.update_layout(
        width=600,
        height=500,
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white", font_size=15),
        title=dict(text=f"{title}", font_size=22),
        showlegend=False,
        yaxis_tickformat=",d",
        xaxis=dict(
            tickmode="array",
            tickvals=filtered_grouped["data"].to_list(),
            ticktext=filtered_grouped["data"].to_list(),
            tickfont=dict(size=14),
        ),
    )
    if len(filtered_grouped) > 20:
        fig.update_xaxes(tickangle=-45)
    else:
        fig.update_xaxes(tickangle=0)
    fig.update_yaxes(
        range=[
            0,
            filtered_grouped[field].max() + (filtered_grouped[field].max() * 0.15),
        ]
    )
    return fig


@st.cache_resource(ttl=360)
def fig_cols(df, x_field, y_field, title, color_code):

    fig = px.bar(
        df,
        x=x_field,
        y=y_field,
        text=y_field,
    )
    fig.update_traces(
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=12,
        textposition="outside",
        marker_color=color_code,
    )
    fig.update_layout(
        width=600,
        height=500,
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white"),
        title=dict(text=f"{title}", font_size=18),
        # showlegend=False,
        yaxis_tickformat=",d",
        xaxis=dict(
            tickmode="array",
            tickvals=df[x_field].to_list(),
            ticktext=df[x_field].to_list(),
            tickfont=dict(size=14),
        ),
    )
    fig.update_xaxes(tickangle=-30)
    fig.update_yaxes(range=[0, df[y_field].max() + (df[y_field].max() * 0.15)])
    return fig


@st.cache_resource(ttl=360)
def create_heatmap(df, center=None, zoom=10):
    df.dropna(subset=["latitude", "longitude"], inplace=True)
    lats = df["latitude"].to_list()
    lons = df["longitude"].to_list()

    locations = list(zip(lats, lons))
    if center is None:
        center = [np.mean(lats), np.mean(lons)]

    m = folium.Map(location=center, tiles="cartodb positron", zoom_start=zoom)
    heatmap_layer = folium.plugins.HeatMap(
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
    )

    heatmap_layer.add_to(m)
    return m


@st.cache_resource(ttl=360)
def create_markercluster(df, center=None, zoom=10):
    df.dropna(subset=["latitude", "longitude"], inplace=True)

    lats = df["latitude"].to_list()
    lons = df["longitude"].to_list()

    locations = list(zip(lats, lons))
    # Define coordinates of where we want to center our map
    if center is None:
        center = [np.mean(lats), np.mean(lons)]

    # tiles1 = "cartodb positron"
    attr = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and GIS User Community"
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


@st.cache_data(ttl=360)
def get_total_obs():
    df_total = pd.read_csv(f"{directory}/data/264_obs.csv")
    return df_total


def get_value(parameter):
    if parameter == 0 or parameter == "":
        return None
    elif parameter == st.session_state.year:
        return int(parameter)
    else:
        return parameter


def convert_table(df, index):
    return df.to_csv(index=index).encode("utf-8")


@st.cache_data(ttl=360)
def get_table_count(url, parameter):
    if parameter == "identifiers":
        results = requests.get(url).json()["results"]
        total = []
        for result in results:
            identifiers_count = {
                "name": result["user"]["login"],
                "count": result["count"],
            }
            total.append(identifiers_count)
        identifiers_count = pd.DataFrame(total)
        return identifiers_count

    elif parameter == "observers":
        results = []
        total_results = requests.get(url).json()["total_results"]

        if total_results > 500:
            num = math.ceil(total_results / 500)
            for i in range(1, num + 1):
                page_url = f"{url}&page={i}"
                results.extend(requests.get(page_url).json()["results"])
        else:
            results = requests.get(url).json()["results"]

        total = []
        for result in results:
            observers_count = {
                "name": result["user"]["login"],
                "count": result["observation_count"],
            }
            total.append(observers_count)
        observers_count = pd.DataFrame(total)
        return observers_count

    elif parameter == "species":
        results = []
        total_results = requests.get(url).json()["total_results"]

        if total_results > 500:
            num = math.ceil(total_results / 500)
            for i in range(1, num + 1):
                page_url = f"{url}&page={i}"
                results.extend(requests.get(page_url).json()["results"])
        else:
            results = requests.get(url).json()["results"]

        total = []
        for result in results:
            species_count = {"name": result["taxon"]["name"], "count": result["count"]}
            total.append(species_count)
        species_count = pd.DataFrame(total)
        return species_count


@st.cache_resource(ttl=360)
def fig_bars_months_v2(grouped, field, title, color):
    fig = px.bar(
        grouped,
        x="month",
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
            tickvals=grouped["month"].to_list(),
            ticktext=grouped["month"].to_list(),
            tickfont=dict(size=16),
        ),
    )
    fig.update_xaxes(tickangle=-90)
    return fig


def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data(ttl=360)
def get_country(lat, lon, searches):
    if f"{lat}, {lon}" in searches.keys():
        return searches[f"{lat}, {lon}"]
    else:
        try:
            geolocator = Nominatim(user_agent="mecoda")
            location = geolocator.reverse(f"{lat}, {lon}", language="en")
            try:
                country = location.raw["address"]["country"]
            except:
                country = ""
            try:
                region = location.raw["address"]["region"]
            except:
                region = ""
            try:
                state = location.raw["address"]["state"]
            except:
                state = ""
            try:
                province = location.raw["address"]["state_district"]
            except:
                province = ""
            try:
                county = location.raw["address"]["county"]
            except:
                county = ""
            searches[f"{lat}, {lon}"] = (
                country,
                region,
                state,
                province,
                county,
            )
            return country, region, state, province, county
        except:
            return "", "", "", "", ""


@st.cache_data(ttl=360)
def get_url(base_url):
    if st.session_state.id_project != 0:
        base_url = f"{base_url}&id_project={st.session_state.id_project}"
    if st.session_state.user != "":
        base_url = f"{base_url}&user_login={st.session_state.user}"
    if st.session_state.taxon != "":
        base_url = f"{base_url}&iconic_taxa={st.session_state.taxon}"
    if st.session_state.year != 0:
        base_url = f"{base_url}&year={st.session_state.year}"
    return base_url


@st.cache_data(ttl=360)
def _get_marine_worm(taxon_name):
    name_clean = taxon_name.replace(" ", "+")
    status = requests.get(
        f"https://www.marinespecies.org/rest/AphiaIDByName/{name_clean}?marine_only=true"
    ).status_code
    if (status == 200) or (status == 206):
        result = True
    else:
        result = False
    return result


@st.cache_data(ttl=360)
def get_marine(taxon_id, taxon_name, taxon_tree):
    if taxon_id == "nan":
        return ""
    else:
        try:
            return taxon_tree.loc[
                taxon_tree.taxon_id == int(taxon_id), "marine"
            ].values[0]
        except:
            return _get_marine_worm(taxon_name)


@st.cache_resource(ttl=3600)
def fig_area_evolution(df, field, title, color, start_date=None, end_date=None):
    """
    Generate an area plot to visualize the evolution of a specific field in a dataframe.

    Parameters:
    - df: The input dataframe.
    - field: The field to be plotted.
    - title: The title of the plot.
    - color: The color of the markers and lines in the plot.
    """
    if start_date is None:
        start_date = df["data"].min()
    if end_date is None:
        end_date = df["data"].max()
    filtered_df = df[(df["data"] >= start_date) & (df["data"] <= end_date)]

    if df.empty:
        raise ValueError("Input dataframe is empty.")
    fig = px.area(
        filtered_df,
        x="data",
        y=field,
        markers=False,
        height=500,
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
        title=dict(text=title, font_size=22),
        hoverlabel=dict(bgcolor="white", font_size=15),
    )
    return fig


@st.cache_data(ttl=360)
def get_last_species(city):
    df = pd.read_csv(f"{directory}/data/obs_{city}.csv")
    df2 = df.drop_duplicates(subset=["taxon_id"], keep="first")
    result = df2.sort_values(by=["created_at"], ascending=False)[
        ["taxon_name", "created_at", "id"]
    ].head(5)
    df_photos = pd.read_csv(f"{directory}/data/264_photos.csv")
    result["image"] = result["id"].apply(
        lambda x: df_photos[df_photos["id"] == x]["photos_medium_url"].head(1).item()
    )
    result["url"] = result["id"].apply(
        lambda x: f"https://minka-sdg.org/observations/{x}"
    )
    return result


@st.cache_data(ttl=360)
def get_num_species_by_city(city):
    df = pd.read_csv(f"{directory}/data/obs_{city}.csv")
    df_species = df.taxon_name.value_counts().to_frame().reset_index()
    return df_species


@st.cache_data(ttl=360)
def get_best_observers(city):
    df = pd.read_csv(f"{directory}/data/obs_{city}.csv")
    df_observers = (
        df.groupby("user_login")
        .agg("count")["id"]
        .sort_values(ascending=False)
        .to_frame()
        .reset_index()
    )
    df_observers.columns = ["nom", "observacions"]
    return df_observers


@st.cache_data(ttl=360)
def get_obs_by_rank(i_rank):
    df = pd.read_csv(f"{directory}/data/264_obs.csv")
    df2 = df[df.quality_grade == "research"]
    ranks = ["kingdom", "phylum", "class", "order", "family", "genus"]
    result_df = (
        df2.groupby(by=ranks[: i_rank + 1]).count()["id"].to_frame().reset_index()
    )
    return result_df


@st.cache_data(ttl=360)
def get_rank_names(rank_level):
    df = pd.read_csv(f"{directory}/data/264_obs.csv")
    df2 = df[df.quality_grade == "research"]
    list_names = df2[rank_level].unique()
    return list_names


@st.cache_data(ttl=360)
def build_tree(df, ranks):
    tree = []
    for _, row in df.iterrows():
        node = tree
        for col in df[ranks]:
            label = col
            value = row[col]
            existing_node = next((n for n in node if n["label"] == label), None)
            if existing_node:
                node = existing_node.get("children", [])
            else:
                new_node = {"label": label, "value": value}
                node.append(new_node)
                node = new_node.setdefault("children", [])
    return tree


@st.cache_data(ttl=360)
def get_num_species(main_project):
    num_species = []
    base_url = "https://api.minka-sdg.org/v1/observations/species_counts?"
    start_date = datetime.datetime(2022, 1, 1)
    end_date = datetime.datetime.now().replace(day=1)

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"{base_url}project_id={main_project}&introduced=true&d2={date_str}"
        try:
            total_species = requests.get(url).json()["total_results"]
            datos = {"data": date_str, "introduced_species": total_species}
            num_species.append(datos)
        except Exception as e:
            print(f"Error al obtener datos para la fecha {date_str}: {e}")
        current_date = current_date + datetime.timedelta(
            days=32
        )  # Avanzar al primer día del siguiente mes
        current_date = current_date.replace(day=1)
    return num_species


@st.cache_data(ttl=360)
def get_introduced_species(project_id, date=None):
    species = "https://api.minka-sdg.org/v1/observations/species_counts?"
    if date is None:
        url = f"{species}project_id={project_id}&introduced=true"
    else:
        url = f"{species}project_id={project_id}&introduced=true&d2={date}"
    total_species = requests.get(url).json()["total_results"]
    return total_species


@st.cache_data(ttl=720)
def get_introduced_df(project_id):
    obs = get_obs(id_project=project_id, introduced=True)
    df_obs, df_photos = get_dfs(obs)
    return df_obs, df_photos


@st.cache_data(ttl=720)
def get_count_per_day(df_obs):
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
    counts_per_day = df_obs["day_of_week"].value_counts().reset_index()
    counts_per_day.columns = ["day_of_week", "count"]

    # Ordenar los días de la semana para asegurarse de que aparezcan en el orden correcto
    dias_semana_ordenados = [
        "dilluns",
        "dimarts",
        "dimecres",
        "dijous",
        "divendres",
        "dissabte",
        "diumenge",
    ]
    counts_per_day = counts_per_day.sort_values(
        by="day_of_week",
        key=lambda x: x.map({d: i for i, d in enumerate(dias_semana_ordenados)}),
    )
    counts_per_day = counts_per_day.rename(columns={"count": "observacions"})
    return counts_per_day


@st.cache_data(ttl=720)
def get_count_by_hour(df_obs):
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
    counts_per_hour = df_with_time["hour_of_day"].value_counts().reset_index()
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

    counts_per_hour = counts_per_hour.rename(columns={"count": "observacions"})

    return counts_per_hour


def _extract_hour(x):
    try:
        return x.strftime("%H")
    except ValueError:
        return None


@st.cache_data(ttl=360)
def get_count_hour_per_day(df_obs):
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
    df_obs["observed_on_time"] = pd.to_datetime(
        df_obs["observed_on_time"], format="%H:%M:%S"
    ).dt.time
    df_obs["hour_of_day"] = df_obs["observed_on_time"].apply(_extract_hour)
    counts_per_day = df_obs[["day_of_week", "hour_of_day"]].value_counts().reset_index()
    counts_per_day.columns = ["day_of_week", "hour_of_day", "count"]

    # Ordenar los días de la semana para asegurarse de que aparezcan en el orden correcto
    dias_semana_ordenados = [
        "dilluns",
        "dimarts",
        "dimecres",
        "dijous",
        "divendres",
        "dissabte",
        "diumenge",
    ]
    counts_per_day = counts_per_day.sort_values(
        by="day_of_week",
        key=lambda x: x.map({d: i for i, d in enumerate(dias_semana_ordenados)}),
    )
    counts_per_day = counts_per_day.rename(columns={"count": "observacions"})
    return counts_per_day


@st.cache_data(ttl=720)
def get_number_species(df):
    cols = ["kingdom", "phylum", "class", "order", "family", "genus", "taxon_name"]
    df_total = pd.DataFrame(columns=["name", "parent", "number"])

    for i in range(len(cols)):
        group_cols = cols[: i + 1]
        group_name = cols[i]
        parent_name = cols[i - 1] if i > 0 else None

        group_data = df.groupby(group_cols).size().reset_index(name="number")
        group_data.columns = group_cols + ["number"]
        group_data["name"] = group_data[group_name]
        group_data["parent"] = group_data[parent_name] if parent_name else "Life"
        group_data.drop(group_name, axis=1, inplace=True)

        df_total = pd.concat([df_total, group_data])

    df_total = df_total[["name", "parent", "number"]].reset_index(drop=True)
    return df_total


@st.cache_resource(ttl=720)
def get_photo_from_ob(df, id_obs):
    image = df.loc[df["id"] == id_obs, "photos_medium_url"].values[0]
    response = requests.get(image)
    st.image(response.content)
    mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")


def get_photo_url_from_taxon(taxon_id):
    """Get photo URL from taxon ID"""
    taxon_id = int(taxon_id)
    url = f"https://minka-sdg.org/taxa/{taxon_id}.json"
    photo_url = requests.get(url).json()["photo_url"]
    photo_url = photo_url.replace("/square.", "/large.")
    return photo_url


@st.cache_resource(ttl=720)
def heatmap_day_hour(df_time):
    # Crear un DataFrame con todas las combinaciones de horas y días posibles
    dias = [
        "dilluns",
        "dimarts",
        "dimecres",
        "dijous",
        "divendres",
        "dissabte",
        "diumenge",
    ]
    horas = [str(i).zfill(2) for i in range(24)]  # Generar horas de 00 a 23
    combinaciones = [(dia, hora) for dia in dias for hora in horas]

    # Crear un DataFrame con las combinaciones posibles
    df_completo = pd.DataFrame(combinaciones, columns=["day_of_week", "hour_of_day"])

    # Combinar los datos reales con el DataFrame completo para rellenar los valores faltantes con 0
    df = pd.merge(
        df_completo, df_time, on=["day_of_week", "hour_of_day"], how="left"
    ).fillna(0)

    # Ordenar el DataFrame
    df["day_of_week"] = pd.Categorical(
        df["day_of_week"], categories=dias[::-1], ordered=True
    )
    df = df.sort_values(by=["day_of_week", "hour_of_day"], ascending=True)

    # Crear el heatmap
    heatmap = go.Figure(
        data=go.Heatmap(
            z=df["observacions"],
            x=df["hour_of_day"],
            y=df["day_of_week"],
            xgap=3,
            ygap=3,
            hovertemplate="Hora: %{x}<br>Dia: %{y}<br>Observacions: %{z}",
            colorscale=[[0, "rgb(255,255,255)"], [1, "#0081B8"]],
            texttemplate="%{z}",
        )
    )

    # Personalizar el layout del heatmap
    heatmap.update_layout(
        title="",
        xaxis_title="Hora del dia",
        yaxis_title="Dia de la setmana",
        font=dict(size=12),
        width=800,
        height=600,
        xaxis=dict(
            side="top",
            tickmode="array",
            tickvals=horas,
            ticktext=horas,
            tickfont=dict(color="black", size=13),
        ),
        yaxis=dict(
            gridcolor="white",
            tickfont=dict(color="black", size=13),
        ),
        hoverlabel=dict(bgcolor="white", font_size=14),
        showlegend=False,
    )

    return heatmap


@st.cache_resource(ttl=720)
def fig_monthly_bars(df_obs):
    # Agrupa los datos por mes y especie, y cuenta el número de observaciones
    df_obs.observed_on = pd.to_datetime(df_obs.observed_on)
    observations_per_month = (
        df_obs.groupby([pd.Grouper(key="observed_on", freq="ME")])
        .size()
        .reset_index(name="num_observations")
    )

    # Gráfico de barras
    fig = px.bar(
        observations_per_month,
        x="observed_on",
        y="num_observations",
        text_auto=",d",
        # title="Número de Observaciones por Mes",
        labels={"num_observations": "Observacions", "observed_on": "Mes"},
    )

    fig.update_traces(
        marker_color="#0081B8",
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=12,
        textposition="outside",
    )
    fig.update_layout(
        width=600,
        height=500,
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white", font_size=15),
        title=dict(text=f"Nombre d'observacions per mes", font_size=22),
        showlegend=False,
        yaxis_tickformat=",d",
        xaxis=dict(
            tickmode="array",
            tickvals=observations_per_month["observed_on"].dt.date.to_list(),
            ticktext=observations_per_month["observed_on"]
            .dt.strftime("%Y-%m")
            .tolist(),
            tickfont=dict(size=14),
        ),
    )
    if len(observations_per_month) > 10:
        fig.update_xaxes(tickangle=-60)
    else:
        fig.update_xaxes(tickangle=0)

    fig.update_yaxes(
        range=[
            0,
            observations_per_month["num_observations"].max()
            + (observations_per_month["num_observations"].max() * 0.15),
        ]
    )

    return fig
