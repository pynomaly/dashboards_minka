import os
from datetime import datetime

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


# @st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


# @st.cache_data(ttl=360)
def get_observers(df_obs):
    df_users = pd.read_csv(f"{directory}/data/minka_accounts.csv")
    df_observers = (
        df_users[df_users.observations_count > 0].reset_index(drop=True).copy()
    )

    df_observers = df_observers[
        -df_observers["user_name"].isin(EXCLUDE_USERS)
    ].reset_index(drop=True)

    # Contar el número de observaciones con "web" y "app" por usuario
    obs_device_counts = (
        df_obs.groupby(["user_id", "device"]).size().unstack(fill_value=0)
    )

    # Renombrar columnas
    obs_device_counts = obs_device_counts.rename(
        columns={"web": "web_observations", "app": "app_observations"}
    )

    # Asegurar que ambas columnas existen (en caso de que no haya registros de un tipo)
    if "web_observations" not in obs_device_counts:
        obs_device_counts["web_observations"] = 0
    if "app_observations" not in obs_device_counts:
        obs_device_counts["app_observations"] = 0

    # Unir estos datos a "observers" por user_id
    df_observers = df_observers.merge(
        obs_device_counts, on="user_id", how="left"
    ).fillna(0)

    # Convertir a enteros (opcional)
    df_observers["web_observations"] = df_observers["web_observations"].astype(int)
    df_observers["app_observations"] = df_observers["app_observations"].astype(int)

    df_observers.loc[df_observers.web_observations == 0, "user_type"] = "pure_app"
    df_observers.loc[df_observers.app_observations == 0, "user_type"] = "pure_web"
    df_observers.loc[
        (df_observers.app_observations != 0) & (df_observers.web_observations != 0),
        "user_type",
    ] = "mixed_device"

    df_observers = df_observers[
        [
            "user_id",
            "user_name",
            "created_at",
            "observations_count",
            "identifications_count",
            "species_count",
            "web_observations",
            "app_observations",
            "user_type",
        ]
    ]

    return df_observers


def get_active_users(df_observers, df_obs, activity_period=365):
    # Obtener la fecha de referencia
    last_days = pd.Timestamp.today() - pd.Timedelta(days=activity_period)
    df_obs["created_at"] = pd.to_datetime(df_obs["created_at"])

    # Crear una lista con los usuarios que han subido observaciones en los últimos 365 días
    active_users = set(df_obs[df_obs["created_at"] >= last_days]["user_id"])

    # Crear la columna 'is_active' en observers (True si está en active_users, False si no)
    df_observers["is_active"] = df_observers["user_id"].isin(active_users)

    return df_observers


# @st.cache_data(ttl=360)
def create_users_period_df(df_observers, period):
    # Convertir la fecha de creación a datetime
    df_observers["created_at"] = pd.to_datetime(df_observers["created_at"])

    # Extraer el año
    if period == "year":
        df_observers["period"] = df_observers["created_at"].dt.year.astype(
            "Int64"
        )  # Soporta NaN sin convertir a float

    elif period == "month":
        df_observers["period"] = df_observers["created_at"].dt.to_period("M")

    # Contar el número de observadores creados por año
    df_observers_per_period = (
        df_observers.groupby("period")
        .agg(
            total_observers=("created_at", "size"),
            active_users=("is_active", lambda x: x.sum()),
            non_active_users=("is_active", lambda x: (~x).sum()),
            pure_web=("user_type", lambda x: (x == "pure_web").sum()),
            pure_app=("user_type", lambda x: (x == "pure_app").sum()),
            mixed_device=("user_type", lambda x: (x == "mixed_device").sum()),
        )
        .reset_index()
    )

    df_observers_per_period["period"] = df_observers_per_period["period"].astype(str)

    # Mostrar el resultado
    return df_observers_per_period


