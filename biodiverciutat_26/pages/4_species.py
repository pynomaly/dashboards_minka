import os

import config
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

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

import streamlit.components.v1 as components
from i18n import init_i18n, t
from utils import (
    create_heatmap,
    create_markercluster,
    get_marine_terrestrial,
    get_number_species,
    get_photo_from_ob,
)

# Initialize i18n
init_i18n(current_page="species")

session = requests.Session()


@st.cache_data(ttl=300, show_spinner=False)
def load_observations(path):
    """Cache observations CSV"""
    return pd.read_csv(path)


@st.cache_data(ttl=300, show_spinner=False)
def load_photos(path):
    """Cache photos CSV"""
    return pd.read_csv(path)


@st.cache_data(ttl=3600, show_spinner=False)
def load_taxon_tree(url):
    """Cache remote taxon tree CSV (1 hour TTL - rarely changes)"""
    return pd.read_csv(url)


@st.cache_data(ttl=300, show_spinner=False)
def get_cached_species_maps(_df_obs, species_name):
    """Cache map HTML for each species"""
    df = _df_obs[_df_obs.taxon_name == species_name].copy()
    heatmap = create_heatmap(df, zoom=9, center=[41.36174441599461, 2.108076037807884])
    markermap = create_markercluster(
        df, zoom=9, center=[41.36174441599461, 2.108076037807884]
    )
    return heatmap._repr_html_(), markermap._repr_html_(), len(df)

# Cabecera
with st.container():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[{t('header.species_title')} - {config.PROJ_NAME}]")
        st.markdown(f":green[{config.PROJ_DATES}]")

# Cargamos observaciones del proyecto principal
st.markdown(f"### {t('species_page.by_taxonomic_rank')}")
obs_path = f"{directory}/data/{config.MAIN_PROJ}_obs.csv"
photos_path = f"{directory}/data/{config.MAIN_PROJ}_photos.csv"
if not os.path.exists(obs_path) or not os.path.exists(photos_path):
    st.warning(t("ui.no_data"))
    df_obs = pd.DataFrame()
    df_photos = pd.DataFrame()
else:
    df_obs = load_observations(obs_path)
    df_photos = load_photos(photos_path)

try:
    # sunburst: número de especies observadas por rango taxonómico
    df_research = df_obs[df_obs.quality_grade == "research"].reset_index(drop=True)
    if len(df_research) == 0:
        st.markdown(t("species_page.no_research_obs"))
    else:
        # preparación de los rangos taxonómicos vacíos
        df_research.loc[df_research["class"].isnull(), "class"] = df_research["phylum"]
        df_research.loc[df_research["order"].isnull(), "order"] = df_research["class"]
        df_research.loc[df_research["family"].isnull(), "family"] = df_research["order"]
        df_research.loc[df_research["taxon_rank"] == "genus", "genus"] = df_research[
            "taxon_name"
        ]

        # df de taxonomías agrupadas con ["name", "parent", "number"]
        df_total = get_number_species(df_research)
        rank_order = ["Life", "Kingdom", "Phylum", "Class", "Order", "Family", "Genus"]
        df_total = df_total[df_total["rank"].isin(rank_order)]

        df_total.drop_duplicates(subset="name", keep="first", inplace=True)

        life_row = pd.DataFrame(
            [{"name": "Life", "number": len(df_research), "parent": ""}]
        )
        df_total2 = pd.concat([life_row, df_total]).reset_index(drop=True)

        st.markdown(f"{t('species_page.click_to_expand')} :point_down:")
        fig_sunburst = px.sunburst(
            df_total,
            names="name",
            parents="parent",
            values="number",
            branchvalues="total",
            color_discrete_sequence=[
                "#4aae79",
                "#f0c579",
                "#ec9e7b",
                "#426a5a",
                "#007d8a",
            ],
        )

        fig_sunburst.update_layout(width=800, height=800)

        st.plotly_chart(fig_sunburst, use_container_width=True)
except AttributeError:
    st.markdown(t("species_page.no_research_obs"))

