# Run as streamlit run app_biomarato.py --server.port 9003

import os

import pandas as pd
import requests
import streamlit as st
from markdownlit import mdlit
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_folium import folium_static
from utils import (
    create_heatmap,
    create_markercluster,
    fig_area_evolution,
    fig_bars_months,
    fig_provinces,
    get_grouped_monthly,
    get_last_obs,
    get_last_week_metrics,
    get_main_metrics,
    get_metrics_province,
    reindex,
)

try:
    directory = f"{os.environ['DASHBOARDS']}/biomarato_23"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard BioMARató 2023",
)

exclude_users = [
    "xasalva",
    "bertinhaco",
    "andrea",
    "laurabiomar",
    "guillermoalvarez_fecdas",
    "mediambient_ajelprat",
    "fecdas_mediambient",
    "planctondiving",
    "marinagm",
    "CEM",
    "uri_domingo",
    "mimo_fecdas",
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "anellides",
    "irodero",
    "manelsalvador",
    "sara_riera",
]

base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"


projects = [
    {"id": 121, "name": "Girona"},
    {"id": 122, "name": "Tarragona"},
    {"id": 123, "name": "Barcelona"},
    {"id": 124, "name": "Catalunya"},
]


# Cabecera
with st.container():
    col1, col2 = st.columns([1, 14])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Resultats BioMARató 2023]")
        st.markdown(":orange[Apr 28, 2023 - Oct 15, 2023]")

# Error si no responde la API
try:
    total_species, total_participants, total_obs = get_main_metrics(124)
    lw_obs, lw_spe, lw_part = get_last_week_metrics(124)
except:
    st.error("Error loading data")
    st.stop()

# Main metrics (incluye todos los usuarios y todos los grados)
with st.container():
    __, col1, col2, col3, _ = st.columns([2, 1, 1, 1, 2])
    with col1:
        st.metric(
            ":camera_with_flash: Observacions",
            f"{total_obs:,}".replace(",", " "),
            f"+{lw_obs:,} última setmana".replace(",", " "),
        )
    with col2:
        st.metric(
            ":ladybug: Espècies",
            f"{total_species:,}".replace(",", " "),
            f"+{lw_spe} última setmana",
        )
    with col3:
        st.metric(
            ":eyes: Participants",
            f"{total_participants:,}".replace(",", " "),
            f"+{lw_part} última setmana",
        )

    style_metric_cards(
        background_color="#fef7eb",
        border_left_color="#f9b853",
        box_shadow=False,
    )

    # Evolution lines
    main_metrics = pd.read_csv(f"{directory}/data/main_metrics.csv")
    main_metrics.rename(
        columns={
            "date": "data",
            "observations": "observacions",
            "species": "espècies",
        },
        inplace=True,
    )

    grouped = get_grouped_monthly(main_metrics)
    grouped["data"] = grouped["data"].astype(str)

    col1_line, col2_line, col3_line = st.columns(3, gap="large")

    with col1_line:
        fig1 = fig_area_evolution(
            df=main_metrics,
            field="observacions",
            title="Evolució del nombre d'observacions",
            color="#089aa2",
        )

        st.plotly_chart(fig1, use_container_width=True)

    with col2_line:
        fig2 = fig_area_evolution(
            df=main_metrics,
            field="espècies",
            title="Evolució del nombre d'espècies",
            color="#dc6619",
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col3_line:
        fig3 = fig_area_evolution(
            df=main_metrics,
            field="participants",
            title="Evolució del nombre de participants",
            color="#f9b853",
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Resultados mensuales
    col1_month, col2_month, col3_month = st.columns(3, gap="large")
    with col1_month:
        fig1b = fig_bars_months(
            grouped,
            field="observacions",
            title="Nombre d'observacions per mes",
            color="#089aa2",
        )
        st.plotly_chart(fig1b, use_container_width=True)

    with col2_month:
        fig2b = fig_bars_months(
            grouped,
            field="espècies",
            title="Nombre de espècies per mes",
            color="#dc6619",
        )
        st.plotly_chart(fig2b, use_container_width=True)

    with col3_month:
        fig3b = fig_bars_months(
            grouped,
            field="participants",
            title="Nombre de participants per mes",
            color="#f9b853",
        )
        st.plotly_chart(fig3b, use_container_width=True)

st.divider()

# Ranking by province (incluye todos los usuarios y grado research)
with st.container():
    # Cabecera
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Quina província ha estat la més activa?]")
    if "main_metrics_prov" not in st.session_state:
        st.session_state.main_metrics_prov = get_metrics_province()

    # Gráfico de barras
    fig1 = fig_provinces(
        st.session_state.main_metrics_prov, "observacions", "Nombre d’observacions"
    )
    fig2 = fig_provinces(
        st.session_state.main_metrics_prov, "espècies", "Nombre d’espècies diferents"
    )
    fig3 = fig_provinces(
        st.session_state.main_metrics_prov, "participants", "Nombre de participants"
    )

    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, use_container_width=True)
    with col3:
        st.plotly_chart(fig3, use_container_width=True)

    # Trofeos provincia en cabeza
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(
        [2, 1, 4, 2, 1, 4, 2, 1, 4], gap="small"
    )

    prov_sp = (
        st.session_state.main_metrics_prov.sort_values(by="espècies", ascending=False)[
            "provincia"
        ]
        .head(1)
        .values[0]
    )
    prov_obs = (
        st.session_state.main_metrics_prov.sort_values(
            by="observacions", ascending=False
        )["provincia"]
        .head(1)
        .values[0]
    )
    prov_part = (
        st.session_state.main_metrics_prov.sort_values(
            by="participants", ascending=False
        )["provincia"]
        .head(1)
        .values[0]
    )

    with col2:
        st.image(f"{directory}/images/BioMARato_Trofeo_100.png")
    with col3:
        st.subheader(prov_obs)
    with col5:
        st.image(f"{directory}/images/BioMARato_Trofeo_100.png")
    with col6:
        st.subheader(prov_sp)
    with col8:
        st.image(f"{directory}/images/BioMARato_Trofeo_100.png")
    with col9:
        st.subheader(prov_part)

