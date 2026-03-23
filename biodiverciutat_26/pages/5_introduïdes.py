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

# variables
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

# Sidebar
st.sidebar.markdown(
    """
Les espècies introduïdes, també anomenades exòtiques, són organismes que han estat transportats fora del seu rang natural i han establert poblacions en nous entorns. Poden tenir un impacte negatiu en els ecosistemes locals, competint amb les espècies natives per recursos com ara l'alimentació, l'espai i l'aigua. Això pot alterar l'equilibri ecològic i provocar canvis significatius en la biodiversitat i la dinàmica dels ecosistemes. 
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

# Especies introducidas
st.markdown("### Espècies introduïdes")

obs_path = f"{directory}/data/{config.MAIN_PROJ}_obs.csv"
if not os.path.exists(obs_path):
    st.warning("Cap dada disponible")
    introduced_species = 0
    df_obs = pd.DataFrame()
else:
    introduced_species = get_introduced_species(f"{config.MAIN_PROJ}")
    df_obs, df_photos = get_introduced_df(f"{config.MAIN_PROJ}")

if len(df_obs) > 0:
    # Tarjeta número total
    with st.container():
        col1, col2 = st.columns([3, 10])
        with col1:
            st.metric(
                "Nombre d'espècies",
                introduced_species,
            )
            style_metric_cards(
                background_color="#fff",
                border_left_color="#C2C2C2",
                box_shadow=False,
            )

        with col2:
            # Últimes espècies registrades
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

            st.markdown("**Data de la primera observació**")
            st.dataframe(
                first_observed,
                column_config={
                    "taxon_name": st.column_config.TextColumn(
                        "Nom de l'espècie", width="medium"
                    ),
                    "observed_on": st.column_config.DateColumn(
                        "Primera observació", format="DD-MM-YYYY"
                    ),
                    "link": st.column_config.LinkColumn(
                        "Link a observació",
                    ),
                },
                hide_index=True,
                height=340,
            )

    # Mapas de presencia de cada especie
    # con selector desplegable

    st.divider()

    valores = sorted(df_obs.taxon_name.unique())

    st.markdown("## Distribució geogràfica de cada espècie")

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
            components.html(map_html1, height=300)

        with map2:
            st.session_state.st_clustermap = create_markercluster(
                df, zoom=9, center=[41.36174441599461, 2.108076037807884]
            )
            map_html2 = st.session_state.st_clustermap._repr_html_()
            components.html(map_html2, height=300)
    st.divider()

    # Visor de especies introducidas
    st.markdown("## Visor d'espècies introduïdes")
    df_species_photos = df_photos.drop_duplicates(
        subset=["taxon_name"], keep="last"
    ).reset_index(drop=True)

    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        col = 0
        for index, row in df_species_photos.iterrows():
            image = row["photos_medium_url"]
            id_obs = row["id"]
            taxon_name = row.taxon_name
            try:
                response = requests.get(image)
            except:
                continue

            if col == 0:
                with c1:
                    st.image(response.content)
                    mdlit(f"@({config.HOME_PATH}/observations/{id_obs})")
                col += 1
            elif col == 1:
                with c2:
                    st.image(response.content)
                    mdlit(f"@({config.HOME_PATH}/observations/{id_obs})")
                col += 1
            elif col == 2:
                with c3:
                    st.image(response.content)
                    mdlit(f"@({config.HOME_PATH}/observations/{id_obs})")
                col += 1
            elif col == 3:
                with c4:
                    st.image(response.content)
                    mdlit(f"@({config.HOME_PATH}/observations/{id_obs})")
                col = 0

    st.divider()

else:
    st.markdown("Cap espècie introduïda registrada")
