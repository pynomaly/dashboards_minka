import os

import config
import streamlit as st

# Set page config FIRST, before any other st commands or local imports
try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title=f"Dashboard {config.PROJ_NAME}",
)

# Now import the rest
import datetime

import numpy as np
import pandas as pd
import requests
from i18n import create_footer, init_i18n, t
from streamlit_extras.metric_cards import style_metric_cards

st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 300px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 300px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize i18n
init_i18n(current_page="species")

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

# grupos_especies - now defined within species_groups structure


@st.cache_data(ttl=3600, show_spinner=False)
def load_csv(file_path):
    """Load CSV with caching and error handling"""
    try:
        return pd.read_csv(file_path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner="Processant dades d'espècies...")
def load_all_species_data(directory_path, main_project_id):
    """Load all required species data with caching"""
    data = {}

    # Load species groups
    grupos_especies = ["exoticas", "protegidas"]
    for grupo in grupos_especies:
        data[f"species_{grupo}"] = load_csv(
            f"{directory_path}/data/species/{grupo}.csv"
        )

    # Load main project observations
    data["main_obs"] = load_csv(f"{directory_path}/data/{main_project_id}_df_obs.csv")

    # Load province observations
    for prov_id in config.PROJECTS_BY_NAME.values():
        if prov_id != config.MAIN_PROJ:
            data[f"obs_{prov_id}"] = load_csv(
                f"{directory_path}/data/{prov_id}_df_obs.csv"
            )

    return data


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


# Legacy function - replaced by optimized version
def get_obs_by_species_group(df_obs, grupo):
    """Legacy function - use get_obs_by_species_group_optimized instead"""
    df_grupo = load_csv(f"{directory}/data/species/{grupo}.csv")
    return get_obs_by_species_group_optimized(df_obs, df_grupo)


@st.cache_data(ttl=1800, show_spinner="Analitzant espècies...")
def get_species_table(df_obs, df_especies):
    """
    Optimized version: process species data with vectorized operations
    """
    if df_obs.empty or df_especies.empty:
        return pd.DataFrame(), 0

    # Convert datetime once
    df_obs = df_obs.copy()
    df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])

    # Filter species observations using vectorized operations
    species_ids = set(df_especies.taxon_id.tolist())
    obs_result = df_obs[df_obs.taxon_id.isin(species_ids)].copy()

    if obs_result.empty:
        return pd.DataFrame(), 0

    # Calculate last month species count efficiently
    end_date = datetime.datetime.now() - datetime.timedelta(days=30)
    last_month_species = obs_result[obs_result["observed_on"] < end_date][
        "taxon_name"
    ].nunique()

    # Optimized aggregation using groupby
    species_stats = (
        obs_result.groupby("taxon_name")["observed_on"]
        .agg([("count", "size"), ("first_observed", "min"), ("last_observed", "max")])
        .reset_index()
    )

    # Sort by count descending
    species_stats = species_stats.sort_values("count", ascending=False)

    # Add taxon URLs efficiently
    species_stats["taxon_url"] = species_stats["taxon_name"].apply(
        lambda x: f"{config.HOME_PATH}/taxa/{x}"
    )

    return species_stats, last_month_species


@st.cache_data(ttl=7200, show_spinner=False)
def get_photo_url(obs_id):
    """Get photo URL with caching and better error handling"""
    try:
        with requests.Session() as session:
            response = session.get(
                f"{config.API_PATH}/observations?id={obs_id}", timeout=10
            )
            response.raise_for_status()
            results = response.json()["results"]

            if results and results[0].get("photos"):
                photo_url = results[0]["photos"][0]["url"].replace(
                    "/square.", "/large."
                )
                return photo_url
    except Exception as e:
        # Silent fail for missing photos
        pass
    return None


@st.cache_data(ttl=1800)
def get_obs_by_species_group_optimized(df_obs, species_df):
    """Optimized version with better performance"""
    if df_obs.empty or species_df.empty:
        return pd.DataFrame()

    species_ids = set(species_df.taxon_id.tolist())
    filtered_obs = df_obs[df_obs.taxon_id.isin(species_ids)].copy()

    if not filtered_obs.empty:
        filtered_obs["observed_on"] = pd.to_datetime(filtered_obs["observed_on"])
        return filtered_obs.sort_values(by="observed_on", ascending=False)

    return pd.DataFrame()


def show_last_species(df):
    """
    Optimized display of last species with better error handling
    """
    if df.empty:
        st.info(t("species_page.no_photos"))
        return

    try:
        df = df.reset_index(drop=True)
        cols = st.columns(min(5, len(df)), gap="small")

        for i, col in enumerate(cols):
            if i >= len(df):
                break

            with col:
                photo_url = df.loc[i, "photo_url"]
                taxon_name = df.loc[i, "taxon_name"]
                obs_id = df.loc[i, "id"]
                user_login = df.loc[i, "user_login"]

                st.markdown(f":link: [MINKA]({config.HOME_PATH}/observations/{obs_id})")

                if photo_url:
                    st.image(
                        photo_url,
                        caption=f"{taxon_name} | Foto: {user_login}",
                        use_container_width=True,
                    )
                else:
                    st.info(f"Sense foto\n{taxon_name}")

    except Exception as e:
        st.error(f"Error mostrant fotos: {e}")


with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":orange[{t('header.species_title')}]")

# Load all data once with caching
with st.spinner(t("ui.loading_species_data")):
    all_data = load_all_species_data(directory, config.MAIN_PROJ)

