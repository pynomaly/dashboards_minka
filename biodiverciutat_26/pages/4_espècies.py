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
from utils import (
    create_heatmap,
    create_markercluster,
    get_marine_terrestrial,
    get_number_species,
    get_photo_from_ob,
)

# variables
session = requests.Session()

# Columna izquierda
st.sidebar.markdown("# Quines espècies busca el BioDiverCiutat?")
st.sidebar.markdown(
    """
La idea del CNC és que totes les ciutats que se sumin al repte identifiquin qualsevol taxó d’ésser viu del seu entorn metropolità. En el cas de Barcelona, l’objectiu és registrar observacions d’espècies tant marines, costaneres com terrestres, ja que Barcelona inclou diverses àrees amb biodiversitat (platges, zones verdes, parcs i jardins, boscos de Collserola).
"""
)
# Cabecera
with st.container():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image(f"{directory}/images/{config.PROJ_LOGO}")
    with col2:
        st.header(f":green[{config.PROJ_NAME}]")
        st.markdown(f":green[{config.PROJ_DATES}]")

# Cargamos observaciones del proyecto principal
st.markdown("### Observacions per rang taxonòmic amb grau investigació")
obs_path = f"{directory}/data/{config.MAIN_PROJ}_obs.csv"
photos_path = f"{directory}/data/{config.MAIN_PROJ}_photos.csv"
if not os.path.exists(obs_path) or not os.path.exists(photos_path):
    st.warning("Cap dada disponible")
    df_obs = pd.DataFrame()
    df_photos = pd.DataFrame()
else:
    df_obs = pd.read_csv(obs_path)
    df_photos = pd.read_csv(photos_path)

try:
    # sunburst: número de especies observadas por rango taxonómico
    df_research = df_obs[df_obs.quality_grade == "research"].reset_index(drop=True)
    if len(df_research) == 0:
        st.markdown("Cap observació amb grau investigació encara")
    else:
        # preparación de los rangos taxonómicos vacíos
        df_research.loc[df_research["class"].isnull(), "class"] = df_research["phylum"]
        df_research.loc[df_research["order"].isnull(), "order"] = df_research["class"]
        df_research.loc[df_research["family"].isnull(), "family"] = df_research["order"]
        df_research.loc[df_research["taxon_rank"] == "genus", "genus"] = df_research[
            "taxon_name"
        ]

        # df de taxonomías agrupdas con ["name", "parent", "number"]
        df_total = get_number_species(df_research)
        rank_order = ["Life", "Kingdom", "Phylum", "Class", "Order", "Family", "Genus"]
        df_total = df_total[df_total["rank"].isin(rank_order)]

        df_total.drop_duplicates(subset="name", keep="first", inplace=True)

        life_row = pd.DataFrame(
            [{"name": "Life", "number": len(df_research), "parent": ""}]
        )
        df_total2 = pd.concat([life_row, df_total]).reset_index(drop=True)

        st.markdown(
            "Fes clic en un rang taxonòmic per veure'n el desglossament :point_down:"
        )
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
    st.markdown("Cap observació amb grau investigació encara")

# últimas especies incorporadas
if len(df_obs) > 0:
    st.divider()
    col1, col2 = st.columns([5, 14], gap="large")
    with col1:
        # Últimes espècies registrades
        df_sorted = df_obs.sort_values(by="observed_on").reset_index(drop=True)
        first_observed = df_sorted.drop_duplicates(subset=["taxon_name"], keep="first")[
            ["id", "taxon_name", "observed_on"]
        ].sort_values(by=["observed_on"], ascending=False)

        st.markdown("##### Data de la primera observació")
        st.dataframe(
            first_observed[["taxon_name", "observed_on"]],
            column_config={
                "taxon_name": st.column_config.TextColumn(
                    "nom de l'espècie", width="medium"
                ),
                "observed_on": st.column_config.DateColumn(
                    "primera observació", format="DD-MM-YYYY"
                ),
            },
            hide_index=True,
            height=280,
        )
    with col2:
        # Extraemos una foto de cada una de las últimas especies
        ids_obs = first_observed["id"].to_list()[:3]
        st.markdown("##### Últimes espècies incorporades")
        c1, c2, c3 = st.columns(3)
        with c1:
            get_photo_from_ob(df_photos, ids_obs[0], session=session)
        with c2:
            get_photo_from_ob(df_photos, ids_obs[1], session=session)
        with c3:
            get_photo_from_ob(df_photos, ids_obs[2], session=session)

