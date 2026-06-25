# Contents of ~/my_app/main_page.py
import os

try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    directory = os.path.dirname(os.path.abspath(__file__))
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

import streamlit as st

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard Bioplatgesmet",
)

from datetime import datetime

import pandas as pd
import streamlit.components.v1 as components
from i18n import create_footer, create_sidebar_content, init_i18n, t
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

# configuracion de ModeBar
config_modebar = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "zoom2d",
        "pan2d",
        "lasso2d",
        "autoScale2d",
        "resetScale2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
        "zoomIn2d",
        "zoomOut2d",
    ],
    "displaylogo": False,
}

# Initialize i18n
init_i18n(current_page="main")
create_sidebar_content()

base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"

main_project = 264

codes = {
    163: "Montgat",
    164: "Castelldefels",
    165: "Barcelona",
    166: "Viladecans",
    167: "Gava",
    168: "El Prat",
    169: "Sant Adria",
    170: "Badalona",
}

matomo_script = """
<!-- Matomo -->
<script>
  var _paq = window._paq = window._paq || [];
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


# Cacheado de datos optimizado
@st.cache_data(ttl=3600, show_spinner=False)
def load_csv(file_path):
    return pd.read_csv(file_path)


@st.cache_data(ttl=3600, show_spinner=False)
def load_and_process_cumulative_data():
    """Carga y procesa datos acumulativos mensuales"""
    df_cumulative_monthly = pd.read_csv(
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
            "total_spe": "especies",
            "total_part": "participants",
            "total_ident": "identificadores",
        },
        inplace=True,
    )
    return df_cum_monthly_general.reset_index(drop=True).loc[5:]


@st.cache_data(ttl=3600, show_spinner=False)
def load_and_process_monthly_data():
    """Carga y procesa datos mensuales (no acumulados)"""
    df_monthly = pd.read_csv(f"{directory}/data/city_monthly_metrics.csv")
    df_monthly_general = df_monthly[df_monthly.city == "BioPlatgesMet"].copy()
    df_monthly_general["month"] = df_monthly_general["month"].astype(str)
    df_monthly_general.rename(
        columns={
            "city": "ciutat",
            "month": "data",
            "total_obs": "observacions",
            "total_spe": "especies",
            "total_part": "participants",
            "total_ident": "identificadores",
        },
        inplace=True,
    )
    return df_monthly_general.reset_index(drop=True).loc[5:]


@st.cache_data(ttl=3600, show_spinner=False)
def load_and_process_main_metrics():
    """Carga y procesa metricas principales"""
    main_metrics = pd.read_csv(f"{directory}/data/264_main_metrics.csv")
    main_metrics.rename(
        columns={
            "date": "data",
            "observations": "observacions",
            "species": "especies",
            "identifiers": "identificadores",
        },
        inplace=True,
    )
    return main_metrics


@st.cache_data(ttl=3600, show_spinner=False)
def load_observations_data():
    """Carga datos de observaciones"""
    return pd.read_csv(f"{directory}/data/{main_project}_obs.csv")


@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")


def create_header():
    with st.container():
        col1, col2 = st.columns([1, 15])
        with col1:
            st.image(f"{directory}/images/Logo_BioplatgesMet.png")
        with col2:
            st.header(f":blue[{t('header.main_title')}]")


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
            f":camera_with_flash: {t('metrics.observations')}",
            f"{total_obs:,}".replace(",", " "),
            f"+{total_obs - lw_obs} {t('metrics.last_week')}",
        )
    with col2:
        st.metric(
            f":ladybug: {t('metrics.species')}",
            total_species,
            f"+{total_species - lw_spe} {t('metrics.last_week')}",
        )
    with col3:
        st.metric(
            f":eyes: {t('metrics.participants')}",
            total_participants,
            f"+{total_participants - lw_part} {t('metrics.last_week')}",
        )
    with col4:
        st.metric(
            f":books: {t('metrics.identifiers')}",
            total_identifiers,
            f"+{total_identifiers - lw_ident} {t('metrics.last_week')}",
        )
    style_metric_cards(
        background_color="#fff",
        border_left_color=colors[1],
        box_shadow=False,
    )


# Grafico de columnas mensual (no acumulado)
with st.container():
    cum_monthly_result = load_and_process_monthly_data()

    fecha_actual = datetime.now()
    month_year = fecha_actual.strftime("%Y-%m")
    start_date, end_date = st.select_slider(
        f"**{t('ui.select_time_range')}**",
        options=cum_monthly_result.data.unique(),
        value=(
            "2022-06",
            month_year,
        ),
    )
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            f"\t{t('metrics.observations')}\t",
            f"\t{t('metrics.species')}\t",
            f"\t{t('metrics.participants')}\t",
            f"\t{t('metrics.identifiers')}\t",
        ]
    )

    with tab1:
        fig1b = fig_bars_months(
            cum_monthly_result,
            field="observacions",
            title=t("charts.observations_accumulated"),
            color=colors[0],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig1b, config=config_modebar, use_container_width=True)

    with tab2:
        fig2b = fig_bars_months(
            cum_monthly_result,
            field="especies",
            title=t("charts.species_accumulated"),
            color=colors[1],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig2b, config=config_modebar, use_container_width=True)

    with tab3:
        fig3b = fig_bars_months(
            cum_monthly_result,
            field="participants",
            title=t("charts.participants_accumulated"),
            color=colors[2],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig3b, config=config_modebar, use_container_width=True)

    with tab4:
        fig4b = fig_bars_months(
            cum_monthly_result,
            field="identificadores",
            title=t("charts.identifiers_accumulated"),
            color=colors[3],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig4b, config=config_modebar, use_container_width=True)

    # Cache de conversion CSV
    if "csv2" not in st.session_state:
        st.session_state.csv2 = convert_df(cum_monthly_result)

    st.download_button(
        label=t("ui.download_data"),
        data=st.session_state.csv2,
        file_name="cum_monthly_result.csv",
        mime="text/csv",
    )


# Grafico de area, evolucion por dias
with st.container():
    main_metrics = load_and_process_main_metrics()

    tab5, tab6, tab7, tab8 = st.tabs(
        [
            f"\t{t('metrics.observations')}\t",
            f"\t{t('metrics.species')}\t",
            f"\t{t('metrics.participants')}\t",
            f"\t{t('metrics.identifiers')}\t",
        ]
    )

    with tab5:
        fig1 = fig_area_evolution(
            df=main_metrics,
            field="observacions",
            title=t("charts.observations_evolution"),
            color=colors[0],
            start_date=start_date,
            end_date=end_date,
        )

        st.plotly_chart(fig1, config=config_modebar, use_container_width=True)

        if "csv1" not in st.session_state:
            st.session_state.csv1 = convert_df(main_metrics)

        st.download_button(
            label=t("ui.download_data"),
            data=st.session_state.csv1,
            file_name="main_metrics_by_day.csv",
            mime="text/csv",
        )

    with tab6:
        fig2 = fig_area_evolution(
            df=main_metrics,
            field="especies",
            title=t("charts.species_evolution"),
            color=colors[1],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig2, config=config_modebar, use_container_width=True)

    with tab7:
        fig3 = fig_area_evolution(
            df=main_metrics,
            field="participants",
            title=t("charts.participants_evolution"),
            color=colors[2],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig3, config=config_modebar, use_container_width=True)

    with tab8:
        fig4 = fig_area_evolution(
            df=main_metrics,
            field="identificadores",
            title=t("charts.identifiers_evolution"),
            color=colors[3],
            start_date=start_date,
            end_date=end_date,
        )
        st.plotly_chart(fig4, config=config_modebar, use_container_width=True)


st.divider()

with st.container():
    st.header(t("charts.observations_by_beach"))

    df = load_observations_data()

    map1, map2 = st.columns([10, 10], gap="small")

    @st.cache_resource(ttl=3600, show_spinner=False)
    def get_cached_maps(data_hash):
        """Crea mapas con cache basado en hash de datos"""
        heatmap = create_heatmap(df, center=[41.36174441599461, 2.108076037807884])
        markermap = create_markercluster(
            df, center=[41.36174441599461, 2.108076037807884]
        )
        return heatmap, markermap

    data_hash = hash(str(df.shape) + str(df["id"].iloc[0] if len(df) > 0 else ""))
    heatmap, markermap = get_cached_maps(data_hash)

    with map1:
        map_html1 = heatmap._repr_html_()
        components.html(map_html1, height=600)
    with map2:
        map_html2 = markermap._repr_html_()
        components.html(map_html2, height=600)

    if "csv3" not in st.session_state:
        st.session_state.csv3 = convert_df(df)

    st.download_button(
        label=t("ui.download_data"),
        data=st.session_state.csv3,
        file_name="observacions_bioplatgesmet.csv",
        mime="text/csv",
    )

# Footer
create_footer()
