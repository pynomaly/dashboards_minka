# Run as streamlit run app_biomarato.py --server.port 9003

import os

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
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
    load_maps,
    reindex,
)

# Variable de entorno para el directorio
try:
    directory = f"{os.environ['DASHBOARDS']}/biomarato_24"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard BioMARató 2024",
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
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "anellides",
    "irodero",
    "manelsalvador",
    "sara_riera",
    "anomalia",
    "amaliacardenas",
    "aluna",
    "carlosrodero",
    "lydia",
    "elibonfill",
    "marinatorresgi",
    "meri",
    "monyant",
    "ura4dive",
    "lauracoro",
    "pirotte_",
    "oceanicos",
    "abril",
    "alba_barrera",
    "amb_platges",
    "daniel_palacios",
    "davidpiquer",
    "laiamanyer",
    "rogerpuig",
    "guillemdavila",
    # vanessa,
    # teresa,
]
matomo_script = """
    <!-- Matomo -->
    <script>
    var _paq = window._paq = window._paq || [];
    /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
    _paq.push(['trackPageView']);
    _paq.push(['enableLinkTracking']);
    (function() {
        var u="//matomo.quanta-labs.com/";
        _paq.push(['setTrackerUrl', u+'matomo.php']);
        _paq.push(['setSiteId', '8']);
        var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
        g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
    })();
    </script>
    <!-- End Matomo Code -->
"""

base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"


projects = [
    {"id": 281, "name": "Girona"},
    {"id": 280, "name": "Tarragona"},
    {"id": 282, "name": "Barcelona"},
    {"id": 283, "name": "Catalunya"},
]

main_project = 283

# Error si no responde la API
try:
    total_species, total_participants, total_obs = get_main_metrics(main_project)
    lw_obs, lw_spe, lw_part = get_last_week_metrics(main_project)
except:
    st.error("Error loading data")
    st.stop()

# Main metrics (incluye todos los usuarios y todos los grados)
components.html(matomo_script, height=0, width=0)

with st.container():
    col1, col2 = st.columns([1, 14])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Resultats BioMARató 2024]")
        st.markdown(":orange[May 6, 2024 - Oct 15, 2024]")

    __, col1, col2, col3, _ = st.columns([2, 1, 1, 1, 2])
    with col1:
        st.metric(
            ":camera_with_flash: Observacions",
            f"{total_obs:,}".replace(",", " "),
            f"+{total_obs - lw_obs:,} última setmana".replace(",", " "),
        )
    with col2:
        st.metric(
            ":ladybug: Espècies",
            f"{total_species:,}".replace(",", " "),
            f"+{total_species - lw_spe} última setmana",
        )
    with col3:
        st.metric(
            ":eyes: Participants",
            f"{total_participants:,}".replace(",", " "),
            f"+{total_participants - lw_part} última setmana",
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

    col1_line, col2_line, col3_line = st.columns(3, gap="large")

    with col1_line:
        fig1 = fig_area_evolution(
            df=main_metrics,
            field="observacions",
            title="Evolució del nombre d'observacions",
            color="#089aa2",
        )

        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)

    with col2_line:
        fig2 = fig_area_evolution(
            df=main_metrics,
            field="espècies",
            title="Evolució del nombre d'espècies",
            color="#dc6619",
        )
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)

    with col3_line:
        fig3 = fig_area_evolution(
            df=main_metrics,
            field="participants",
            title="Evolució del nombre de participants",
            color="#f9b853",
        )
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

    # Resultados mensuales
    grouped = get_grouped_monthly(project_id=main_project)
    # grouped["data"] = grouped["data"].astype(str)
    col1_month, col2_month, col3_month = st.columns(3, gap="large")
    with col1_month:
        fig1b = fig_bars_months(
            grouped,
            field="observacions",
            title="Nombre d'observacions per mes",
            color="#089aa2",
        )
        st.plotly_chart(fig1b, config=config_modebar, use_container_width=True)

    with col2_month:
        fig2b = fig_bars_months(
            grouped,
            field="espècies",
            title="Nombre de espècies per mes",
            color="#dc6619",
        )
        st.plotly_chart(fig2b, config=config_modebar, use_container_width=True)

    with col3_month:
        fig3b = fig_bars_months(
            grouped,
            field="participants",
            title="Nombre de participants per mes",
            color="#f9b853",
        )
        st.plotly_chart(fig3b, config=config_modebar, use_container_width=True)

st.divider()

