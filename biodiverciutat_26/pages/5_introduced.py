import os

import config
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from markdownlit import mdlit
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    create_heatmap,
    create_markercluster,
    get_introduced_df,
    get_introduced_species,
)

try:
    directory = f"{os.environ['DASHBOARDS']}/{config.DIRECTORY}"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title=f"Dashboard {config.PROJ_NAME}",
)

from i18n import init_i18n, t

# Initialize i18n
init_i18n(current_page="introduced")


@st.cache_data(ttl=300, show_spinner=False)
def get_cached_introduced_species(proj_id):
    """Cache API call for introduced species count"""
    return get_introduced_species(proj_id)


@st.cache_data(ttl=300, show_spinner=False)
def get_cached_introduced_df(proj_id):
    """Cache introduced observations dataframes"""
    return get_introduced_df(proj_id)


@st.cache_data(ttl=300, show_spinner=False)
def get_cached_species_maps(_df_obs, species_name):
    """Cache map HTML for each introduced species"""
    df = _df_obs[_df_obs.taxon_name == species_name].copy()
    heatmap = create_heatmap(df, zoom=9, center=[41.36174441599461, 2.108076037807884])
    markermap = create_markercluster(
        df, zoom=9, center=[41.36174441599461, 2.108076037807884]
    )
    return heatmap._repr_html_(), markermap._repr_html_(), len(df)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_image(url):
    """Cache image fetching (1 hour TTL)"""
    try:
        response = requests.get(url)
        return response.content if response.ok else None
    except Exception:
        return None


# Sidebar con descripción
st.sidebar.markdown("---")
st.sidebar.markdown(t("introduced_page.description"))

# Cabecera
with st.container():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[{t('header.introduced_title')} - {config.PROJ_NAME}]")
        st.markdown(f":green[{config.PROJ_DATES}]")

# Especies introducidas
st.markdown(f"### {t('introduced_page.title')}")

obs_path = f"{directory}/data/{config.MAIN_PROJ}_obs.csv"
if not os.path.exists(obs_path):
    st.warning(t("ui.no_data"))
    introduced_species = 0
    df_obs = pd.DataFrame()
else:
    introduced_species = get_cached_introduced_species(config.MAIN_PROJ)
    df_obs, df_photos = get_cached_introduced_df(config.MAIN_PROJ)

if len(df_obs) > 0:
    # Tarjeta número total
    with st.container():
        col1, col2 = st.columns([3, 10])
        with col1:
            st.metric(
                t("introduced_page.num_species"),
                introduced_species,
            )
            style_metric_cards(
                background_color="#fff",
                border_left_color="#C2C2C2",
                box_shadow=False,
            )

        with col2:
            df_sorted = df_obs.sort_values(by="observed_on").reset_index(drop=True)

            first_observed = df_sorted.drop_duplicates(
                subset=["taxon_name"], keep="first"
            )[["taxon_name", "observed_on", "id"]].sort_values(
                by=["observed_on"], ascending=False
            )

            first_observed["link"] = (
                f"{config.HOME_PATH}/observations/"
                + first_observed["id"].astype(int).astype(str)
            )
            first_observed.drop(columns="id", inplace=True)

            st.markdown(f"**{t('introduced_page.first_observation_date')}**")
            st.dataframe(
                first_observed,
                column_config={
                    "taxon_name": st.column_config.TextColumn(
                        t("introduced_page.species_name"), width="medium"
                    ),
                    "observed_on": st.column_config.DateColumn(
                        t("introduced_page.first_observation"), format="DD-MM-YYYY"
                    ),
                    "link": st.column_config.LinkColumn(
                        t("introduced_page.link_observation"),
                    ),
                },
                hide_index=True,
                height=340,
            )

    st.divider()

    valores = sorted(df_obs.taxon_name.unique())

    st.markdown(f"## {t('introduced_page.geographic_distribution')}")

    option = st.selectbox(label="label", options=valores, label_visibility="collapsed")

    with st.container():
        map_html1, map_html2, obs_count = get_cached_species_maps(df_obs, option)
        st.markdown(f"**{t('introduced_page.observations_registered')}:** {obs_count}")

        map1, map2 = st.columns(2)
        with map1:
            components.html(map_html1, height=500)
        with map2:
            components.html(map_html2, height=500)
    st.divider()

    # Visor de especies introducidas
    st.markdown(f"## {t('introduced_page.species_viewer')}")
    df_species_photos = df_photos.drop_duplicates(
        subset=["taxon_name"], keep="last"
    ).reset_index(drop=True)

    with st.container():
        cols = st.columns(4)
        col_idx = 0
        for _, row in df_species_photos.iterrows():
            image_url = row["photos_medium_url"]
            id_obs = row["id"]

            image_content = fetch_image(image_url)
            if image_content is None:
                continue

            with cols[col_idx]:
                st.image(image_content)
                mdlit(f"@({config.HOME_PATH}/observations/{id_obs})")

            col_idx = (col_idx + 1) % 4

    st.divider()

else:
    st.markdown(t("introduced_page.no_introduced"))

# Footer con fondo de color
image_footer = f"{directory}/images/footer.png"

st.markdown(
    f"""
    <div style="background-color: {config.COLORS[1]}; padding: 10px; margin-top: 10px; border-radius: 10px;">
        <img src="data:image/png;base64,{__import__('base64').b64encode(open(image_footer, 'rb').read()).decode()}"
             style="width: 100%; display: block;">
    </div>
    """,
    unsafe_allow_html=True,
)