# últimas especies incorporadas
if len(df_obs) > 0:
    st.divider()
    col1, col2 = st.columns([5, 14], gap="large")
    with col1:
        df_sorted = df_obs.sort_values(by="observed_on").reset_index(drop=True)
        first_observed = df_sorted.drop_duplicates(subset=["taxon_name"], keep="first")[
            ["id", "taxon_name", "observed_on"]
        ].sort_values(by=["observed_on"], ascending=False)

        st.markdown(f"##### {t('species_page.first_observation_date')}")
        st.dataframe(
            first_observed[["taxon_name", "observed_on"]],
            column_config={
                "taxon_name": st.column_config.TextColumn(
                    t("species_page.species_name"), width="medium"
                ),
                "observed_on": st.column_config.DateColumn(
                    t("species_page.first_observation"), format="DD-MM-YYYY"
                ),
            },
            hide_index=True,
            height=280,
        )
    with col2:
        ids_obs = first_observed["id"].to_list()[:3]
        st.markdown(f"##### {t('species_page.last_species_added')}")
        c1, c2, c3 = st.columns(3)
        with c1:
            get_photo_from_ob(df_photos, ids_obs[0], session=session)
        with c2:
            get_photo_from_ob(df_photos, ids_obs[1], session=session)
        with c3:
            get_photo_from_ob(df_photos, ids_obs[2], session=session)

# Especies marinas / especies terrestres
st.markdown(f"### {t('species_page.marine_terrestrial')}")
if len(df_obs) > 0:
    df_obs["taxon_id"] = df_obs["taxon_id"].replace("nan", None)
    df_filtered = df_obs[
        (df_obs["taxon_id"].notnull()) & (df_obs.quality_grade == "research")
    ].copy()
    df_filtered["taxon_id"] = df_filtered["taxon_id"].astype(int)
    taxon_url = "https://raw.githubusercontent.com/eosc-cos4cloud/mecoda-orange/master/mecoda_orange/data/taxon_tree_with_marines.csv"
    taxon_tree = load_taxon_tree(taxon_url)

    df_filtered = pd.merge(
        df_filtered, taxon_tree[["taxon_id", "marine"]], on="taxon_id", how="left"
    )
    marine_species, terrestrial_species = get_marine_terrestrial(df_filtered)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"##### {t('species_page.marine_species')}")
        st.markdown(f"* **{t('species_page.num_species')}:** {len(marine_species)}")
        st.markdown(
            f"* **{t('species_page.num_observations')}:** {len(df_filtered[df_filtered.marine == True])}"
        )
        if len(marine_species) > 0:
            try:
                st.data_editor(
                    marine_species,
                    disabled=True,
                    column_config={
                        "taxa_url": st.column_config.LinkColumn(
                            t("species_page.taxon_link"),
                            display_text=t("species_page.see_species"),
                            width="medium",
                        ),
                        "taxon_name": st.column_config.TextColumn(
                            t("species_page.name"), width="medium"
                        ),
                        "count": st.column_config.NumberColumn(
                            t("metrics.observations")
                        ),
                    },
                    hide_index=True,
                    width=450,
                )
            except AttributeError:
                pass
    with col2:
        st.markdown(f"##### {t('species_page.terrestrial_species')}")
        if len(terrestrial_species) > 0:
            st.markdown(
                f"* **{t('species_page.num_species')}:** {len(terrestrial_species)}"
            )
            st.markdown(
                f"* **{t('species_page.num_observations')}:** {len(df_filtered[df_filtered.marine == False])}"
            )
            try:
                st.data_editor(
                    terrestrial_species,
                    disabled=True,
                    column_config={
                        "taxa_url": st.column_config.LinkColumn(
                            t("species_page.taxon_link"),
                            display_text=t("species_page.see_species"),
                            width="medium",
                        ),
                        "taxon_name": st.column_config.TextColumn(
                            t("species_page.name"), width="medium"
                        ),
                        "count": st.column_config.NumberColumn(
                            t("metrics.observations")
                        ),
                    },
                    hide_index=True,
                )
            except AttributeError:
                pass
else:
    st.warning(t("ui.no_data"))

st.divider()

# Mapas de presencia de cada especie
st.header(t("species_page.geographic_distribution"))
if len(df_obs) > 0:
    valores = sorted(df_obs[df_obs.taxon_name.notnull()].taxon_name.unique())

    option = st.selectbox(label="label", options=valores, label_visibility="collapsed")

    with st.container():
        map_html1, map_html2, obs_count = get_cached_species_maps(df_obs, option)
        st.markdown(f"**{t('species_page.observations_registered')}:** {obs_count}")

        map1, map2 = st.columns(2)
        with map1:
            components.html(map_html1, height=600)
        with map2:
            components.html(map_html2, height=600)
else:
    st.warning(t("ui.no_data"))
