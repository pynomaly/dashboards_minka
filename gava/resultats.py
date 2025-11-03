import os
from datetime import datetime

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components
from folium.plugins import MarkerCluster
from mecoda_minka import get_dfs, get_obs

# configuración de ModeBar
config_modebar = {
    "displayModeBar": True,  # Mostrar u ocultar la ModeBar
    "modeBarButtonsToRemove": [  # Lista de botones a remover
        "zoom2d",  # Eliminar el botón de zoom
        "pan2d",  # Eliminar el botón de paneo
        "lasso2d",  # Eliminar el botón de lazo
        "select2d",
        "autoScale2d",  # Eliminar el botón de autoescalar
        "resetScale2d",  # Eliminar el botón de resetear escala
        "hoverClosestCartesian",  # Eliminar el botón de acercar el hover
        "hoverCompareCartesian",  # Eliminar el botón de comparar en hover
        "zoomIn2d",  # Eliminar el botón de zoom +
        "zoomOut2d",  # Eliminar el botón de zoom -
    ],
    "displaylogo": False,  # Ocultar el logo de Plotly
}

try:
    directory = f"{os.environ['DASHBOARDS']}/gava"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="MINKA Resultats a Gavà",
)


# año actual + 1
last_year = datetime.now().year + 1

# place de municipio de Gavà
place = 278

# Funciones


@st.cache_data(ttl=3600)
def create_markercluster(df, center=None, zoom=13):
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

    # Añadir clúster de marcadores
    marker_cluster = MarkerCluster().add_to(m)

    for i in range(len(df)):
        folium.Marker(
            location=locations[i],
            popup=folium.Popup(
                f"<b>Taxon: </b>{df['taxon_name'].values[i]}<br><b>User: </b>{df['user_login'].values[i]}<br><a href='https://minka-sdg.org/observations/{df['id'].values[i]}' target='_blank'>MINKA observació</a>",
                min_width=150,
                max_width=150,
            ),
            icon=folium.Icon(color="green", icon="fa-solid fa-binoculars", prefix="fa"),
        ).add_to(marker_cluster)

    return m


# devuelve acumulado por año y guarda las observaciones
@st.cache_data(ttl=3600, show_spinner="Carregant mètriques principals...")
def get_observations(place):
    # Comprobación si hay obs nuevas
    df_obs = pd.read_csv(f"{directory}/data/df_obs_total.csv")
    response = requests.get(
        f"https://api.minka-sdg.org/v1/observations?place_id={place}"
    ).json()
    total_results = response["total_results"]

    # Descarga si hay nuevas observaciones
    if len(df_obs) == total_results:
        obs = get_obs(place_id=place)
        df_obs, __ = get_dfs(obs)
        df_obs["created_at"] = pd.to_datetime(df_obs["created_at"])
        df_obs["year_uploaded"] = df_obs["created_at"].dt.year
        df_obs["minka_link"] = (
            df_obs["id"]
            .astype(str)
            .apply(lambda x: f"https://minka-sdg.org/observations/{x}")
        )
        df_obs.to_csv(f"{directory}/data/df_obs_total.csv", index=False)

    # Acumulado por año
    observations_by_year = []
    for year in range(2022, last_year):
        data = {"year": year}
        data["total_obs"] = len(df_obs[df_obs["year_uploaded"] == year])
        data["research_grade_obs"] = len(
            df_obs[
                (df_obs["year_uploaded"] == year)
                & (df_obs["quality_grade"] == "research")
            ]
        )
        data["no_research_grade_obs"] = len(
            df_obs[
                (df_obs["year_uploaded"] == year)
                & (df_obs["quality_grade"] != "research")
            ]
        )
        observations_by_year.append(data)

    df_observations = pd.DataFrame(observations_by_year)
    return df_observations