st.divider()

# Ranking users por provincia, excluidos los usuarios voluntarios
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Rànquing de participants]")
    st.markdown("Nombre d'observacions amb grau de recerca.")

    col0, col1, col2, col3 = st.columns(4, gap="large")
    with col0:
        st.subheader("General")
        # Dataframe
        if "pt_users0" not in st.session_state:
            st.session_state.pt_users0 = pd.read_csv(
                f"{directory}/data/124_pt_users.csv"
            )
            st.session_state.pt_users0 = st.session_state.pt_users0[
                -st.session_state.pt_users0.participant.isin(exclude_users)
            ].reset_index(drop=True)
            st.session_state.pt_users0.index = range(
                st.session_state.pt_users0.index.start + 1,
                st.session_state.pt_users0.index.stop + 1,
            )
            st.session_state.pt_users0["observacions"] = st.session_state.pt_users0[
                "observacions"
            ].apply(lambda x: "{:,.0f}".format(x).replace(",", " "))

        st.dataframe(st.session_state.pt_users0, use_container_width=True, height=210)

        # Nombre
        __, col1b, __ = st.columns([1, 10, 1])
        with col1b:
            medals = ["first_place_medal", "second_place_medal", "third_place_medal"]
            for i in range(1, 4):
                nombre = st.session_state.pt_users0.loc[i, "participant"]
                st.subheader(
                    f":{medals[i-1]}: [{nombre}](https://minka-sdg.org/users/{nombre})"
                )

    with col1:
        st.subheader("Girona")

        # Dataframe
        if "pt_users1" not in st.session_state:
            st.session_state.pt_users1 = pd.read_csv(
                f"{directory}/data/121_pt_users.csv"
            )
            st.session_state.pt_users1 = st.session_state.pt_users1[
                -st.session_state.pt_users1.participant.isin(exclude_users)
            ].reset_index(drop=True)

            st.session_state.pt_users1.index = range(
                st.session_state.pt_users1.index.start + 1,
                st.session_state.pt_users1.index.stop + 1,
            )
            st.session_state.pt_users1["observacions"] = st.session_state.pt_users1[
                "observacions"
            ].apply(lambda x: "{:,.0f}".format(x).replace(",", " "))

        st.dataframe(st.session_state.pt_users1, use_container_width=True, height=210)

        # Nombre
        __, col1b, __ = st.columns([1, 10, 1])
        with col1b:
            nombre = st.session_state.pt_users1.loc[1, "participant"]
            st.subheader(f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})")
            # st.markdown(f":first_place_medal: **[{nombre}]('https://minka-sdg.org/users/{nombre}')**")

            # Foto
            try:
                url = f"{base_url}/users/{nombre}.json"
                foto = f"https://minka-sdg.org/{requests.get(url).json()['medium_user_icon_url']}"
                response = requests.get(foto)
                st.image(response.content, caption=nombre, width=300)
            except:
                pass

    with col2:
        st.subheader("Tarragona")
        # Dataframe
        if "pt_users2" not in st.session_state:
            st.session_state.pt_users2 = pd.read_csv(
                f"{directory}/data/122_pt_users.csv"
            )
            st.session_state.pt_users2 = st.session_state.pt_users2[
                -st.session_state.pt_users2.participant.isin(exclude_users)
            ].reset_index(drop=True)
            st.session_state.pt_users2.index = range(
                st.session_state.pt_users2.index.start + 1,
                st.session_state.pt_users2.index.stop + 1,
            )
            st.session_state.pt_users2["observacions"] = st.session_state.pt_users2[
                "observacions"
            ].apply(lambda x: "{:,.0f}".format(x).replace(",", " "))

        st.dataframe(st.session_state.pt_users2, use_container_width=True, height=210)

        # Nombre
        __, col1b, __ = st.columns([1, 10, 1])
        with col1b:
            nombre = st.session_state.pt_users2.loc[1, "participant"]
            st.subheader(f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})")

            # Foto
            try:
                url = f"{base_url}/users/{nombre}.json"
                foto = f"https://minka-sdg.org/{requests.get(url).json()['medium_user_icon_url']}"
                response = requests.get(foto)
                st.image(response.content, caption=nombre, width=300)
            except:
                pass

    with col3:
        st.subheader("Barcelona")

        # Dataframe
        if "pt_users3" not in st.session_state:
            st.session_state.pt_users3 = pd.read_csv(
                f"{directory}/data/123_pt_users.csv"
            )
            st.session_state.pt_users3 = st.session_state.pt_users3[
                -st.session_state.pt_users3.participant.isin(exclude_users)
            ].reset_index(drop=True)
            st.session_state.pt_users3.index = range(
                st.session_state.pt_users3.index.start + 1,
                st.session_state.pt_users3.index.stop + 1,
            )
            st.session_state.pt_users3["observacions"] = st.session_state.pt_users3[
                "observacions"
            ].apply(lambda x: "{:,.0f}".format(x).replace(",", " "))

        st.dataframe(st.session_state.pt_users3, use_container_width=True, height=210)

        # Nombre
        __, col1b, __ = st.columns([1, 10, 1])
        with col1b:
            nombre = st.session_state.pt_users3.loc[1, "participant"]
            st.subheader(f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})")

            # Foto
            try:
                url = f"{base_url}/users/{nombre}.json"
                foto = f"https://minka-sdg.org/{requests.get(url).json()['medium_user_icon_url']}"
                response = requests.get(foto)
                st.image(response.content, caption=nombre, width=300)
            except:
                pass


