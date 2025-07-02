import os

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import folium_static
from utils import (
    create_heatmap,
    create_markercluster,
    get_marine_terrestrial,
    get_number_species,
    get_photo_from_ob,
)

# variables
colors = ["#009DE0", "#0081B8", "#00567A"]

try:
    directory = f"{os.environ['DASHBOARDS']}/biodiverciutat_25"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard BioDiverCiutat 2025",
)

base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"

main_project = 233

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
        st.image(f"{directory}/images/LOGO OFICIAL_biodiverciutat_marca_rgbpositiu.png")
    with col2:
        st.header(":green[BioDiverCiutat 2025]")
        st.markdown(":green[25 - 28 d'abril de 2025]")

# Cargamos observaciones del proyecto principal
st.markdown("### Observacions per rang taxonòmic amb grau investigació")
try:
    df_obs = pd.read_csv(f"{directory}/data/{main_project}_obs.csv")
    df_photos = pd.read_csv(f"{directory}/data/{main_project}_photos.csv")
except:
    df_obs = pd.DataFrame()

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
st.divider()

# últimas especies incorporadas
if len(df_obs) > 0:
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
            get_photo_from_ob(df_photos, ids_obs[0])
        with c2:
            get_photo_from_ob(df_photos, ids_obs[1])
        with c3:
            get_photo_from_ob(df_photos, ids_obs[2])


st.divider()

# Especies marinas / especies terrestres
col1, col2 = st.columns(2)
with col1:
    st.markdown("##### Espècies marines amb grau investigació")
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
                # width=450,
            )
        except AttributeError:
            pass
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

st.divider()