# especies por año y desglose
@st.cache_data(ttl=3600)
def get_species(place: int, mode="by_year"):
    if mode == "by_year":
        species_by_year = []
        for year in range(2022, last_year):
            data = {"year": year}
            url = f"https://api.minka-sdg.org/v1/observations/species_counts?place_id={place}&year={year}"
            response = requests.get(url).json()
            data["total_species_by_year"] = response["total_results"]
            data["species_list"] = []
            for sp in response["results"]:
                sp_count = {}
                try:
                    sp_count["taxon_group"] = sp["taxon"]["iconic_taxon_name"]
                except:
                    sp_count["taxon_group"] = None
                sp_count["taxon_id"] = sp["taxon"]["id"]
                sp_count["taxon_name"] = sp["taxon"]["name"]
                sp_count["taxon_count"] = sp["count"]
                data["species_list"].append(sp_count)
            species_by_year.append(data)
        df_species = pd.DataFrame(species_by_year)
        # Expandir la columna species_list
        df_expanded = df_species.explode("species_list").reset_index(drop=True)

        # Convertir los diccionarios en columnas
        df_species = pd.concat(
            [
                df_expanded[
                    ["year", "total_species_by_year"]
                ],  # Mantener las columnas originales que quieras
                pd.json_normalize(df_expanded["species_list"]),
            ],
            axis=1,
        )

        return df_species

    elif mode == "total":
        total_species = []
        url = (
            f"https://api.minka-sdg.org/v1/observations/species_counts?place_id={place}"
        )
        response = requests.get(url).json()
        for sp in response["results"]:
            sp_count = {}
            try:
                sp_count["taxon_group"] = sp["taxon"]["iconic_taxon_name"]
            except:
                sp_count["taxon_group"] = None
            sp_count["taxon_id"] = sp["taxon"]["id"]
            sp_count["taxon_name"] = sp["taxon"]["name"]
            sp_count["taxon_count"] = sp["count"]
            total_species.append(sp_count)
        df_total_species = pd.DataFrame(total_species)
        df_total_species["taxon_url"] = df_total_species["taxon_name"].apply(
            lambda x: f"https://minka-sdg.org/taxa/{x}"
        )
        return df_total_species


# El número total de participantes y su desglose por años.
@st.cache_data(ttl=3600)
def get_observers(place, mode="by_year"):
    if mode == "by_year":
        observers_by_year = []
        for year in range(2022, 2026):
            data = {"year": year}
            url = f"https://api.minka-sdg.org/v1/observations/observers?place_id={place}&year={year}"
            response = requests.get(url).json()
            data["total_observers_by_year"] = response["total_results"]
            data["observers_list"] = []
            for sp in response["results"]:
                observers_count = {}
                observers_count["user_id"] = sp["user"]["id"]
                observers_count["user_login"] = sp["user"]["login"]
                observers_count["observation_count"] = sp["observation_count"]
                observers_count["species_count"] = sp["species_count"]
                data["observers_list"].append(observers_count)
            observers_by_year.append(data)

        df_observers = pd.DataFrame(observers_by_year)

        df_expanded = df_observers.explode("observers_list").reset_index(drop=True)

        # Convertir los diccionarios en columnas
        df_observers = pd.concat(
            [
                df_expanded[
                    ["year", "total_observers_by_year"]
                ],  # Mantener las columnas originales que quieras
                pd.json_normalize(df_expanded["observers_list"]),
            ],
            axis=1,
        )

        return df_observers
    elif mode == "total":
        url = f"https://api.minka-sdg.org/v1/observations/observers?place_id={place}"
        response = requests.get(url).json()
        total_observers = []
        for sp in response["results"]:
            observers_count = {}
            observers_count["user_id"] = sp["user"]["id"]
            observers_count["user_login"] = sp["user"]["login"]
            observers_count["user_name"] = sp["user"]["name"]
            observers_count["observation_count"] = sp["observation_count"]
            observers_count["species_count"] = sp["species_count"]
            total_observers.append(observers_count)
        df_total_observers = pd.DataFrame(total_observers)
        return df_total_observers


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


# Descarga los datos
if "df_obs_yearly" not in st.session_state:
    st.session_state.df_obs_yearly = get_observations(place)
if "df_obs" not in st.session_state:
    st.session_state.df_obs = pd.read_csv(f"{directory}/data/df_obs_total.csv")

if "df_species" not in st.session_state:
    st.session_state.df_species = get_species(place)
if "df_total_species" not in st.session_state:
    st.session_state.df_total_species = get_species(place, mode="total")

if "df_observers" not in st.session_state:
    st.session_state.df_observers = get_observers(place)
if "df_total_observers" not in st.session_state:
    st.session_state.df_total_observers = get_observers(place, mode="total")


# Header
with st.container():
    col1, col2 = st.columns([1, 16])
    with col1:
        st.image(f"{directory}/images/minka-logo.png")
    with col2:
        st.header(":red[Resultats a Gavà]")