# Crear el selector de visualización
def create_radio_selector(key):
    visualization_type = st.radio(
        "Select visualization type",
        [
            "Total observers",
            "Active / Non active observers",
            "User device",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key=f"{key}_1",
    )
    return visualization_type


# Media de observaciones por usuario


# Función para crear el gráfico
def create_user_bar_chart(df, key, visualization_type, period="year"):

    # Configuración de gráficos según selección
    if visualization_type == "Total observers":
        max_value = df["total_observers"].max()
        fig = px.bar(
            df,
            x="period",
            y="total_observers",
            title=f"Total observers by {period}",
            text="total_observers",
            color_discrete_sequence=["#1f77b4"],  # Azul
        )

    elif visualization_type == "Active / Non active observers":
        max_value = max(df["active_users"].max(), df["non_active_users"].max())
        fig = px.bar(
            df,
            x="period",
            y=["active_users", "non_active_users"],
            title="Active vs Non Active Observers",
            labels={"value": "Number of users", "variable": "User type"},
            color_discrete_map={
                "active_users": "#1f77b4",  # Azul
                "non_active_users": "#d62728",  # Rojo
            },
            barmode="group",
            text_auto=True,
        )
        newnames = {"active_users": "Active", "non_active_users": "Non Active"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    elif visualization_type == "User device":
        max_value = max(
            df["pure_web"].max(), df["pure_app"].max(), df["mixed_device"].max()
        )
        fig = px.bar(
            df,
            x="period",
            y=["pure_web", "pure_app", "mixed_device"],
            title="Users by device",
            labels={"value": "Number of users", "variable": "Device"},
            color_discrete_map={
                "pure_web": "#1f77b4",  # Azul
                "pure_app": "#ff7f0e",  # Naranja
                "mixed_device": "#d62728",  # Rojo
            },
            barmode="group",
            text_auto=True,
        )
        newnames = {"pure_web": "Web", "pure_app": "App", "mixed_device": "Both"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    # Configurar el eje X para mostrar correctamente los períodos
    fig.update_xaxes(
        tickmode="array",
        tickvals=df["period"].unique(),
        ticktext=df["period"].astype(str),
    )

    # Ajustar layout y etiquetas
    fig.update_layout(
        xaxis_title="Period",
        yaxis_title="Number of Users",
        bargap=0.2,
        bargroupgap=0.1,
        showlegend=True if visualization_type != "Total observers" else False,
        yaxis=dict(range=[0, max_value * 1.1]),
    )

    # Ajustar la posición de las etiquetas de las barras
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=12),
        texttemplate="%{y:,.0f}",
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_2")

    # Agregar botón de descarga de datos
    data_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download data",
        data=data_csv,
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"{key}_3",
    )


def get_avg_per_user(df_obs, period="M"):
    """
    Crea un dataset con el periodo y la media de observaciones por usuario en cada periodo.
    Parámetros:
    df_obs (DataFrame): Dataset con columnas 'user_login' y 'created_at'.
    period (str): Frecuencia de agregación ('D' = diario, 'W' = semanal, 'M' = mensual).
    Retorna:
    DataFrame con 'period' y 'avg_observations'.
    """
    # Asegurar que created_at es de tipo datetime
    df_obs["created_at"] = pd.to_datetime(df_obs["created_at"])

    # Contar observaciones por usuario en cada periodo
    df_user_period = (
        df_obs.groupby([df_obs["created_at"].dt.to_period(period), "user_login"])
        .size()
        .reset_index(name="observations")
    )
    # Calcular la media de observaciones por usuario en cada periodo
    df_period_mean = (
        df_user_period.groupby("created_at")["observations"].mean().reset_index()
    )
    # Renombrar columnas para mayor claridad
    df_period_mean = df_period_mean.rename(
        columns={"created_at": "period", "observations": "avg_observations"}
    )
    df_period_mean["avg_observations"] = round(df_period_mean["avg_observations"], 2)
    return df_period_mean


def create_user_line_chart(df, key):

    df["period"] = df["period"].astype(str)

    # Configuración de gráficos según selección
    max_value = df["avg_observations"].max()

    fig = px.bar(
        df,
        x="period",
        y="avg_observations",
        title=f"Average number of observations by user",
        text="avg_observations",
        color_discrete_sequence=["#1f77b4"],  # Azul
    )

    fig.update_layout(
        xaxis_title="Period",
        yaxis_title="Average number of observations",
        showlegend=False,
        yaxis=dict(range=[0, max_value * 1.15]),
        margin=dict(b=100),
    )
    fig.update_traces(
        hovertemplate="<b>Period:</b> %{x}<br>"
        + "<b>Average observations:</b> %{y:,.2f}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True, key=f"{key}_line")


if __name__ == "__main__":

    # st.markdown("**Users excluded**")
    st.markdown(f'**Excluded users**: :gray[{", ".join(EXCLUDE_USERS)}]')

    # Carga de observaciones
    # Eliminamos observaciones importadas y de cuentas excluidas
    if "df_obs" not in st.session_state or st.session_state.df_obs is None:
        df_obs = pd.read_csv(f"{directory}/data/minka_obs.csv")
        df_obs_filtered = df_obs[df_obs.imported == False]
        df_obs_filtered = df_obs_filtered[
            -df_obs_filtered.user_login.isin(EXCLUDE_USERS)
        ].copy()
        st.session_state.df_obs = df_obs_filtered

    # Extracción de observadores
    st.markdown("**Period of days to be considered active an user:**")
    col1, col2 = st.columns([1, 10])
    with col1:
        activity_period = st.number_input(
            "Period of days to be considered active an user:",
            value=365,
            placeholder="Type a number...",
            label_visibility="collapsed",
        )

    # Excluye usuarios del listado
    df_observers = get_observers(st.session_state.df_obs)

    df_observers = get_active_users(
        df_observers, st.session_state.df_obs, activity_period=activity_period
    )
    df_observers["created_at"] = pd.to_datetime(df_observers["created_at"]).dt.date

    # Df agrupados por año
    df_observers_per_year = create_users_period_df(df_observers, period="year")

    selected_visualization = create_radio_selector("user_chart")
    create_user_bar_chart(
        df_observers_per_year, "observers_by_year", selected_visualization
    )

    # Df agrupados por mes
    df_observers_per_month = create_users_period_df(df_observers, period="month")
    create_user_bar_chart(
        df_observers_per_month,
        "observers_by_month",
        selected_visualization,
        period="month",
    )

    # Media de observaciones por usuario
    st.header("Average observations by user")
    period_chart = st.radio(
        "Period selecter",
        ["year", "month"],
        key="period_chart",
    )
    if period_chart == "year":
        df_avg = get_avg_per_user(st.session_state.df_obs, period="Y")

    elif period_chart == "month":
        df_avg = get_avg_per_user(st.session_state.df_obs, period="M")

    create_user_line_chart(df_avg, "avg_obs_by_user_yearly")

    # Total tables to download
    st.header("Observers (users with at least one observation):")

    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        current_year = datetime.now().year
        years = [""] + [str(year) for year in range(2022, current_year + 1)]
        year_option = st.selectbox(
            "Accounts created in this year:",
            years,
        )
    with col2:
        month_option = st.selectbox(
            "Accounts created in this month:",
            [""] + [str(month) for month in range(1, 13)],
        )
    with col3:
        type_option = st.selectbox(
            "Accounts by type:",
            ["", "pure_web", "pure_app", "mixed_device"],
        )
    with col4:
        active_option = st.selectbox(
            "Account is active:",
            ["", "YES", "NO"],
        )

    df_result = df_observers.copy()
    if year_option != "":
        df_result = df_result[df_result["created_at"].dt.year == int(year_option)]
    if month_option != "":
        df_result = df_result[df_result["created_at"].dt.month == int(month_option)]
    if type_option != "":
        df_result = df_result[df_result["user_type"] == type_option]
    if active_option != "":
        df_result = df_result[df_result["is_active"] == (active_option == "YES")]

    st.markdown(f"**Number of observers**: {df_result.shape[0]}")
    if df_result.shape[0] > 0:
        avg_observations = round(
            df_result["observations_count"].sum() / df_result.shape[0], 2
        )
        st.markdown(
            f"**Average number of observations uploaded by observer**: {avg_observations}"
        )
        avg_species = round(df_result["species_count"].sum() / df_result.shape[0], 2)
        st.markdown(f"**Average number of species observed**: {avg_species}")
        avg_identifications = round(
            df_result["identifications_count"].sum() / df_result.shape[0], 2
        )
        st.markdown(f"**Average number of identifications**: {avg_identifications}")

        st.dataframe(
            df_result.drop(columns=["period"]).assign(
                is_active=df_observers["is_active"].map({True: "YES", False: "NO"}),
                created_at=df_observers["created_at"].dt.date,
            ),
            hide_index=True,
            height=300,
        )