# Define species groups and names
species_groups = [
    {
        "key": "exoticas",
        "name": t("species_page.exotic"),
        "title": f"**{t('species_page.exotic_species')}**",
    },
    {
        "key": "protegidas",
        "name": t("species_page.protected"),
        "title": f"**{t('species_page.protected_species')}**",
    },
]

counter = 0
for tab, group_info in zip(
    st.tabs([group["title"] for group in species_groups]), species_groups
):
    with tab:
        # Use preloaded data
        group_key = group_info["key"]
        group_name = group_info["name"]

        df_especies = all_data.get(f"species_{group_key}", pd.DataFrame())
        df_main_project = all_data.get("main_obs", pd.DataFrame())

        try:
            table_species, last_month_species = get_species_table(
                df_main_project, df_especies
            )
        except Exception as e:
            st.markdown("Cap espècie registrada aquest any")
            table_species = pd.DataFrame()
            last_month_species = 0

        col1, col2, col3 = st.columns([10, 1, 10])
        with col1:
            try:
                if isinstance(table_species, pd.DataFrame) and not table_species.empty:
                    # Use the group name from our data structure
                    st.metric(
                        f":ladybug: {t('species_page.num_species')} {group_name}",
                        len(table_species),
                        f"+{len(table_species) - last_month_species} {t('metrics.last_month')}",
                    )
                    style_metric_cards(
                        background_color="#fff",
                        # border_left_color="#C2C2C2",
                        border_left_color=config.COLORS[1],
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
                                t("species_page.species_name_col"),
                                display_text=r"https://minka-sdg.org/taxa/(.*?)$",
                            ),
                            "count": st.column_config.NumberColumn(
                                t("species_page.observations_count_col")
                            ),
                            "first_observed": st.column_config.DateColumn(
                                t("species_page.first_observation_col"),
                                format="DD-MM-YYYY",
                            ),
                            "last_observed": st.column_config.DateColumn(
                                t("species_page.last_observation_col"),
                                format="DD-MM-YYYY",
                            ),
                        },
                        hide_index=False,
                        height=340,
                    )

            except NameError:
                pass

        with col3:
            st.subheader(t("species_page.observations_by_province"))
            project_name = st.selectbox(
                t("provinces.filter_label"),
                config.PROJECTS_BY_NAME.keys(),
                key=f"provincia_{counter}",
            )
            counter += 1
            proj_id = config.PROJECTS_BY_NAME.get(project_name)

            # Use preloaded provincial data (use main_obs for Catalunya/main project)
            if proj_id == config.MAIN_PROJ:
                df_obs = all_data.get("main_obs", pd.DataFrame())
            else:
                df_obs = all_data.get(f"obs_{proj_id}", pd.DataFrame())
            try:
                last_obs = get_obs_by_species_group_optimized(df_obs, df_especies)
            except Exception as e:
                last_obs = pd.DataFrame()

            if len(last_obs) > 0:
                last_obs_formatted = last_obs[
                    ["observed_on", "user_login", "taxon_name", "id"]
                ].reset_index(drop=True)
                last_obs_formatted.index = np.arange(1, len(last_obs_formatted) + 1)
                last_obs_formatted["id"] = last_obs_formatted["id"].astype(str)
                last_obs_formatted["url"] = last_obs_formatted["id"].apply(
                    lambda x: f"{config.HOME_PATH}/observations/{x}"
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

                # bloque tabla
                if len(last_obs_formatted) == 1:
                    height = 40
                elif len(last_obs_formatted) == 2:
                    height = 105
                elif len(last_obs_formatted) == 3:
                    height = 142
                elif len(last_obs_formatted) == 4:
                    height = 180
                elif len(last_obs_formatted) == 5:
                    height = 210
                else:
                    height = 500
                st.dataframe(
                    last_obs_formatted[
                        ["observed_on", "user_login", "taxon_name", "url"]
                    ],
                    column_config={
                        "observed_on": st.column_config.DateColumn(
                            t("table.observation_date"), format="DD-MM-YYYY"
                        ),
                        "user_login": st.column_config.TextColumn(
                            label=t("table.participant"), width="medium"
                        ),
                        "taxon_name": st.column_config.TextColumn(
                            label=t("table.species_name"), width="medium"
                        ),
                        "url": st.column_config.LinkColumn(
                            t("table.link"),
                            width="medium",
                            # display_text=r"https://minka-sdg.org/observations/(.*?)",
                        ),
                    },
                    hide_index=True,
                    height=height,
                )

            else:
                st.markdown(t("species_page.no_observations"))

        st.divider()
        st.subheader(t("species_page.last_species_photos"))

        # Use main project data for photos to get the latest species across all provinces
        main_last_obs = get_obs_by_species_group_optimized(df_main_project, df_especies)

        if len(main_last_obs) > 0:
            # Get unique species (latest observation per species)
            last_obs_species = main_last_obs.drop_duplicates(
                subset=["taxon_id"], keep="first"
            ).reset_index(drop=True)

            last_five_obs_species = last_obs_species.head(5).copy()

            # Load photos with progress indicator
            if not last_five_obs_species.empty:
                with st.spinner("🖼️ Carregant fotos..."):
                    # Use cached photo loading
                    last_five_obs_species.loc[:, "photo_url"] = last_five_obs_species[
                        "id"
                    ].apply(get_photo_url)

                show_last_species(last_five_obs_species)
        else:
            st.markdown("Cap foto per mostrar.")

st.container(height=50, border=False)

# Footer with logos
create_footer()