# observaciones
with st.container():
    st.markdown("### ")
    st.markdown("## Observacions")
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            st.session_state.df_obs_yearly,
            x="year",
            y=["research_grade_obs", "no_research_grade_obs"],
            title="",
            color_discrete_map={
                "research_grade_obs": "#1B3F5F",
                "no_research_grade_obs": "#A0C4E4",
            },
        )
        fig.update_traces(
            hovertemplate="%{fullData.name}: %{y:,}<extra></extra>",
            selected=dict(marker=dict(opacity=1)),  # No cambiar al seleccionar
            unselected=dict(marker=dict(opacity=1)),  # No cambiar al no seleccionar
        )

        for idx in range(len(st.session_state.df_obs_yearly)):
            fig.add_annotation(
                x=idx,  # usar el índice numérico en lugar del valor de year
                y=st.session_state.df_obs_yearly.iloc[idx]["total_obs"],
                text=str(int(st.session_state.df_obs_yearly.iloc[idx]["total_obs"])),
                showarrow=False,
                yshift=10,
                font=dict(size=14, color="black"),
            )
        fig.update_xaxes(type="category")

        fig.update_layout(
            hovermode="x unified",
            hoverlabel=dict(
                font_size=14,  # Tamaño de la fuente
                # font_family="Arial"
            ),
            legend=dict(
                orientation="h",  # horizontal
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                title_text="",  # Quita el título de la leyenda
            ),
        )
        selected = st.plotly_chart(
            fig, config=config_modebar, on_select="rerun", selection_mode="points"
        )
        # Botón para descargar todo
        st.session_state.df_obs["minka_link"] = (
            st.session_state.df_obs["id"]
            .astype(str)
            .apply(lambda x: f"https://minka-sdg.org/observations/{x}")
        )
        if "csv1" not in st.session_state:
            st.session_state.csv1 = convert_df(st.session_state.df_obs)

        st.download_button(
            label="Descarrega totes les observacions",
            data=st.session_state.csv1,
            file_name="gava_observations.csv",
            mime="text/csv",
        )
    with col2:

        if selected and selected["selection"]["points"]:
            punto = selected["selection"]["points"][0]
            year_seleccionado = int(punto["x"])  # Convertir a int por si acaso

            # Obtener la lista de observaciones del año seleccionado
            df_obs_filtered = st.session_state.df_obs[
                (st.session_state.df_obs["year_uploaded"] == year_seleccionado)
            ]
            df_obs_filtered = df_obs_filtered.drop(columns=["year_uploaded"])
            df_obs_filtered["id"] = df_obs_filtered["id"].astype(str)

            st.write(
                f"#### Observacions pujades el {year_seleccionado}:&nbsp;&nbsp;&nbsp;&nbsp; {len(df_obs_filtered)}"
            )
            st.dataframe(df_obs_filtered, use_container_width=True, hide_index=True)
        else:
            st.info("Fes clic en un any per veure el llistat d'observacións")

    st.divider()

# especies
with st.container():
    st.markdown("## Espècies")
    # Species
    col1, col2 = st.columns(2)
    with col1:
        df_species_cumulative = st.session_state.df_species[
            ["year", "total_species_by_year"]
        ].drop_duplicates(keep="first")
        fig = px.bar(
            df_species_cumulative,
            x="year",
            y="total_species_by_year",
            title="",
        )
        fig.update_xaxes(type="category")
        fig.update_traces(marker_color="#1B3F5F")
        fig.update_layout(
            hoverlabel=dict(
                font_size=13,  # Tamaño de la fuente
                # font_family="Arial"
            ),
        )
        # totales encima de la columna
        for idx in range(len(df_species_cumulative)):
            fig.add_annotation(
                x=idx,  # usar el índice numérico en lugar del valor de year
                y=df_species_cumulative.iloc[idx]["total_species_by_year"],
                text=str(int(df_species_cumulative.iloc[idx]["total_species_by_year"])),
                showarrow=False,
                yshift=10,
                font=dict(size=14, color="black"),
            )
        selected = st.plotly_chart(
            fig, config=config_modebar, on_select="rerun", selection_mode="points"
        )

        # Botón para descargar todo
        if "csv2" not in st.session_state:
            st.session_state.csv2 = convert_df(st.session_state.df_total_species)

        st.download_button(
            label="Descarrega totes les espècies",
            data=st.session_state.csv2,
            file_name="gava_species.csv",
            mime="text/csv",
        )

    with col2:
        if selected and selected["selection"]["points"]:
            punto = selected["selection"]["points"][0]
            year_seleccionado = int(punto["x"])  # Convertir a int por si acaso

            # Obtener la lista de especies del año seleccionado
            species_year = st.session_state.df_species[
                st.session_state.df_species["year"] == year_seleccionado
            ]

            species_year.loc[species_year.taxon_name == "Dictyota", "taxon_group"] = (
                "Chromista"
            )
            df_species_year = pd.DataFrame(
                species_year[["taxon_group", "taxon_name", "taxon_count"]],
            )
            df_species_year["taxon_url"] = df_species_year["taxon_name"].apply(
                lambda x: f"https://minka-sdg.org/taxa/{x}"
            )

            # st.dataframe(df_species, use_container_width=True, hide_index=True)
            # df_species_year
            st.write(
                f"#### Espècies observades a {year_seleccionado}:&nbsp;&nbsp;&nbsp;&nbsp; {len(df_species_year)}"
            )

            st.data_editor(
                df_species_year[
                    ["taxon_group", "taxon_url", "taxon_count"]
                ].sort_values(by="taxon_count", ascending=False),
                column_config={
                    "taxon_url": st.column_config.LinkColumn(
                        "taxon_name", display_text=r"https://minka-sdg.org/taxa/(.*?)$"
                    ),
                    "taxon_count": st.column_config.NumberColumn(),
                },
                hide_index=True,
            )
        else:
            st.info("Fes clic en un any per veure el llistat d'espècies")

    st.divider()

