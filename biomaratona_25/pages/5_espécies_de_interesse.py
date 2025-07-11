import datetime
import os

import numpy as np
import pandas as pd
import requests
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"


try:
    directory = f"{os.environ['DASHBOARDS']}/biomaratona_25"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard BioMARatona 2025",
)

st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 220px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 220px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# configuración de ModeBar
config_modebar = {
    "displayModeBar": True,  # Mostrar u ocultar la ModeBar
    "modeBarButtonsToRemove": [  # Lista de botones a remover
        "zoom2d",  # Eliminar el botón de zoom
        "pan2d",  # Eliminar el botón de paneo
        "lasso2d",  # Eliminar el botón de lazo
        "autoScale2d",  # Eliminar el botón de autoescalar
        "resetScale2d",  # Eliminar el botón de resetear escala
        "hoverClosestCartesian",  # Eliminar el botón de acercar el hover
        "hoverCompareCartesian",  # Eliminar el botón de comparar en hover
        "zoomIn2d",  # Eliminar el botón de zoom +
        "zoomOut2d",  # Eliminar el botón de zoom -
    ],
    "displaylogo": False,  # Ocultar el logo de Plotly
}

colors = ["#5fbfbb", "#1e9ca3", "#0c6a83", "#de6719", "#fab954"]

projects = {
    424: "BioMARatona 2025",
    452: "BioMARatona 2024",
}

main_project = 424
project_id_2024 = next(
    (k for k, v in projects.items() if v == "BioMARatona 2024"), None
)
project_id_2025 = next(
    (k for k, v in projects.items() if v == "BioMARatona 2025"), None
)


grupos_especies = ["exoticas", "protegidas", "amenazadas"]


@st.cache_data(ttl=3600, show_spinner=False)
def load_csv(file_path):
    return pd.read_csv(file_path)


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


def get_obs_by_species_group(df_obs, grupo):
    df_grupo = load_csv(f"{directory}/data/species/{grupo}.csv")
    species_ids = df_grupo.taxon_id.to_list()
    last_obs = df_obs[df_obs.taxon_id.isin(species_ids)].sort_values(
        by="observed_on", ascending=False
    )
    return last_obs


def get_species_table(df_obs, df_especies):
    """
    A partir de las observaciones y el df de las especies,
    crea df con especie, número de observaciones, primera observación, última observación, enlace al taxon
    """
    df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])
    # Filtramos las especies de ese grupo
    obs_result = df_obs[
        df_obs.taxon_id.isin(df_especies.taxon_id.to_list())
    ].reset_index(drop=True)

    end_date = datetime.datetime.now() - datetime.timedelta(days=30)
    last_month_species = obs_result.loc[
        obs_result["observed_on"] < end_date, "taxon_name"
    ].nunique()

    # tabla de num. observaciones por especie
    table_species = obs_result.taxon_name.value_counts().to_frame().reset_index()
    table_species["first_observed"] = table_species["taxon_name"].apply(
        lambda x: obs_result.loc[obs_result["taxon_name"] == x, "observed_on"].min()
    )
    table_species["last_observed"] = table_species["taxon_name"].apply(
        lambda x: obs_result.loc[obs_result["taxon_name"] == x, "observed_on"].max()
    )
    table_species["taxon_url"] = table_species["taxon_name"].apply(
        lambda x: f"https://minka-sdg.org/taxa/{x}"
    )
    return table_species, last_month_species


def get_photo_url(obs_id, session=None):
    if session is None:
        session = requests.Session()
    results = session.get(f"{api_path}/observations?id={obs_id}").json()["results"]
    try:
        photo_url = results[0]["photos"][0]["url"].replace("/square.", "/large.")
        return photo_url
    except:
        return None


def show_last_species(df):
    """
    Show the last species added to the list.
    """
    try:
        df.reset_index(drop=True, inplace=True)

        col1sp, col2sp, col3sp, col4sp, col5sp = st.columns(5, gap="small")
        i = 0
        for col in [col1sp, col2sp, col3sp, col4sp, col5sp]:
            with col:
                photo_url = df.loc[i, "photo_url"]
                taxon_name = df.loc[i, "taxon_name"]
                st.markdown(
                    f":link: [MINKA](https://minka-sdg.org/observations/{df.loc[i, 'id']})"
                )
                st.image(
                    photo_url,
                    caption=f"{taxon_name} | Foto: {df.loc[i, 'user_login']}",
                )
                i += 1

    except:
        pass


with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Espécies de interesse]")

