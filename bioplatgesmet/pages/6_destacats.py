import math
import os
from datetime import date, datetime, timedelta

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

grupos = ["amenazadas", "exoticas", "invasoras", "protegidas"]
main_project = 264

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
st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 220px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 220px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

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

components.html(matomo_script, height=0, width=0)


@st.cache_data(ttl=3600)
def load_csv(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def get_message(grupo: str, df_obs: pd.DataFrame, days: int, color: str) -> str:
    """Get message for a group of species."""
    # Leer el archivo de especies
    df_grupo = load_csv(f"{directory}/data/species/{grupo}.csv")
    species_ids = df_grupo.taxon_id.to_list()

    # Filtrar las observaciones del grupo y ordenar por más recientes
    last_obs = df_obs[df_obs.taxon_id.isin(species_ids)].sort_values(
        by="observed_on", ascending=False
    )

    # Filtrar observaciones de los últimos x días
    fecha_actual = date.today()
    limite = fecha_actual - timedelta(days=days)
    last_week = last_obs[
        last_obs.observed_on >= limite.strftime("%Y-%m-%d")
    ].reset_index(drop=True)

    msg = ""

    # Agrupamos las observaciones por taxon_name y contamos cada grupo
    if len(last_week) > 0:

        grouped = last_week.groupby("taxon_name")

        # Ordenar los grupos por el tamaño de cada grupo, de mayor a menor
        sorted_groups = sorted(grouped, key=lambda x: len(x[1]), reverse=True)

        for taxon_name, group in sorted_groups:
            msg += f"\n* **:{color}-background[*{taxon_name}*]**: {len(group)} observacions\n"

            # Iteramos en cada observación dentro del grupo para agregar detalles
            for _, row in group.iterrows():
                # Construimos fecha con formato DD-MM-YYYY
                fecha = f"{row['observed_on'][-2:]}-{row['observed_on'][-5:-3]}-{row['observed_on'][0:4]}"
                msg += (
                    f"    - Registrat el {fecha} a {row['address']} por *{row['user_login']}*: "
                    f"https://minka-sdg.org/observations/{row['id']}\n"
                )

    else:
        tabs = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        msg = f":gray[{tabs}Cap observació registrada.]"
    return msg


def get_members_df(id_project: int) -> pd.DataFrame:
    """Get members of a project."""
    session = requests.Session()
    # Extraemos los ids de las personas que se han unido al proyecto
    total_results = []
    url = f"https://api.minka-sdg.org/v1/projects/{id_project}/members"
    total = session.get(url).json()["total_results"]
    # Iteramos por las páginas de resultados
    for i in range(1, math.ceil(total / 100) + 1):
        url = f"https://api.minka-sdg.org/v1/projects/{id_project}/members?per_page=100&page={i}"
        results = requests.get(url).json()["results"]
        total_results.extend(results)
    df_members = pd.json_normalize(total_results)
    # Eliminamos la columna de conteo total de observaciones, para que no lleve a confusión
    df_members.drop(columns=["observations_count"], inplace=True)
    # Sacamos el número de observaciones de cada persona
    url2 = (
        f"https://api.minka-sdg.org/v1/observations/observers?project_id={id_project}"
    )
    df_observers = pd.json_normalize(session.get(url2).json()["results"])
    df_result = pd.merge(
        df_members,
        df_observers[["user_id", "observation_count"]],
        on="user_id",
        how="left",
    )
    df_result = df_result.sort_values(by="created_at", ascending=False)
    return df_result


def generar_reporte_nuevas_especies(df_sorted: pd.DataFrame, days: int) -> str:
    """
    Genera un reporte de las nuevas especies registradas en los últimos días especificados.

    """

    # Procesar primeras observaciones
    first_observed = (
        df_sorted.drop_duplicates(subset=["taxon_name"], keep="first")
        .sort_values(by=["observed_on"], ascending=False)
        .reset_index(drop=True)
    )

    # Convertir fechas y filtrar por días recientes
    first_observed["observed_on"] = pd.to_datetime(first_observed["observed_on"])
    days_ago = datetime.now() - timedelta(days=days)
    last_days = first_observed[first_observed["observed_on"] >= days_ago]

    # Filtrar taxonomías no deseadas
    last_days = last_days[
        ~last_days.taxon_rank.isin(["kingdom", "phylum", "class"])
    ].reset_index(drop=True)

    # Agrupar por taxón icónico
    grouped_counts = (
        last_days.groupby("iconic_taxon").size().sort_values(ascending=False)
    )

    # Generar reporte
    text_report = ""
    for taxon, count in grouped_counts.items():
        text_report += f"""\n\n :green-background[**{count} {taxon}**]:\n"""

        # Filtrar observaciones del grupo actual
        group = last_days[last_days["iconic_taxon"] == taxon]
        for _, row in group.iterrows():
            taxon_name = row["taxon_name"]
            observation_id = row["id"]
            address = row["address"]
            text_report += f" - [{taxon_name}](https://minka-sdg.org/observations/{observation_id}) a {address}.\n"

    return text_report


# Cargar datos y crear primeras observaciones
df_obs = load_csv(f"{directory}/data/{main_project}_obs.csv")
df_sorted = df_obs.sort_values(by="observed_on").reset_index(drop=True)
first_observed = (
    df_sorted.drop_duplicates(subset=["taxon_name"], keep="first")
    .sort_values(by=["observed_on"], ascending=False)
    .reset_index(drop=True)
)


periods = {"7 dies": 7, "14 dies": 14, "1 mes": 30, "3 mesos": 90, "6 mesos": 180}

# Título
with st.container():
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(":blue[Destacats del projecte BioPlatgesMet]")
        st.markdown("")
        st.markdown("")
        st.markdown("")

# Período consultado
with st.container():
    col1, col2, col3 = st.columns([2, 1, 8])
    with col1:
        st.markdown("##### Període consultat:")

    with col2:
        option = st.selectbox(
            "## Període consultat:", (periods.keys()), label_visibility="collapsed"
        )


days = periods[option]

st.divider()

# Reporte de gatos y ratas: crear listado de especies
with st.container():
    titulo4 = f":blue[Alerta d'espècies monitoritzades]"
    st.subheader(titulo4)
    st.markdown(f"{get_message('alerta', df_obs, days, color='red')}")

st.divider()


# Reporte de especies de interés
with st.container():
    titulo1 = f":blue[Espècies d'interès registrades en els darrers {days} dies]"
    st.subheader(titulo1)

    st.markdown("##### **Espècies invasores:**")
    st.markdown(f"{get_message('invasoras', df_obs, days, color='orange')}")
    st.markdown("")

    st.markdown("##### **Espècies exòtiques:**")
    st.markdown(f"{get_message('exoticas', df_obs, days, color='orange')}")
    st.markdown("")

    st.markdown("##### **Espècies amenaçades:**")
    st.markdown(f"{get_message('amenazadas', df_obs, days, color='orange')}")
    st.markdown("")

    st.markdown("##### **Espècies protegides:**")
    st.markdown(f"{get_message('protegidas', df_obs, days, color='orange')}")
    st.markdown("")

st.divider()

# Nuevas especies: últimas especies que se han registrado por primera vez
with st.container():
    titulo3 = f":blue[Noves espècies registrades en els darrers {days} dies]"
    st.subheader(titulo3)

    text_report = generar_reporte_nuevas_especies(df_sorted, days)

    # Mostrar resultado
    if text_report:
        st.markdown(text_report)
    else:
        tabs = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        st.markdown(f"{tabs}:grey[Cap espècie registrada per primera vegada.]")

st.divider()

# Nuevos usuarios: mínimo suben una observación al proyecto, separada por municipio.
with st.container():
    titulo2 = f":blue[Participants incorporats al projecte en els darrers {days} dies]"
    st.subheader(titulo2)
    df_members = get_members_df(264)

    # Miembros creados en los últimos x días
    fecha_actual = date.today()
    limite = fecha_actual - timedelta(days=days)
    df_members.created_at = pd.to_datetime(df_members.created_at).dt.date
    members_last_month = df_members[df_members.created_at > limite]
    # Observaciones de cada nuevo miembro del proyecto si más de 0 observaciones
    for i, row in members_last_month.iterrows():
        # Filtrar observaciones del miembro actual
        user_obs = df_obs[df_obs.user_id == row.user_id]

        if len(user_obs) > 0:
            num_obs = len(user_obs)

            # Usar fillna('') para manejar valores NaN
            species = ", ".join(set(user_obs["taxon_name"].fillna("").to_list()))
            cities = ", ".join(set(user_obs["address"].fillna("").to_list()))

            st.markdown(
                f"* **:blue-background[[{row['user.login']}](https://minka-sdg.org/users/{row['user.login']})]**: {num_obs} observacion/s a {cities}"
            )

    # Mensaje si no hay nuevos usuarios
    if len(members_last_month) == 0:
        tabs = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        msg_users = f":gray[{tabs}Cap nou participant amb almenys una observació.]"
        st.markdown(msg_users)

    st.markdown("")
    st.markdown("")
    st.markdown("")


# Footer
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