# observadores
with st.container():
    st.markdown("## Observadors/es")
    # Observers
    col1, col2 = st.columns(2)
    with col1:
        df_observers_cumulative = st.session_state.df_observers[
            ["year", "total_observers_by_year"]
        ].drop_duplicates(keep="first")
        fig = px.bar(
            df_observers_cumulative,
            x="year",
            y="total_observers_by_year",
            title="",
        )
        fig.update_xaxes(type="category")
        fig.update_traces(marker_color="#1B3F5F")
        fig.update_layout(
            hoverlabel=dict(
                font_size=13,  # Tamaño de la fuente
                # font_family="Arial"
            ),
        )
        # totales encima de la columna
        for idx in range(len(df_observers_cumulative)):
            fig.add_annotation(
                x=idx,  # usar el índice numérico en lugar del valor de year
                y=df_observers_cumulative.iloc[idx]["total_observers_by_year"],
                text=str(
                    int(df_observers_cumulative.iloc[idx]["total_observers_by_year"])
                ),
                showarrow=False,
                yshift=10,
                font=dict(size=14, color="black"),
            )
        selected = st.plotly_chart(
            fig, config=config_modebar, on_select="rerun", selection_mode="points"
        )
        # Botón para descargar todo
        if "csv3" not in st.session_state:
            st.session_state.csv3 = convert_df(st.session_state.df_total_observers)

        st.download_button(
            label="Descarrega totes les persones participants",
            data=st.session_state.csv3,
            file_name="gava_observers.csv",
            mime="text/csv",
        )

    with col2:
        if selected and selected["selection"]["points"]:
            punto = selected["selection"]["points"][0]
            year_seleccionado = int(punto["x"])  # Convertir a int por si acaso

            # Obtener la lista de especies del año seleccionado
            observers_year = st.session_state.df_observers[
                st.session_state.df_observers["year"] == year_seleccionado
            ]
            df_observers_year = pd.DataFrame(
                observers_year[["user_login", "observation_count", "species_count"]],
            )
            df_observers_year["user_url"] = df_observers_year["user_login"].apply(
                lambda x: f"https://minka-sdg.org/users/{x}"
            )

            # st.dataframe(df_observers, use_container_width=True, hide_index=True)
            st.write(
                f"#### Observadors/es a {year_seleccionado}:&nbsp;&nbsp;&nbsp;&nbsp; {len(df_observers_year)}"
            )
            st.data_editor(
                df_observers_year[
                    ["user_url", "observation_count", "species_count"]
                ].sort_values(by="observation_count", ascending=False),
                column_config={
                    "user_url": st.column_config.LinkColumn(
                        "user_name",
                        display_text=r"https://minka-sdg.org/users/(.*?)$",
                        width="medium",
                    ),
                    "observation_count": st.column_config.NumberColumn(),
                    "species_count": st.column_config.NumberColumn(),
                },
                hide_index=True,
            )
        else:
            st.info("Fes clic en un any per veure el llistat d'observadors/es")

    st.divider()

# mapa
with st.container():
    st.markdown("## Map d'observacións a Gavà")
    # Definir el centro del mapa
    gava_center = [41.2890, 2.14]

    # Guardar el mapa en session_state para evitar que desaparezca

    if "markermap_gava" not in st.session_state:
        st.session_state.markermap_gava = create_markercluster(st.session_state.df_obs)

    map_html = st.session_state.markermap_gava._repr_html_()
    components.html(map_html, height=600)
