import calendar
import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
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


def get_identifiers_by_period(period, type="unique"):
    session = requests.Session()

    if type == "unique":
        # year
        if len(str(period).split("-")) == 1:
            year = str(period).split("-")[0]
            url_identifiers = f"https://api.minka-sdg.org/v1/observations/identifiers?created_d1={year}-01-01&created_d2={year}-12-31"
            response = session.get(url_identifiers)

        # year-month
        if len(str(period).split("-")) == 2:
            year = str(period).split("-")[0]
            month = str(period).split("-")[1]
            _, last_day = calendar.monthrange(int(year), int(month))

            start_date = f"{year}-{month}-01"
            end_date = f"{year}-{month}-{last_day}"

            url_identifiers = f"https://api.minka-sdg.org/v1/observations/identifiers?created_d1={start_date}&created_d2={end_date}"
            response = session.get(url_identifiers)

        if response.status_code == 200:
            results = response.json()["results"]
            identifiers = []
            for result in results:
                data = {}
                data["identifier_id"] = result["user_id"]
                data["identifier_name"] = result["user"]["login"]
                data["number_identifications"] = result["count"]
                data["created_at"] = result["user"]["created_at"]
                identifiers.append(data)
            identifiers_df = pd.DataFrame(identifiers)
            identifiers_df = identifiers_df[
                identifiers_df.identifier_name.isin(EXCLUDE_USERS) == False
            ].reset_index(drop=True)
            return len(identifiers_df)

        else:
            print(f"Error fetching data for {period}")
            return None
    elif type == "cumulative":
        # year
        if len(str(period).split("-")) == 1:
            year = str(period).split("-")[0]
            url_identifiers = f"https://api.minka-sdg.org/v1/observations/identifiers?created_d2={year}-12-31"
            response = session.get(url_identifiers)

        # year-month
        if len(str(period).split("-")) == 2:
            year = str(period).split("-")[0]
            month = str(period).split("-")[1]
            _, last_day = calendar.monthrange(int(year), int(month))

            end_date = f"{year}-{month}-{last_day}"

            url_identifiers = f"https://api.minka-sdg.org/v1/observations/identifiers?created_d2={end_date}"
            response = session.get(url_identifiers)

        if response.status_code == 200:
            results = response.json()["results"]
            identifiers = []
            for result in results:
                data = {}
                data["identifier_id"] = result["user_id"]
                data["identifier_name"] = result["user"]["login"]
                data["number_identifications"] = result["count"]
                data["created_at"] = result["user"]["created_at"]
                identifiers.append(data)
            identifiers_df = pd.DataFrame(identifiers)
            identifiers_df = identifiers_df[
                identifiers_df.identifier_name.isin(EXCLUDE_USERS) == False
            ].reset_index(drop=True)
            return len(identifiers_df)

        else:
            print(f"Error fetching data for {period}")
            return None


def create_user_bar_chart(df, key):
    max_value = df["identifiers"].max()
    fig = px.bar(
        df,
        x="period",
        y="identifiers",
        text="identifiers",
        color_discrete_sequence=["#1f77b4"],  # Blue
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=df["period"].unique(),
        ticktext=df["period"].astype(str),
    )

    # Ajustar layout y etiquetas
    fig.update_layout(
        xaxis_title="Period",
        yaxis_title="Number of identifiers",
        bargap=0.2,
        bargroupgap=0.1,
        showlegend=False,
        yaxis=dict(range=[0, max_value * 1.1]),
    )

    # Ajustar la posición de las etiquetas de las barras
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=12),
        texttemplate="%{y:,.0f}",
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig, use_container_width=True, key=f"identifiers_bars_plot")

    # Agregar botón de descarga de datos
    data_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download data",
        data=data_csv,
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"{key}_csv",
    )