i = 0
counter = 0
for tab in st.tabs(
    [
        "**Espécies exóticas**",
        "**Espécies protegidas**",
        "**Espécies ameaçadas**",
    ]
):

    with tab:
        # Cálculos generales
        df_especies = load_csv(f"{directory}/data/species/{grupos_especies[i]}.csv")
        df_main_project = load_csv(f"{directory}/data/{main_project}_df_obs.csv")
        try:
            table_species, last_month_species = get_species_table(
                df_main_project, df_especies
            )
        except:
            st.markdown("Nenhuma espécie registada neste ano")

        col1, col2, col3 = st.columns([10, 1, 10])
        with col1:
            try:
                if isinstance(table_species, pd.DataFrame):
                    # Etiqueta para la métrica total
                    if grupos_especies[i] == "exoticas":
                        name = "exoticas"
                    elif grupos_especies[i] == "protegidas":
                        name = "protegidas"
                    st.metric(
                        f":ladybug: Número de espécies {name}",
                        len(table_species),
                        f"+{len(table_species) - last_month_species} mês passado",
                    )
                    style_metric_cards(
                        background_color="#fff",
                        # border_left_color="#C2C2C2",
                        border_left_color=colors[1],
                        box_shadow=False,
                    )

                    # Dataframe para el listado de especies
                    table_species.index = np.arange(1, len(table_species) + 1)
                    st.dataframe(
                        table_species[
                            ["taxon_url", "count", "first_observed", "last_observed"]
                        ],
                        column_config={
                            "taxon_url": st.column_config.LinkColumn(
                                "Nome da espécie",
                                display_text=r"https://minka-sdg.org/taxa/(.*?)$",
                            ),
                            "count": st.column_config.NumberColumn(
                                "Número de observações"
                            ),
                            "first_observed": st.column_config.DateColumn(
                                "Primeira observação", format="DD-MM-YYYY"
                            ),
                            "last_observed": st.column_config.DateColumn(
                                "Última observação", format="DD-MM-YYYY"
                            ),
                        },
                        hide_index=False,
                        height=340,
                    )

            except NameError:
                pass

        with col3:
            st.subheader("Observações por ano")
            project_name = st.selectbox(
                "Filtrar por ano:",
                projects.values(),
                key=f"provincia_{counter}",
            )
            counter += 1
            proj_id = next((k for k, v in projects.items() if v == project_name), None)

            try:
                df_obs = load_csv(f"{directory}/data/{proj_id}_df_obs.csv")
                last_obs = get_obs_by_species_group(df_obs, grupos_especies[i])
            except:
                last_obs = pd.DataFrame()

            if len(last_obs) > 0:
                last_obs_formatted = last_obs[
                    ["observed_on", "user_login", "taxon_name", "id"]
                ].reset_index(drop=True)
                last_obs_formatted.index = np.arange(1, len(last_obs_formatted) + 1)
                last_obs_formatted["id"] = last_obs_formatted["id"].astype(str)
                last_obs_formatted["url"] = last_obs_formatted["id"].apply(
                    lambda x: f"https://minka-sdg.org/observations/{x}"
                )

                # bloque sumario
                sumari = ""
                for idx, row in (
                    last_obs_formatted["taxon_name"]
                    .value_counts()
                    .to_frame()
                    .reset_index()
                    .iterrows()
                ):
                    sumari += f"- {row.taxon_name}: {row['count']}\n"

                st.markdown(sumari)

            else:
                st.markdown("Nenhuma observação registada.")

        st.divider()
        st.subheader(f"Imagens das últimas espécies registadas")
        session = requests.Session()
        print(grupos_especies[i])
        if len(last_obs) > 0:
            # df_especies = get_obs_by_species_group(df_main_project, grupos_especies[i])
            last_obs_species = last_obs.drop_duplicates(
                subset=["taxon_id"], keep="first"
            ).reset_index(drop=True)
            last_five_obs_species = last_obs_species.head(5).copy()
            last_five_obs_species.loc[:, "photo_url"] = last_five_obs_species[
                "id"
            ].apply(get_photo_url, session=session)
            show_last_species(last_five_obs_species)
        else:
            st.markdown("Nenhuma foto a exibir.")

        i += 1

st.container(height=50, border=False)

# Logos
st.divider()
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown("##### Organizadores:")
        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{directory}/images/organizadores_2024_v2.png")

    with col_2:
        st.markdown("##### Com o financiamento de projetos europeus:")
        st.image(f"{directory}/images/logos_financiacion_biomarato_v2.png")
