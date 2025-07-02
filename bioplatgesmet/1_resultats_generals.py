# Contents of ~/my_app/main_page.py
import os
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# from streamlit.components.v1 import html
from streamlit_extras.metric_cards import style_metric_cards
from utils import (
    create_heatmap,
    create_markercluster,
    fig_area_evolution,
    fig_bars_months,
    get_last_week_metrics,
    get_main_metrics,
)

# variables
colors = ["#009DE0", "#0081B8", "#00567A", "#3b4a7f"]

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

try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard Bioplatgesmet",
)


base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"

main_project = 264

codes = {
    163: "Montgat",
    164: "Castelldefels",
    165: "Barcelona",
    166: "Viladecans",
    167: "Gavà",
    168: "El Prat",
    169: "Sant Adrià",
    170: "Badalona",
}

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
    _paq.push(['setSiteId', '7']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
  })();
</script>
<!-- End Matomo Code -->
"""


# Cacheado de datos
@st.cache_data(ttl=3600)
def load_csv(file_path):
    return pd.read_csv(file_path)


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


def create_sidebar():
    st.sidebar.markdown("# BioPlatgesMet")
    st.sidebar.markdown(
        """
    El Servei de Platges de l’AMB, l’Institut de Ciències del Mar – CSIC i l'Institut Metròpoli participen en el projecte europeu GUARDEN (Programa Horizon Europe) junt amb altres 15 socis de 8 països. BioPlatgesMet és el nom del seu desenvolupament en l’àmbit de les platges metropolitanes.

    El seu objectiu principal és protegir la biodiversitat de les platges metropolitanes, preservar els beneficis que la natura aporta a la societat i conscienciar la ciutadania de la seva importància. Aquesta iniciativa de ciència ciutadana recopilarà dades sobre la biodiversitat de les platges amb geolocalització, mapatge de vegetació i seguiment d'espècies a l'ecosistema platja-duna amb tecnologies per identificar-les.
    """
    )


def create_header():
    with st.container():
        # Título
        col1, col2 = st.columns([1, 15])
        with col1:
            st.image(f"{directory}/images/Logo_BioplatgesMet.png")
        with col2:
            st.header(":blue[Panell de seguiment BioPlatgesMet]")


# Columna izquierda
create_sidebar()

# Header

components.html(matomo_script, height=0, width=0)

create_header()

# Error si no responde la API
try:
    total_obs, total_species, total_participants, total_identifiers = get_main_metrics(
        main_project
    )
    lw_obs, lw_spe, lw_part, lw_ident = get_last_week_metrics(main_project)
except:
    st.error("Error loading data")
    st.stop()

with st.container():
    # Tarjetas de totales
    __, col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 1, 1])
    with col1:
        st.metric(
            ":camera_with_flash: Observacions",
            f"{total_obs:,}".replace(",", " "),
            f"+{total_obs - lw_obs} última setmana",
        )
    with col2:
        st.metric(
            ":ladybug: Espècies",
            total_species,
            f"+{total_species - lw_spe} última setmana",
        )
    with col3:
        st.metric(
            ":eyes: Participants",
            total_participants,
            f"+{total_participants - lw_part} última setmana",
        )
    with col4:
        st.metric(
            ":books: Persones idenficadores",
            total_identifiers,
            f"+{total_identifiers - lw_ident} última setmana",
        )
    style_metric_cards(
        background_color="#fff",
        # border_left_color="#C2C2C2",
        border_left_color=colors[1],
        box_shadow=False,
    )


# Gráfico de columnas, acumulado mensual
with st.container():
    df_cumulative_monthly = load_csv(
        f"{directory}/data/cumulative_city_monthly_metrics.csv"
    )
    df_cum_monthly_general = df_cumulative_monthly[
        df_cumulative_monthly.city == "BioPlatgesMet"
    ].copy()
    df_cum_monthly_general["month"] = df_cum_monthly_general["month"].astype(str)
    df_cum_monthly_general.rename(
        columns={
            "city": "ciutat",
            "month": "data",
            "total_obs": "observacions",
            "total_spe": "espècies",
            "total_part": "participants",
            "total_ident": "identificadores",
        },
        inplace=True,
    )

    # Resultados mensuales desde junio 2022

    fecha_actual = datetime.now()
    month_year = fecha_actual.strftime("%Y-%m")

    cum_monthly_result = df_cum_monthly_general.reset_index(drop=True).loc[5:]
    start_date, end_date = st.select_slider(
        "**Selecciona un rang temporal per als gràfics:**",
        options=cum_monthly_result.data.unique(),
        value=(
            "2022-06",
            month_year,
        ),
    )
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "\tObservacions\t",
            "\tEspècies\t",
            "\tParticipants\t",
            "\tPersones idenficadores\t",
        ]
    )

    with tab1:
        fig1b = fig_bars_months(
            cum_monthly_result,
            field="observacions",
            title="Acumulat d'observacions per mes",
            color=colors[0],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig1b, config=config_modebar, use_container_width=True)

    with tab2:
        fig2b = fig_bars_months(
            cum_monthly_result,
            field="espècies",
            title="Acumulat d'espècies per mes",
            color=colors[1],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig2b, config=config_modebar, use_container_width=True)

    with tab3:
        fig3b = fig_bars_months(
            cum_monthly_result,
            field="participants",
            title="Acumulat de participants per mes",
            color=colors[2],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig3b, config=config_modebar, use_container_width=True)

    with tab4:
        fig4b = fig_bars_months(
            cum_monthly_result,
            field="identificadores",
            title="Acumulat de persones identificadores per mes",
            color=colors[3],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig4b, config=config_modebar, use_container_width=True)

    csv2 = convert_df(cum_monthly_result)

    st.download_button(
        label="Descarrega les dades",
        data=csv2,
        file_name="cum_monthly_result.csv",
        mime="text/csv",
    )


# Gráfico de área, evolución por días
with st.container():
    main_metrics = load_csv(f"{directory}/data/264_main_metrics.csv")
    main_metrics.rename(
        columns={
            "date": "data",
            "observations": "observacions",
            "species": "espècies",
            "identifiers": "identificadores",
        },
        inplace=True,
    )

    tab5, tab6, tab7, tab8 = st.tabs(
        [
            "\tObservacions\t",
            "\tEspècies\t",
            "\tParticipants\t",
            "\tPersones idenficadores\t",
        ]
    )

    with tab5:
        fig1 = fig_area_evolution(
            df=main_metrics,
            field="observacions",
            title="Evolució del nombre d'observacions",
            color=colors[0],
            start_date=start_date,
            end_date=end_date,
        )

        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)

        csv1 = convert_df(main_metrics)

        st.download_button(
            label="Descarrega les dades",
            data=csv1,
            file_name="main_metrics_by_day.csv",
            mime="text/csv",
        )

    with tab6:
        fig2 = fig_area_evolution(
            df=main_metrics,
            field="espècies",
            title="Evolució del nombre d'espècies",
            color=colors[1],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)

    with tab7:
        fig3 = fig_area_evolution(
            df=main_metrics,
            field="participants",
            title="Evolució del nombre de participants",
            color=colors[2],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

    with tab8:
        fig4 = fig_area_evolution(
            df=main_metrics,
            field="identificadores",
            title="Evolució del nombre de persones identificadores",
            color=colors[3],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig4, config=config_modebar, use_container_width=True)


st.divider()

with st.container():
    st.header("Observacions per platja")
    if "df" not in st.session_state:
        st.session_state.df = load_csv(f"{directory}/data/{main_project}_obs.csv")

    df = st.session_state.df  # Reutiliza el dataframe

    map1, map2 = st.columns([10, 10], gap="small")

    # Guardar el mapa en session_state para evitar que desaparezca
    if "heatmap" not in st.session_state or st.session_state.heatmap is None:
        st.session_state.heatmap = create_heatmap(
            df, center=[41.36174441599461, 2.108076037807884]
        )

    if "markermap" not in st.session_state or st.session_state.markermap is None:
        st.session_state.markermap = create_markercluster(
            df, center=[41.36174441599461, 2.108076037807884]
        )
    with map1:
        # st_folium(st.session_state.heatmap, width=700, height=500, key="heatmap")
        map_html1 = st.session_state.heatmap._repr_html_()
        components.html(map_html1, height=600)
    with map2:
        map_html2 = st.session_state.markermap._repr_html_()
        components.html(map_html2, height=600)

    csv3 = convert_df(df)

    st.download_button(
        label="Descarrega les dades",
        data=csv3,
        file_name="observacions_bioplatgesmet.csv",
        mime="text/csv",
    )

st.container(height=50, border=False)

with st.container(border=True):
    col1, __, col2 = st.columns([10, 1, 5], gap="small")
    with col1:
        st.markdown("##### Organitzadors")
        st.image(
            f"{directory}/images/organizadores_bioplatgesmet_logos2.png",
        )
    with col2:
        st.markdown("##### Amb el finançament dels projectes europeus")
        st.image(
            f"{directory}/images/financiadores_bioplatgesmet_logos.png",
        )