st.divider()

# Carrusel de últimas observaciones,
# con grado research, excluidos xasalva y mediambient_ajelprat
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Últimes observacions publicades]")

    # Botones
    last_total = get_last_obs(124)

    if "index" not in st.session_state:
        st.session_state.index = 0

    __, col1, col2, col3 = st.columns([10, 1, 1, 10])
    with col1:
        if st.button(":orange[**<<**]"):
            if st.session_state.index > 4:
                st.session_state.index = 0
    with col2:
        if st.button(":orange[**>>**]"):
            st.session_state.index += 5

    # convertimos el df para que sólo aparezcan 5 obs de cada usuario como máximo
    results = pd.DataFrame()
    for user in last_total.user_login.unique():
        last_five = last_total[last_total.user_login == user][:5]
        results = pd.concat([results, last_five], axis=0)
    results.reset_index(drop=True, inplace=True)
    results = results.sort_values(by="id", ascending=False)

    for c in st.columns(5, gap="medium"):
        with c:
            photo_url = results.loc[st.session_state.index, "photos_medium_url"]
            photo_url = photo_url.replace("/medium/", "/original/")

            mdlit(
                f"@(https://minka-sdg.org/observations/{results.loc[st.session_state.index, 'id']})"
            )

            st.image(
                photo_url, caption=results.loc[st.session_state.index, "taxon_name"]
            )
            st.session_state.index += 1

st.divider()

