import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    directory = f"{os.environ['DASHBOARDS']}/internal-analytics"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Internal KPIs MINKA",
)

# variables
API_PATH = "https://api.minka-sdg.org/v1"
CATALUNYA_PLACE = 374
EXCLUDE_USERS = [
    "xasalva",
    "bertinhaco",
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "irodero",
    "anomalia",
    "aluna",
    "carlosrodero",
    "lydia",
    "elibonfill",
    "marinatorresgi",
    "meri",
    "verificador_1",
    "loreto_rodriguez",
    "minkatutor",
    "minkatest",
    "anonimousminkacontributor",
    "minkauser10",
    "test_minka_athens",
    "infominka",
    "admin",
]


# funciones


@st.cache_data(ttl=360)
def create_obs_grouped_df(df_projects, period="year"):
    # Convertir la columna de fecha a datetime
    df_projects["created_at"] = pd.to_datetime(df_projects["created_at"])

    if period == "year":
        # Extraer el año
        df_projects["year"] = df_projects["created_at"].dt.year

        # Agrupar por año y calcular los KPIs adicionales
        df_grouped = (
            df_projects.groupby("year")
            .agg(
                total_projects=("project_id", "count"),
                active=("is_active", lambda x: x.sum()),  # Proyectos activos
                not_active=(
                    "is_active",
                    lambda x: x.count() - x.sum(),
                ),  # Inactivos = Total - Activos
                embimos=("embimos", lambda x: x.sum()),
                not_embimos=("embimos", lambda x: (~x).sum()),
            )
            .reset_index()
        )

    elif period == "quarter":
        # Extraer año y trimestre
        df_projects["year"] = df_projects["created_at"].dt.year
        df_projects["quarter"] = df_projects["created_at"].dt.quarter

        # Agrupar por año y trimestre y calcular los KPIs
        df_grouped = (
            df_projects.groupby(["year", "quarter"])
            .agg(
                total_projects=("project_id", "count"),  # Total de proyectos
                active=("is_active", lambda x: x.sum()),  # Proyectos activos (True)
                non_active=(
                    "is_active",
                    lambda x: (~x).sum(),
                ),  # Proyectos inactivos (False)
                embimos=("embimos", lambda x: x.sum()),
                not_embimos=("embimos", lambda x: (~x).sum()),
            )
            .reset_index()
        )

    # Mostrar resultado
    return df_grouped


