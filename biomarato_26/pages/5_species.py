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
    data["species_exotic"] = load_csv(
        f"{directory_path}/data/species/species_exotic.csv"
    )
    data["species_protected"] = load_csv(
        f"{directory_path}/data/species/species_protected.csv"
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


@st.cache_data(ttl=1800, show_spinner="Analitzant espècies...")
def get_species_table_with_regulation(df_obs, df_especies):
    """
    Process species data including regulation column
    """
    if df_obs.empty or df_especies.empty:
        return pd.DataFrame(), 0

    df_obs = df_obs.copy()
    df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])

    species_ids = set(df_especies.taxon_id.dropna().tolist())
    obs_result = df_obs[df_obs.taxon_id.isin(species_ids)].copy()

    if obs_result.empty:
        return pd.DataFrame(), 0

    end_date = datetime.datetime.now() - datetime.timedelta(days=30)
    last_month_species = obs_result[obs_result["observed_on"] < end_date][
        "taxon_name"
    ].nunique()

    species_stats = (
        obs_result.groupby("taxon_name")["observed_on"]
        .agg([("count", "size"), ("first_observed", "min"), ("last_observed", "max")])
        .reset_index()
    )

    # Merge with species data to get regulation
    species_stats = species_stats.merge(
        df_especies[["taxon_name", "regulation"]].drop_duplicates(),
        on="taxon_name",
        how="left",
    )

    species_stats = species_stats.sort_values("count", ascending=False)

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
        total = len(df)

        # Show in rows of 5
        for row_start in range(0, total, 5):
            row_end = min(row_start + 5, total)
            num_cols = row_end - row_start
            cols = st.columns(num_cols, gap="small")

            for i, col in enumerate(cols):
                idx = row_start + i
                with col:
                    photo_url = df.loc[idx, "photo_url"]
                    taxon_name = df.loc[idx, "taxon_name"]
                    obs_id = df.loc[idx, "id"]
                    user_login = df.loc[idx, "user_login"]

                    st.markdown(
                        f":link: [MINKA]({config.HOME_PATH}/observations/{obs_id})"
                    )

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


def display_species_column(df_especies, df_main_project, group_name):
    """Helper function to display species data in a column"""
    try:
        table_species, last_month_species = get_species_table(
            df_main_project, df_especies
        )
    except Exception as e:
        st.markdown("Cap espècie registrada aquest any")
        return

    if isinstance(table_species, pd.DataFrame) and not table_species.empty:
        st.metric(
            f":ladybug: {t('species_page.num_species')} {group_name}",
            len(table_species),
            f"+{len(table_species) - last_month_species} {t('metrics.last_month')}",
        )
        style_metric_cards(
            background_color="#fff",
            border_left_color=config.COLORS[1],
            box_shadow=False,
        )

        table_species.index = np.arange(1, len(table_species) + 1)
        st.dataframe(
            table_species[["taxon_url", "count", "first_observed", "last_observed"]],
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


def display_species_column_with_regulation(df_especies, df_main_project, group_name):
    """Helper function to display species data with regulation column"""
    try:
        table_species, last_month_species = get_species_table_with_regulation(
            df_main_project, df_especies
        )
    except Exception as e:
        st.markdown("Cap espècie registrada aquest any")
        return

    if isinstance(table_species, pd.DataFrame) and not table_species.empty:
        # Metric card at half width
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"### {t('metrics.species')} {group_name}")
            st.metric(
                label=f":ladybug: {t('species_page.num_species')}",
                value=len(table_species),
                delta=f"+{len(table_species) - last_month_species} {t('metrics.last_month')}",
            )
            style_metric_cards(
                background_color="#fff",
                border_left_color=config.COLORS[1],
                box_shadow=False,
            )

        # Table at full width
        table_species.index = np.arange(1, len(table_species) + 1)
        st.dataframe(
            table_species[
                ["taxon_url", "count", "first_observed", "last_observed", "regulation"]
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
                "regulation": st.column_config.TextColumn(
                    t("species_page.regulation_col"),
                    width=400,
                ),
            },
            hide_index=False,
            height=200,
            use_container_width=True,
        )


def display_species_photos(df_main_project, df_especies):
    """Helper function to display species photos"""
    main_last_obs = get_obs_by_species_group_optimized(df_main_project, df_especies)

    if len(main_last_obs) > 0:
        last_obs_species = main_last_obs.drop_duplicates(
            subset=["taxon_id"], keep="first"
        ).reset_index(drop=True)

        last_five_obs_species = last_obs_species.head(10).copy()

        if not last_five_obs_species.empty:
            with st.spinner("Carregant fotos..."):
                last_five_obs_species.loc[:, "photo_url"] = last_five_obs_species[
                    "id"
                ].apply(get_photo_url)

            show_last_species(last_five_obs_species)
    else:
        st.markdown("Cap foto per mostrar.")


# Create tabs
tab_exotic, tab_protected = st.tabs(
    [
        f"**{t('species_page.exotic_species')}**",
        f"**{t('species_page.protected_species')}**",
    ]
)

df_main_project = all_data.get("main_obs", pd.DataFrame())

# Tab: Exotic species
with tab_exotic:
    df_exotic_all = all_data.get("species_exotic", pd.DataFrame())

    # Filter by category
    df_exotica = df_exotic_all[df_exotic_all["categoria"] == "Exòtica"]
    df_exotica_invasora = df_exotic_all[
        df_exotic_all["categoria"] == "Exòtica invasora"
    ]

    col1, col2, col3 = st.columns([10, 1, 10])

    with col1:
        display_species_column(df_exotica, df_main_project, t("species_page.exotic"))

    with col3:
        display_species_column(
            df_exotica_invasora, df_main_project, t("species_page.exotic_invasive")
        )

    st.divider()
    st.subheader(t("species_page.last_species_photos"))
    display_species_photos(df_main_project, df_exotic_all)

# Tab: Protected species
with tab_protected:
    df_protected_all = all_data.get("species_protected", pd.DataFrame())

    # Define protected species categories
    protected_categories = [
        ("En perill d'extinció", "species_page.endangered"),
        ("Vulnerable", "species_page.vulnerable"),
        ("Espècie protegida", "species_page.protected"),
        ("Extinta com a reproductora a Catalunya", "species_page.extinct_breeder"),
        (
            "Espècie amb regulació de l'explotació o del comerç",
            "species_page.trade_regulated",
        ),
        ("Espècie amb protecció de l'hàbitat/ZEC", "species_page.habitat_protected"),
    ]

    # Display each category vertically
    for category, translation_key in protected_categories:
        df_category = df_protected_all[df_protected_all["category"] == category]
        if not df_category.empty:
            display_species_column_with_regulation(
                df_category, df_main_project, t(translation_key)
            )
            st.divider()

    st.subheader(t("species_page.last_species_photos"))
    display_species_photos(df_main_project, df_protected_all)

st.container(height=50, border=False)

# Footer with logos
create_footer()