# Ranking by province (incluye todos los usuarios y todos los grados)
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
        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)
    with col2:
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)
    with col3:
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

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
    # Header participantes
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Rànquing de participants]")
    st.markdown("Nombre d'observacions amb grau de recerca.")

    pd.read_csv(f"{directory}/data/{main_project}_pt_users.csv")
    col0, col1, col2, col3 = st.columns(4, gap="large")

    # Ranking general
    with col0:
        st.subheader("General")
        # Tabla
        if "pt_users0" not in st.session_state:
            st.session_state.pt_users0 = pd.read_csv(
                f"{directory}/data/{main_project}_pt_users.csv"
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

        st.dataframe(
            st.session_state.pt_users0[["participant", "observacions", "espècies"]],
            use_container_width=True,
            height=210,
        )

        # Medallas
        __, col1b, __ = st.columns([1, 10, 1])
        with col1b:
            if len(st.session_state.pt_users0) > 0:
                medals = [
                    "first_place_medal",
                    "second_place_medal",
                    "third_place_medal",
                ]
                for i in range(1, 4):
                    nombre = st.session_state.pt_users0.loc[i, "participant"]
                    st.subheader(
                        f":{medals[i-1]}: [{nombre}](https://minka-sdg.org/users/{nombre})"
                    )

    # Ranking Girona
    with col1:
        try:
            st.subheader("Girona")

            # Dataframe
            if "pt_users1" not in st.session_state:
                st.session_state.pt_users1 = pd.read_csv(
                    f"{directory}/data/281_pt_users.csv"
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

            st.dataframe(
                st.session_state.pt_users1[["participant", "observacions", "espècies"]],
                use_container_width=True,
                height=210,
            )

            # Nombre
            __, col1b, __ = st.columns([1, 10, 1])
            with col1b:
                if len(st.session_state.pt_users1) > 0:
                    nombre = st.session_state.pt_users1.loc[1, "participant"]
                    st.subheader(
                        f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})"
                    )
                    # st.markdown(f":first_place_medal: **[{nombre}]('https://minka-sdg.org/users/{nombre}')**")

                    # Foto
                    try:
                        url = f"{base_url}/users/{nombre}.json"
                        foto = f"https://minka-sdg.org/{requests.get(url).json()['medium_user_icon_url']}"
                        response = requests.get(foto)
                        st.image(response.content, caption=nombre, width=300)
                    except:
                        pass
        except FileNotFoundError:
            pass

    # Ranking Tarragona
    with col2:
        st.subheader("Tarragona")
        # Dataframe
        if "pt_users2" not in st.session_state:
            st.session_state.pt_users2 = pd.read_csv(
                f"{directory}/data/280_pt_users.csv"
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

        st.dataframe(
            st.session_state.pt_users2[["participant", "observacions", "espècies"]],
            use_container_width=True,
            height=210,
        )

        # Nombre
        __, col1b, __ = st.columns([1, 10, 1])
        with col1b:
            if len(st.session_state.pt_users2) > 0:
                nombre = st.session_state.pt_users2.loc[1, "participant"]
                st.subheader(
                    f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})"
                )

                # Foto
                try:
                    url = f"{base_url}/users/{nombre}.json"
                    foto = f"https://minka-sdg.org/{requests.get(url).json()['medium_user_icon_url']}"
                    response = requests.get(foto)
                    st.image(response.content, caption=nombre, width=300)
                except:
                    pass

    # Ranking Barcelona
    with col3:
        st.subheader("Barcelona")

        # Dataframe
        if "pt_users3" not in st.session_state:
            st.session_state.pt_users3 = pd.read_csv(
                f"{directory}/data/282_pt_users.csv"
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

        st.dataframe(
            st.session_state.pt_users3[["participant", "observacions", "espècies"]],
            use_container_width=True,
            height=210,
        )

        # Nombre
        __, col1b, __ = st.columns([1, 10, 1])
        with col1b:
            if len(st.session_state.pt_users3) > 0:
                nombre = st.session_state.pt_users3.loc[1, "participant"]
                st.subheader(
                    f":medal: [{nombre}](https://minka-sdg.org/users/{nombre})"
                )

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

    # Visor de imágenes: 15 imágenes, máximo 3 por usuario
    # Excluye a Xavi y a mediambient_ajelprat en la función
    try:
        last_total = get_last_obs(main_project)

        # convertimos el df para que sólo aparezcan 5 obs de cada usuario como máximo
        results = pd.DataFrame()
        for user in last_total.user_login.unique():
            last_five = last_total[last_total.user_login == user][:3]
            results = pd.concat([results, last_five], axis=0)
        # results = results.reset_index(drop=True)
        results = (
            results.sort_values(by="id", ascending=False)
            .reset_index(drop=True)
            .head(15)
        )

        c1, c2, c3, c4, c5 = st.columns(5)
        col = 0
        for index, row in results.iterrows():
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
                    mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
                col += 1
            elif col == 1:
                with c2:
                    st.image(response.content)
                    mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
                col += 1
            elif col == 2:
                with c3:
                    st.image(response.content)
                    mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
                col += 1
            elif col == 3:
                with c4:
                    st.image(response.content)
                    mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
                col += 1
            elif col == 4:
                with c5:
                    st.image(response.content)
                    mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
                col = 0

    except FileNotFoundError:
        pass
st.divider()

# Últimas especies incorporadas, excluyendo las subidas por xavi y ajelprat
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Últimes espècies registrades]")

    # usuarios excluidos
    excluded = ["xasalva", "mediambient_ajelprat"]

    # Dataframes de observaciones de cada provincia
    try:
        sp_girona = pd.read_csv(f"{directory}/data/281_species.csv")
        sp_girona = sp_girona[-sp_girona.author.isin(excluded)]
        sp_girona = sp_girona[sp_girona.photo_url.notnull()].reset_index(drop=True)
    except:
        sp_girona = None
    try:
        sp_tarragona = pd.read_csv(f"{directory}/data/280_species.csv")
        sp_tarragona = sp_tarragona[-sp_tarragona.author.isin(excluded)]
    except FileNotFoundError:
        sp_tarragona = None

    try:
        sp_barcelona = pd.read_csv(f"{directory}/data/282_species.csv")
        sp_barcelona = sp_barcelona[-sp_barcelona.author.isin(excluded)]
        sp_barcelona = sp_barcelona[sp_barcelona.photo_url.notnull()].reset_index(
            drop=True
        )
    except FileNotFoundError:
        sp_barcelona = None

    for df in [sp_girona, sp_tarragona, sp_barcelona]:
        if df is not None:
            df = reindex(df)

    # Girona
    st.subheader("Girona")
    i = 1
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    try:
        with col1:
            st.dataframe(
                sp_girona[["name", "first_date"]].rename(
                    columns={"first_date": "data"}
                ),
                use_container_width=True,
                height=300,
            )

        for col in [col2, col3, col4, col5]:
            with col:
                photo_url = sp_girona.loc[i, "photo_url"].replace(
                    "/large/", "/original/"
                )
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
    except:
        st.markdown("Cap espècie a Girona")

    st.divider()

    # Tarragona
    st.subheader("Tarragona")
    try:
        i = 1
        col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
        with col1:
            try:
                st.dataframe(
                    sp_tarragona[["name", "first_date"]].rename(
                        columns={"first_date": "data"}
                    ),
                    use_container_width=True,
                    height=300,
                )
            except:
                st.markdown("Cap espècie a Tarragona")
        try:
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
        except:
            pass
    except:
        pass

    st.divider()

    # Barcelona
    st.subheader("Barcelona")
    try:
        i = 1
        col1sp, col2sp, col3sp, col4sp, col5sp = st.columns(5, gap="medium")
        with col1sp:
            st.dataframe(
                sp_barcelona[["name", "first_date"]].rename(
                    columns={"first_date": "data"}
                ),
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
    except:
        st.markdown("Cap espècie a Barcelona")

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

    project_ids = {"Barcelona": 282, "Tarragona": 280, "Girona": 281, "Catalunya": 283}

    proj_id = project_ids[project_name]
    try:
        df_map = pd.read_csv(f"{directory}/data/{proj_id}_df_obs.csv")

        map1, map2 = st.columns(2)

        # Guardar el mapa en session_state para evitar que desaparezca
        st.session_state.heatmap = create_heatmap(df_map)
        st.session_state.markermap = create_markercluster(df_map)

        with map1:
            map_html1 = st.session_state.heatmap._repr_html_()
            components.html(map_html1, height=600)
        with map2:
            map_html2 = st.session_state.markermap._repr_html_()
            components.html(map_html2, height=600)
    except FileNotFoundError:
        pass

st.divider()

load_maps()

# Agradecimientos
with st.container():

    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Agraïments]")
    st.markdown("A la Biomarató 2024 de Catalunya han participat:")
    try:
        df_283 = pd.read_csv(f"{directory}/data/283_df_obs.csv")
        list_participants = df_283.user_login.unique()
        list_participants.sort()
        linked_list = []
        for p in list_participants:
            linked_list.append(f"[{p}](https://minka-sdg.org/users/{p})")
        agraiments = ", ".join(linked_list)
        st.markdown(f"{agraiments}")
    except FileNotFoundError:
        pass

# Logos
st.divider()
with st.container():
    __, col_1, col_2, __ = st.columns([1, 10, 10, 1])
    with col_1:
        st.subheader("Organitzadors:")
        col1, __ = st.columns([3, 2])
        with col1:
            st.image(f"{directory}/images/organizadores_2024_v2.png")

    with col_2:
        st.subheader("Amb el finançament dels projectes europeus:")
        col1, __ = st.columns([5, 1])

        # Finançament
        with col1:
            st.image(f"{directory}/images/logos_financiacion_biomarato_v2.png")