# Especies marinas / especies terrestres
st.markdown("### Espècies marines i terrestres")
if len(df_obs) > 0:
    df_obs["taxon_id"] = df_obs["taxon_id"].replace("nan", None)
    df_filtered = df_obs[
        (df_obs["taxon_id"].notnull()) & (df_obs.quality_grade == "research")
    ].copy()
    df_filtered["taxon_id"] = df_filtered["taxon_id"].astype(int)
    # Sacar columna marino
    taxon_url = "https://raw.githubusercontent.com/eosc-cos4cloud/mecoda-orange/master/mecoda_orange/data/taxon_tree_with_marines.csv"
    taxon_tree = pd.read_csv(taxon_url)

    df_filtered = pd.merge(
        df_filtered, taxon_tree[["taxon_id", "marine"]], on="taxon_id", how="left"
    )
    marine_species, terrestrial_species = get_marine_terrestrial(df_filtered)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Espècies marines amb grau investigació")
        st.markdown(f"* **Nombre d'espècies:** {len(marine_species)}")
        st.markdown(
            f"* **Nombre d'observacions:** {len(df_filtered[df_filtered.marine == True])}"
        )
        if len(marine_species) > 0:
            try:
                st.data_editor(
                    marine_species,
                    disabled=True,
                    column_config={
                        "taxa_url": st.column_config.LinkColumn(
                            "Tàxon link", display_text="Veure espècie", width="medium"
                        ),
                        "taxon_name": st.column_config.TextColumn(
                            "Nom", width="medium"
                        ),
                        "count": st.column_config.NumberColumn("Observacions"),
                    },
                    hide_index=True,
                    width=450,
                )
            except AttributeError:
                pass
    with col2:
        st.markdown("##### Espècies terrestres amb grau investigació")
        if len(terrestrial_species) > 0:
            st.markdown(f"* **Nombre d'espècies:** {len(terrestrial_species)}")
            st.markdown(
                f"* **Nombre d'observacions:** {len(df_filtered[df_filtered.marine == False])}"
            )
            try:
                st.data_editor(
                    terrestrial_species,
                    disabled=True,
                    column_config={
                        "taxa_url": st.column_config.LinkColumn(
                            "Tàxon link", display_text="Veure espècie", width="medium"
                        ),
                        "taxon_name": st.column_config.TextColumn("Nom", width="medium"),
                        "count": st.column_config.NumberColumn("Observacions"),
                    },
                    hide_index=True,
                )
            except AttributeError:
                pass
else:
    st.warning("Cap dada disponible")

st.divider()

# Mapas de presencia de cada especie, con selector desplegable
st.header("Distribució geogràfica de cada espècie")
if len(df_obs) > 0:
    valores = sorted(df_obs[df_obs.taxon_name.notnull()].taxon_name.unique())

    option = st.selectbox(label="label", options=valores, label_visibility="collapsed")

    with st.container():
        df = df_obs[df_obs.taxon_name == option].copy()
        st.markdown(f"**Nombre d'observacions registrades:** {len(df)}")
        map1, map2 = st.columns(2)
        with map1:
            st.session_state.st_heatmap = create_heatmap(
                df, zoom=9, center=[41.36174441599461, 2.108076037807884]
            )
            map_html1 = st.session_state.st_heatmap._repr_html_()
            components.html(map_html1, height=600)

        with map2:
            st.session_state.st_clustermap = create_markercluster(
                df, zoom=9, center=[41.36174441599461, 2.108076037807884]
            )
            map_html2 = st.session_state.st_clustermap._repr_html_()
            components.html(map_html2, height=600)
else:
    st.warning("Cap dada disponible")