def create_user_line_chart(df, key, y_column="identifiers", top_users=None):
    max_value = df[y_column].max()

    # Verificar si estamos usando formato mensual o anual
    is_monthly = "-" in str(df.loc[0, "period"])

    fig = go.Figure()

    if is_monthly:
        # CASO MENSUAL
        # Crear lista completa de meses desde 2022-04 hasta el mes actual
        full_range = pd.date_range(
            start="2022-04-01", end=pd.Timestamp.now(), freq="MS"
        ).strftime("%Y-%m")

        # Asegurar que 'period' esté ordenado correctamente como categoría global
        df["period"] = pd.Categorical(df["period"], categories=full_range, ordered=True)

        # Establecer el orden categórico si tenemos top_users
        if top_users is not None and "user.login" in df.columns:
            df["user.login"] = pd.Categorical(
                df["user.login"], categories=top_users, ordered=True
            )

        # Si hay múltiples usuarios, crear una línea para cada uno en el orden correcto
        if "user.login" in df.columns and top_users is not None:
            colors = px.colors.qualitative.Set1

            for i, user in enumerate(top_users):
                user_data = df[df["user.login"] == user].sort_values("period")

                if not user_data.empty:
                    color_idx = i % len(colors)

                    fig.add_trace(
                        go.Scatter(
                            x=user_data["period"],
                            y=user_data[y_column],
                            mode="lines+markers+text",
                            name=user,
                            line=dict(color=colors[color_idx]),
                            text=user_data[y_column],
                            textposition="top center",
                            texttemplate="%{y:,.0f}",
                        )
                    )
        else:
            # Para un solo usuario
            fig.add_trace(
                go.Scatter(
                    x=df.sort_values("period")["period"],
                    y=df.sort_values("period")[y_column],
                    mode="lines+markers+text",
                    text=df.sort_values("period")[y_column],
                    textposition="top center",
                    texttemplate="%{y:,.0f}",
                )
            )

        # Ajustar ejes X para mostrar todos los meses
        fig.update_xaxes(tickmode="array", tickvals=full_range, ticktext=full_range)

    else:
        # CASO ANUAL - Simple gráfico de línea para totales por año
        # Ordenar por año para asegurar que los años aparezcan cronológicamente
        df_sorted = df.sort_values("period")

        fig.add_trace(
            go.Scatter(
                x=df_sorted["period"],
                y=df_sorted[y_column],
                mode="lines+markers+text",
                line=dict(
                    color="rgb(31, 119, 180)", width=3
                ),  # Color azul más destacado
                marker=dict(size=10),  # Marcadores más grandes
                text=df_sorted[y_column],
                textposition="top center",
                texttemplate="%{y:,.0f}",
            )
        )

        # Configurar el eje X para datos anuales
        years = df_sorted["period"].tolist()
        fig.update_xaxes(tickmode="array", tickvals=years, ticktext=years)

    # Ajustar layout y etiquetas (común para ambos casos)
    fig.update_layout(
        xaxis_title="Period",
        yaxis_title=f"Number of {y_column}",
        showlegend=(
            "user.login" in df.columns and is_monthly
        ),  # Solo mostrar leyenda en caso mensual con múltiples usuarios
        yaxis=dict(range=[0, max_value * 1.1]),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig, use_container_width=True, key=f"{y_column}_line_plot")

    # Agregar botón de descarga de datos
    data_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download data",
        data=data_csv,
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"{key}_csv",
    )


def plot_observations_vs_identifications(df):
    df2 = df[-df.user_name.isin(EXCLUDE_USERS)]

    fig = px.scatter(
        df2,
        x="observations_count",
        y="identifications_count",
        hover_name="user_name",
        color="species_count",
        trendline="ols",
        labels={
            "observations_count": "Observations",
            "identifications_count": "Identifications",
            "species_count": "Species observed",
        },
        opacity=0.6,
        height=700,
    )

    # Modificar el color de la línea de tendencia
    for trace in fig.data:
        if trace.mode == "lines":  # La línea de tendencia
            trace.line.color = "red"  # O cualquier color: 'blue', '#00cc96', etc.
            trace.line.width = 1  # Opcional: más gruesa
    st.plotly_chart(fig, use_container_width=True, key=f"scatter_obs_ids")


# A partir de un usuario, sacar las identificaciones que ha hecho por mes / año


