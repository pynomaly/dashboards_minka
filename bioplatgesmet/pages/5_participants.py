import math
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from utils import get_count_hour_per_day, heatmap_day_hour

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


colors = ["#009DE0", "#0081B8", "#00567A", "#3b4a7f"]
main_project = 264
excluded = ["anomalia", "verificador_1", "jaume-piera", "carlosrodero"]


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data(ttl=3600)
def load_csv(file_path):
    return pd.read_csv(file_path)


def get_members_df(id_project):
    session = requests.Session()
    total_results = []
    url = f"https://api.minka-sdg.org/v1/projects/{id_project}/members"
    total = session.get(url).json()["total_results"]
    for i in range(1, math.ceil(total / 100) + 1):
        url = f"https://api.minka-sdg.org/v1/projects/{id_project}/members?per_page=100&page={i}"
        results = requests.get(url).json()["results"]
        total_results.extend(results)
    df_members = pd.json_normalize(total_results)
    df_members.drop(columns=["observations_count"], inplace=True)
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


def get_members_no_obs(df_observers, excluded):
    df_none = df_observers[df_observers.observation_count.isnull()].reset_index(
        drop=True
    )
    df_none = df_none[~df_none["user.login"].isin(excluded)]

    # Convierte created_at en un campo de fecha
    df_none["created_at"] = pd.to_datetime(df_none["created_at"])

    # Extrae el año y el mes de created_at
    df_none["year_month"] = df_none["created_at"].dt.strftime("%m-%Y")

    # Agrupa por 'year_month' y une los nombres de usuario como enlaces Markdown
    grouped = (
        df_none.groupby("year_month")["user.login"]
        .apply(
            lambda x: ", ".join(
                [f"[{name}](https://minka-sdg.org/users/{name})" for name in x.dropna()]
            )
        )
        .reset_index()
    )

    # Convierte 'year_month' al tipo de fecha para ordenar correctamente
    grouped["year_month_date"] = pd.to_datetime(grouped["year_month"], format="%m-%Y")
    grouped = grouped.sort_values("year_month_date", ascending=False)

    # Convierte a diccionario con el formato deseado
    result = {row["year_month"]: row["user.login"] for _, row in grouped.iterrows()}

    return result


def evolution_monthly_bars_by_user(df_obs, user_login):
    # Supongamos que `df_obs` es tu DataFrame
    # Asegúrate de que 'observed_on' sea un campo de fecha
    df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])

    # Extrae el año y mes de 'observed_on' en formato "AAAA-MM" para agrupar
    df_obs["year_month"] = df_obs["observed_on"].dt.to_period("M").astype(str)

    # Filtra por el nombre de usuario deseado, por ejemplo, 'nombre_usuario'
    df_usuario = df_obs[df_obs["user_login"] == user_login]

    # Encuentra el rango de fechas para el usuario específico
    mes_inicio = df_usuario["observed_on"].min().to_period("M")
    mes_fin = df_usuario["observed_on"].max().to_period("M")

    # Genera un rango completo de meses desde la primera hasta la última observación del usuario
    todos_los_meses_usuario = pd.DataFrame(
        {"year_month": pd.period_range(mes_inicio, mes_fin, freq="M").astype(str)}
    )

    # Cuenta el número de observaciones por cada mes para el usuario
    observaciones_por_mes = (
        df_usuario.groupby("year_month").size().reset_index(name="observaciones")
    )

    # Combina el rango completo de meses del usuario con las observaciones, llenando los meses sin observaciones con 0
    observaciones_completas = todos_los_meses_usuario.merge(
        observaciones_por_mes, on="year_month", how="left"
    ).fillna(0)

    # Convierte la columna 'observaciones' a entero
    observaciones_completas["observaciones"] = observaciones_completas[
        "observaciones"
    ].astype(int)

    # Crea el gráfico de barras
    fig = px.bar(
        observaciones_completas,
        x="year_month",
        y="observaciones",
        title=f"Observacions mensuals de {user_login}",
        labels={"year_month": "Mes", "observaciones": "Nombre d'observacions"},
    )

    # Configura la apariencia del eje x para que los meses se muestren en orden cronológico
    fig.update_xaxes(type="category", categoryorder="category ascending")
    fig.update_yaxes(tickfont_size=12, automargin=True)
    fig.update_traces(
        # marker_color=["#f9b853", "#dc6619", "#089aa2"],
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=13,
        textposition="inside",
    )
    fig.update_layout(
        width=600,
        height=400,
        plot_bgcolor="#F3F5F7",
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white", font_size=15),
        showlegend=False,
    )
    # Muestra el gráfico
    return fig


def get_active_users_per_month(df_obs):
    # Asegúrate de que 'observed_on' sea un campo de fecha
    df_obs["observed_on"] = pd.to_datetime(df_obs["observed_on"])

    # Extrae el año y mes de 'observed_on' en formato "AAAA-MM" para agrupar
    df_obs["year_month"] = df_obs["observed_on"].dt.to_period("M").astype(str)

    # Agrupa por 'year_month' y cuenta los usuarios únicos que han subido observaciones en cada mes
    usuarios_por_mes = (
        df_obs.groupby("year_month")["user_login"]
        .nunique()
        .reset_index(name="usuarios_distintos")
    )

    # Crea el gráfico de barras
    fig = px.bar(
        usuarios_por_mes,
        x="year_month",
        y="usuarios_distintos",
        title="",
        labels={
            "year_month": "Mes",
            "usuarios_distintos": "Nombre d'usuaris diferents",
        },
    )

    # Configura la apariencia del eje x para que los meses se muestren en orden cronológico
    fig.update_xaxes(type="category", categoryorder="category ascending")
    fig.update_yaxes(
        tickfont_size=12,
        automargin=True,
    )
    fig.update_traces(
        # marker_color=["#f9b853", "#dc6619", "#089aa2"],
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=13,
        textposition="inside",
    )
    fig.update_layout(
        width=600,
        height=400,
        plot_bgcolor="#F3F5F7",
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="",
        separators=". ",
        hoverlabel=dict(bgcolor="white", font_size=15),
        showlegend=False,
    )
    # Muestra el gráfico
    return fig