# Últimas especies incorporadas, excluyendo las subidas por xavi y ajelprat
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Últimes espècies registrades]")

    # Dataframes de observaciones de cada provincia
    excluded = ["xasalva", "mediambient_ajelprat"]
    sp_girona = pd.read_csv(f"{directory}/data/121_species.csv")
    sp_girona = sp_girona[-sp_girona.author.isin(excluded)]
    sp_girona = sp_girona[sp_girona.photo_url.notnull()].reset_index(drop=True)

    sp_tarragona = pd.read_csv(f"{directory}/data/122_species.csv")
    sp_tarragona = sp_tarragona[-sp_tarragona.author.isin(excluded)]
    sp_tarragona = sp_tarragona[sp_tarragona.photo_url.notnull()].reset_index(drop=True)

    sp_barcelona = pd.read_csv(f"{directory}/data/123_species.csv")
    sp_barcelona = sp_barcelona[-sp_barcelona.author.isin(excluded)]
    sp_barcelona = sp_barcelona[sp_barcelona.photo_url.notnull()].reset_index(drop=True)

    for df in [sp_girona, sp_tarragona, sp_barcelona]:
        df = reindex(df)

    # Girona
    st.subheader("Girona")
    i = 1
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    with col1:
        st.dataframe(
            sp_girona[["name", "first_date"]].rename(columns={"first_date": "data"}),
            use_container_width=True,
            height=300,
        )

    for col in [col2, col3, col4, col5]:
        with col:
            photo_url = sp_girona.loc[i, "photo_url"].replace("/large/", "/original/")
            taxon_id = sp_girona.loc[i, "id"]
            taxon_name = sp_girona.loc[i, "name"]
            st.markdown(
                f":link: [Minka](https://minka-sdg.org/observations/{sp_girona.loc[i, 'obs_id']})"
            )
            st.image(
                photo_url,
                caption=f"{taxon_name} | Foto: {sp_girona.loc[i, 'author']}",
                width=300,
            )
            i += 1
    st.divider()

    # Tarragona
    st.subheader("Tarragona")
    i = 1
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    with col1:
        st.dataframe(
            sp_tarragona[["name", "first_date"]].rename(columns={"first_date": "data"}),
            use_container_width=True,
            height=300,
        )

    for col in [col2, col3, col4, col5]:
        with col:
            photo_url = sp_tarragona.loc[i, "photo_url"].replace(
                "/large/", "/original/"
            )
            taxon_id = sp_tarragona.loc[i, "id"]
            taxon_name = sp_tarragona.loc[i, "name"]
            st.markdown(
                f":link: [Minka](https://minka-sdg.org/observations/{sp_tarragona.loc[i, 'obs_id']})"
            )
            st.image(
                photo_url,
                caption=f"{taxon_name} | Foto: {sp_tarragona.loc[i, 'author']}",
                width=300,
            )
            i += 1
    st.divider()

    # Barcelona
    st.subheader("Barcelona")
    i = 1
    col1sp, col2sp, col3sp, col4sp, col5sp = st.columns(5, gap="medium")
    with col1sp:
        st.dataframe(
            sp_barcelona[["name", "first_date"]].rename(columns={"first_date": "data"}),
            use_container_width=True,
            height=300,
        )

    for col in [col2sp, col3sp, col4sp, col5sp]:
        with col:
            photo_url = sp_barcelona.loc[i, "photo_url"].replace(
                "/large/", "/original/"
            )
            taxon_id = sp_barcelona.loc[i, "id"]
            taxon_name = sp_barcelona.loc[i, "name"]
            st.markdown(
                f":link: [Minka](https://minka-sdg.org/observations/{sp_barcelona.loc[i, 'obs_id']})"
            )
            st.image(
                photo_url,
                caption=f"{taxon_name} | Foto: {sp_barcelona.loc[i, 'author']}",
                width=300,
            )
            i += 1
    st.divider()


# Mapas (incluye todos los usuarios y todos los grados)
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Mapes]")

    project_name = st.selectbox(
        label="Projecte per mostrar al mapa",
        options=("Tarragona", "Barcelona", "Girona", "Catalunya"),
    )

    project_ids = {"Barcelona": 123, "Tarragona": 122, "Girona": 121, "Catalunya": 124}

    proj_id = project_ids[project_name]

    df_map = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")

    map1, map2 = st.columns(2)
    with map1:
        st.session_state.st_heatmap = folium_static(create_heatmap(df_map))
    with map2:
        st.session_state.st_clustermap = folium_static(create_markercluster(df_map))

st.divider()

# Agradecimientos
with st.container():
    df_124 = pd.read_csv(f"{directory}/data/124_df_obs.csv")
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Agraïments]")
    st.markdown("A la Biomarató 2023 de Catalunya han participat:")
    list_participants = df_124.user_login.unique()
    list_participants.sort()
    linked_list = []
    for p in list_participants:
        linked_list.append(f"[{p}](https://minka-sdg.org/users/{p})")
    agraiments = ", ".join(linked_list)
    st.markdown(f"{agraiments}")

# Logos
st.divider()
with st.container():
    __, col_1, col_2, __ = st.columns([1, 10, 10, 1])
    with col_1:
        st.subheader("Organitzadors:")
        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{directory}/images/organitzadors-biomarato-1.png")

    with col_2:
        st.subheader("Amb el finançament dels projectes Europeus:")
        col1, __ = st.columns(2)

        # Finançament
        with col1:
            st.image(f"{directory}/images/entitats-biomarato-2.png")