if __name__ == "__main__":

    # st.markdown("**Users excluded**")
    st.markdown(f'**Excluded users**: :gray[{", ".join(EXCLUDE_USERS)}]')

    df_identifiers = pd.read_csv(f"{directory}/data/minka_identifiers.csv")
    df_identifiers["last_identification"] = pd.to_datetime(
        df_identifiers["last_identification"]
    )

    st.markdown(f"**Total number of identifiers**: {len(df_identifiers)}")

    st.header("Number of unique identifiers by period")

    # Selector de periodo
    period_selected = st.radio(
        "Selection",
        ["year", "month"],
        label_visibility="collapsed",
        key="unique_selector",
    )

    # Dataframe por año
    if period_selected == "year":
        if "df_year" not in st.session_state or st.session_state.df_year is None:
            current_year = datetime.now().year
            df_year = pd.DataFrame({"period": list(range(2022, current_year + 1))})
            df_year["identifiers"] = df_year["period"].apply(get_identifiers_by_period)
            st.session_state.df_year = df_year
        create_user_bar_chart(st.session_state.df_year, key="identifiers_by_year")

    # Dataframe por mes
    elif period_selected == "month":
        if "df_month" not in st.session_state or st.session_state.df_month is None:
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m")
            date_range = pd.date_range(start="2022-04", end=end_date, freq="ME")
            year_month = [date.strftime("%Y-%m") for date in date_range]
            df_month = pd.DataFrame({"period": year_month})
            df_month["identifiers"] = df_month["period"].apply(
                get_identifiers_by_period
            )
            st.session_state.df_month = df_month
        create_user_bar_chart(st.session_state.df_month, key="identifiers_by_month")

    # Evolución en número de usuarios
    st.header("Unique identifiers in MINKA")

    # Acumulativo por año
    if period_selected == "year":
        if (
            "df_year_cumulative" not in st.session_state
            or st.session_state.df_year_cumulative is None
        ):
            current_year = datetime.now().year
            df_year_cumulative = pd.DataFrame(
                {"period": list(range(2022, current_year + 1))}
            )

            df_year_cumulative["identifiers"] = df_year_cumulative["period"].apply(
                lambda x: get_identifiers_by_period(x, "cumulative")
            )
            st.session_state.df_year_cumulative = df_year_cumulative

        create_user_line_chart(
            st.session_state.df_year_cumulative, key="identifiers_by_year_cumulative"
        )

    # Dataframe por mes
    elif period_selected == "month":
        if (
            "df_month_cumulative" not in st.session_state
            or st.session_state.df_month_cumulative is None
        ):
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m")
            date_range = pd.date_range(start="2022-04", end=end_date, freq="ME")
            year_month = [date.strftime("%Y-%m") for date in date_range]
            df_month_cumulative = pd.DataFrame({"period": year_month})
            df_month_cumulative["identifiers"] = df_month_cumulative["period"].apply(
                lambda x: get_identifiers_by_period(x, "cumulative")
            )
            st.session_state.df_month_cumulative = df_month_cumulative
        create_user_line_chart(
            st.session_state.df_month_cumulative, key="identifiers_by_month_cumulative"
        )

    # Identifications by user name
    st.header("Identifications by user name")
    df_identifications = pd.read_csv(f"{directory}/data/minka_identifications.csv")
    print(df_identifications.columns)
    df_identifications = df_identifications.sort_values(
        by="id", ascending=True
    ).reset_index(drop=True)
    df_identifications["created_at"] = pd.to_datetime(
        df_identifications["created_at"], utc=True
    )

    identifiers_name = [""] + sorted(df_identifications["user.login"].unique())

    col1, col2 = st.columns([1, 3])
    with col1:
        user_login = st.selectbox(
            "Search for any user name (EMBIMOS excluded)", identifiers_name
        )

    if user_login != "":
        df_user = (
            df_identifications.loc[
                df_identifications["user.login"] == user_login, "created_at"
            ]
            .dt.to_period("M")
            .value_counts()
            .sort_index()
            .reset_index()
        )

        df_user.columns = ["period", "identifications"]
        df_user["period"] = df_user["period"].astype(str)

        # Generar todos los meses desde el primer hasta el último en el dataset
        end_date = (
            pd.Timestamp.now().normalize()
        )  # Fecha de hoy a medianoche (asegura el mes actual)
        full_range = pd.date_range(
            start="2022-04-01", end=end_date, freq="MS"
        ).strftime("%Y-%m")

        # Crear DataFrame con todos los meses
        df_full = pd.DataFrame(full_range, columns=["period"])

        # Hacer un merge con los datos originales, rellenando los NaN con 0
        df_user = df_full.merge(df_user, on="period", how="left").fillna(0)

        # Convertir identificaciones a int (porque fillna lo convierte en float)
        df_user["identifications"] = df_user["identifications"].astype(int)
        create_user_line_chart(
            df_user, key=f"{user_login}_identifications", y_column="identifications"
        )

    else:
        # Obtener los 20 usuarios con más identificaciones
        top_users = (
            df_identifications["user.login"].value_counts().head(10).index.tolist()
        )

        df_filtered = df_identifications[
            df_identifications["user.login"].isin(top_users)
        ]

        # Calcular identificaciones por mes y usuario
        df_top_users = (
            df_filtered.groupby(
                [df_filtered["created_at"].dt.to_period("M"), "user.login"]
            )
            .size()
            .reset_index(name="identifications")
        )

        df_top_users["period"] = df_top_users["created_at"].astype(str)
        df_top_users.drop(columns=["created_at"], inplace=True)

        # Generar rango de fechas completo
        full_range = pd.date_range(
            start="2022-04-01", end=pd.Timestamp.now(), freq="MS"
        ).strftime("%Y-%m")
        df_full = pd.DataFrame(full_range, columns=["period"])

        # Asegurar que cada usuario tenga todos los meses en su serie de datos
        users = df_top_users["user.login"].unique()
        df_full = (
            df_full.assign(key=1)
            .merge(pd.DataFrame(users, columns=["user.login"]).assign(key=1), on="key")
            .drop("key", axis=1)
        )

        # Unir los datos reales con el rango completo
        df_users = df_full.merge(
            df_top_users, on=["period", "user.login"], how="left"
        ).fillna(0)
        df_top_users["identifications"] = df_top_users["identifications"].astype(int)

        create_user_line_chart(
            df_top_users,
            key="top_users_identifications",
            y_column="identifications",
            top_users=top_users,
        )

    # Total tables to download
    st.header("Identifiers (users with at least one identification)")

    col1, col2, col3 = st.columns([3, 1, 7])

    with col1:
        st.markdown("**Period of days to be considered active an identifier:**")
    with col2:
        activity_period = st.number_input(
            "Period of days to be considered active an identifier:",
            value=365,
            placeholder="Type a number...",
            label_visibility="collapsed",
        )
    last_days = pd.Timestamp.today() - pd.Timedelta(days=activity_period)
    df_identifiers["is_active"] = df_identifiers["last_identification"] >= last_days

    col0, col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 2, 2])
    with col0:
        st.markdown("**Filters:**")
    with col1:
        current_year = datetime.now().year
        years = [""] + [str(year) for year in range(2022, current_year + 1)]
        year_option = st.selectbox(
            "Identifiers in this year:",
            years,
        )
    with col2:
        month_option = st.selectbox(
            "Identifiers in this month:",
            [""] + [str(month) for month in range(1, 13)],
        )
    with col3:
        active_option = st.selectbox(
            "Account is active:",
            ["", "YES", "NO"],
        )

    with col4:
        kingdom_option = st.selectbox(
            "Most identified kingdom:",
            [""]
            + sorted(
                list(
                    df_identifiers.loc[
                        df_identifiers["most_kingdom"].notnull(), "most_kingdom"
                    ].unique()
                )
            ),
        )
    with col5:
        phylum_option = st.selectbox(
            "Most identified phylum:",
            [""]
            + sorted(
                list(
                    df_identifiers.loc[
                        df_identifiers["most_phylum"].notnull(), "most_phylum"
                    ].unique()
                )
            ),
        )

    df_result = df_identifiers.copy()
    df_result["created_at"] = pd.to_datetime(df_result["created_at"])
    df_result["last_identification"] = pd.to_datetime(
        df_result["last_identification"]
    ).dt.date

    if year_option != "":
        unique_users = df_identifications.loc[
            df_identifications["created_at"].dt.year == int(year_option), "user.id"
        ].unique()
        df_result = df_result[df_result["identifier_id"].isin(unique_users)]
        if month_option != "":
            unique_users = df_identifications.loc[
                (df_identifications["created_at"].dt.year == int(year_option))
                & (df_identifications["created_at"].dt.month == int(month_option)),
                "user.id",
            ].unique()
            df_result = df_result[df_result["identifier_id"].isin(unique_users)]
    if month_option != "":
        unique_users = df_identifications.loc[
            (df_identifications["created_at"].dt.month == int(month_option)), "user.id"
        ].unique()
        df_result = df_result[df_result["identifier_id"].isin(unique_users)]
    if active_option != "":
        df_result = df_result[df_result["is_active"] == (active_option == "YES")]

    if kingdom_option != "":
        df_result = df_result[df_result["most_kingdom"] == kingdom_option]
    if phylum_option != "":
        df_result = df_result[df_result["most_phylum"] == phylum_option]

    st.markdown("")
    st.markdown(f"* **Number of identifiers**: {df_result.shape[0]}")

    if df_result.shape[0] > 0:
        avg_identifications = round(
            df_result["number_identifications"].sum() / df_result.shape[0], 2
        )
        st.markdown(
            f"* **Average number of identifications uploaded by identifier**: {avg_identifications}"
        )
        st.dataframe(
            df_result.drop(columns=["identifier_id"]).assign(
                is_active=df_result["is_active"].map({True: "YES", False: "NO"}),
                created_at=df_result["created_at"].dt.date,
            ),
            hide_index=True,
            height=300,
        )

    st.header("Ratio Observations vs. identifications")
    st.markdown("Excluding EMBIMOS members")
    df_users = pd.read_csv(f"{directory}/data/minka_accounts.csv")
    df_observers = (
        df_users[df_users.observations_count > 0].reset_index(drop=True).copy()
    )

    df_observers = df_observers[
        -df_observers["user_name"].isin(EXCLUDE_USERS)
    ].reset_index(drop=True)

    plot_observations_vs_identifications(df_observers)