def get_users_days(df_obs):
    df_days = (
        df_obs.groupby("user_login")["observed_on"]
        .nunique()
        .to_frame()
        .reset_index()
        .sort_values(by="observed_on", ascending=False)
    )
    df_result = (
        df_days["observed_on"]
        .value_counts()
        .reset_index()
        .rename(columns={"observed_on": "nombre_dies", "count": "participants"})
    )

    df_result["days_range"] = df_result["nombre_dies"].apply(classify_days)

    range_sums = df_result.groupby("days_range")["participants"].sum().reset_index()

    return range_sums


def classify_days(days):
    if days == 1:
        return "1 dia"
    elif 2 <= days <= 5:
        return "2-5 dies"
    else:
        return "> 5 dies"


def get_bars(range_sums):
    # Ordenamos los datos de mayor a menor según "participants"
    range_sums["days_range"] = pd.Categorical(
        range_sums["days_range"],
        categories=["1 dia", "2-5 dies", "> 5 dies"],
        ordered=True,
    )

    # Creamos el gráfico
    fig = px.bar(
        range_sums,
        x="days_range",
        y="participants",
        text_auto=True,
        labels={"days_range": "Nombre de dies", "user_count": "Nombre d'usuaris"},
        title="",
    )

    # Ajustamos el diseño del gráfico
    fig.update_traces(
        # marker_color=["#f9b853", "#dc6619", "#089aa2"],
        marker_line_color="#08306b",
        marker_line_width=2,
        textfont_size=13,
        textposition="inside",
    )
    fig.update_layout(
        width=600,
        height=400,
        plot_bgcolor="#F3F5F7",
        paper_bgcolor="white",
        font_color="rgb(8,48,107)",
        xaxis_title="",
        yaxis_title="Nombre d'usuaris",
        showlegend=False,
    )

    # Mostramos el gráfico
    return fig


# Header
with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(":blue[Anàlisi de la participació]")


users = load_csv(f"{directory}/data/{main_project}_participants.csv")
users["url"] = users["participant"].apply(lambda x: f"https://minka-sdg.org/users/{x}")

# Ranking de usuarios por num_observaciones, num_identificaciones y num_especies
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "#### Usuaris per nombre d'observacions, identificacions i espècies"
        )
        st.dataframe(
            users[["url", "observacions", "identificacions", "espècies"]],
            column_config={
                "url": st.column_config.LinkColumn(
                    "participant",
                    display_text=r"https://minka-sdg.org/users/(.*?)$",
                    width=250,
                ),
                "observacions": st.column_config.NumberColumn(width=100),
                "identificacions": st.column_config.NumberColumn(width=100),
                "espècies": st.column_config.NumberColumn(width=100),
            },
            hide_index=True,
        )
    with col2:
        st.markdown(
            "#### Usuaris que s'han unit al projecte però no han pujat cap observació"
        )
        df_observers = get_members_df(264)
        result = get_members_no_obs(df_observers, excluded)
        # Muestra el resultado
        for month, names in result.items():
            st.markdown(f"**{month}**: {names}")

st.divider()
# observaciones activos por mes
st.header("Nombre d'usuaris diferents que han pujat observacions per mes")
df_obs = load_csv(f"{directory}/data/{main_project}_obs.csv")

fig_active_users = get_active_users_per_month(df_obs)

st.plotly_chart(fig_active_users, config=config_modebar, use_container_width=True)

st.divider()

# número de días que han subido observaciones
st.header("Distribució d'usuaris per rangs de dies amb observacions")
range_sums = get_users_days(df_obs)

fig_days_per_user = get_bars(range_sums)
st.plotly_chart(fig_days_per_user, config=config_modebar, use_container_width=True)

st.markdown("Llistat d'usuaris en cada grup")
range_groups = [""] + range_sums["days_range"].unique().tolist()

col1, col2 = st.columns([1, 8])
with col1:
    user_group = st.selectbox("## Grup:", (range_groups), label_visibility="collapsed")

with col2:
    df_days = (
        df_obs.groupby("user_login")["observed_on"]
        .nunique()
        .to_frame()
        .reset_index()
        .sort_values(by="observed_on", ascending=False)
    )
    if user_group == "1 dia":
        list_users = df_days.loc[df_days.observed_on == 1, "user_login"].to_list()
        list_users.sort()
    elif user_group == "2-5 dies":
        list_users = df_days.loc[
            df_days.observed_on.isin([2, 3, 4, 5]), "user_login"
        ].to_list()
    elif user_group == "> 5 dies":
        list_users = df_days.loc[df_days.observed_on >= 5, "user_login"].to_list()
    else:
        list_users = ""
    list_users_links = [
        f"[{user}](https://minka-sdg.org/users/{user})" for user in list_users
    ]
    st.markdown(", ".join(list_users_links))

st.divider()


# observaciones por día de la semana y hora del día
counts_day_hour = get_count_hour_per_day(df_obs)

st.header("Distribució per hora i dia")
fig_heatmap = heatmap_day_hour(counts_day_hour)
st.plotly_chart(fig_heatmap, config=config_modebar, use_container_width=True)

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