if __name__ == "__main__":
    if "df_project" not in st.session_state or st.session_state.df_project is None:
        df_project = pd.read_csv(f"{directory}/data/minka_projects.csv")
        st.session_state.df_project = df_project

    # Project Retention Rate or active projects
    st.markdown("**Period of days to be considered active a project:**")
    col1, col2 = st.columns([1, 10])
    with col1:
        activity_period = st.number_input(
            "Period of days to be considered active a project:",
            value=365,
            placeholder="Type a number...",
            label_visibility="collapsed",
        )

    st.session_state.df_project["last_observation"] = pd.to_datetime(
        st.session_state.df_project["last_observation"]
    )
    st.session_state.df_project["is_active"] = st.session_state.df_project[
        "last_observation"
    ] > datetime.now() - timedelta(days=activity_period)

    st.session_state.df_project["embimos"] = st.session_state.df_project["admin"].isin(
        EXCLUDE_USERS
    )

    st.header("Projects created by year")
    df_year = create_obs_grouped_df(st.session_state.df_project, period="year")

    fig_year = px.bar(
        df_year,
        x=df_year["year"].astype(str),
        y=["total_projects", "active", "not_active"],
        color_discrete_map={
            "total_projects": "#1f77b4",
            "active": "#2ca02c",
            "not_active": "#d62728",
        },
        labels={"value": "Number of projects", "variable": "Project type"},
        barmode="group",
        text_auto=True,
    )
    fig_year.update_traces(
        textposition="outside",
        textfont=dict(size=12),
        texttemplate="%{y:,.0f}",
    )

    # Mostrar gráfico en Streamlit
    st.plotly_chart(fig_year)

    st.header("Projects created quarterly")
    df_quarter = create_obs_grouped_df(st.session_state.df_project, period="quarter")
    fig_quarter = px.bar(
        df_quarter,
        x=df_quarter["year"].astype(str) + "-Q" + df_quarter["quarter"].astype(str),
        y=["total_projects", "active", "non_active"],
        labels={"value": "Number of projects", "variable": "Project type"},
        barmode="group",
        text_auto=True,
        color_discrete_map={
            "total_projects": "#1f77b4",
            "active": "#2ca02c",
            "non_active": "#d62728",
        },
    )
    fig_quarter.update_traces(
        textposition="outside",
        textfont=dict(size=12),
        texttemplate="%{y:,.0f}",
    )
    st.plotly_chart(fig_quarter, key="fig_quarter")

    st.header("Projects created by users EMBIMOS vs. not EMBIMOS quarterly")
    df_quarter["not_embimos"] = df_quarter["total_projects"] - df_quarter["embimos"]
    fig_embimos = px.bar(
        df_quarter,
        x=df_quarter["year"].astype(str) + "-Q" + df_quarter["quarter"].astype(str),
        y=["embimos", "not_embimos"],
        labels={"value": "Number of projects", "variable": "Project type"},
        barmode="group",
        text_auto=True,
        color_discrete_map={
            "embimos": "#1f77b4",
            "not_embimos": "#2ca02c",
        },
    )
    fig_embimos.update_traces(
        textposition="outside",
        textfont=dict(size=12),
        texttemplate="%{y:,.0f}",
    )
    st.plotly_chart(fig_embimos, key="fig_quarter_embimos")

    st.header("Total projects created in MINKA")

    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    with col1:
        current_year = datetime.now().year
        years = [""] + [str(year) for year in range(2022, current_year + 1)]
        year_option = st.selectbox(
            "Year:",
            years,
        )
    with col2:
        quarter_option = st.selectbox(
            "Quarter:",
            ("", "1", "2", "3", "4"),
        )
    with col3:
        filter_option = st.selectbox(
            "Filter:",
            (
                "Total projects",
                "Active projects",
                "Not active projects",
                "EMBIMOS",
                "Not EMBIMOS",
            ),
        )
    with col4:
        list_users = [""] + sorted(st.session_state.df_project["admin"].unique())
        user_name = st.selectbox("Creator of the project", list_users)

    print(st.session_state.df_project.columns)
    df_result = st.session_state.df_project.copy()
    if year_option != "":
        df_result = df_result[df_result["created_at"].dt.year == int(year_option)]
    if quarter_option != "":
        df_result = df_result[df_result["created_at"].dt.quarter == int(quarter_option)]
    if filter_option != "Total projects":
        if filter_option == "Active projects":
            df_result = df_result[df_result["is_active"]]
        elif filter_option == "Not active projects":
            df_result = df_result[~df_result["is_active"]]
        elif filter_option == "EMBIMOS":
            df_result = df_result[df_result["embimos"]]
        elif filter_option == "Not EMBIMOS":
            df_result = df_result[~df_result["embimos"]]
    if user_name != "":
        df_result = df_result[df_result["admin"] == user_name]

    st.markdown(f"**Number of projects:** {df_result.shape[0]}")
    df_result["project_url"] = f"https://minka-sdg.org/projects/" + df_result[
        "project_id"
    ].astype(str)
    st.dataframe(
        df_result[
            [
                "project_url",
                "project_name",
                "project_description",
                "created_at",
                "updated_at",
                "project_type",
                "admin",
                "num_observations",
                "num_observers",
                "num_species",
                "last_observation",
                "is_active",
                "embimos",
            ]
        ].assign(
            created_at=st.session_state.df_project["created_at"].dt.date,
            last_observation=st.session_state.df_project["last_observation"].dt.date,
            is_active=st.session_state.df_project["is_active"].map(
                {True: "YES", False: "NO"}
            ),
            embimos=st.session_state.df_project["embimos"].map(
                {True: "YES", False: "NO"}
            ),
        ),
        column_config={
            "project_url": st.column_config.LinkColumn(
                "Project ID",
                display_text=r"https://minka-sdg.org/projects/(.*?)$",
            )
        },
        height=500,
        hide_index=True,
    )
