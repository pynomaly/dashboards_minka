import calendar
import hmac
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
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


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


# funciones
@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data(ttl=360)
def create_obs_year_df(df_obs):
    # Convertir la columna de fecha a datetime
    df_obs["created_at"] = pd.to_datetime(df_obs["created_at"])
    df_obs["embimos"] = df_obs["user_login"].isin(EXCLUDE_USERS)

    # Extraer el año
    df_obs["year"] = df_obs["created_at"].dt.year

    # Agrupar por año y calcular los KPIs adicionales
    df_obs_year = (
        df_obs.groupby("year")
        .agg(
            total_observations=("created_at", "size"),
            research_quality=("quality_grade", lambda x: (x == "research").sum()),
            in_catalunya=(
                "catalunya",
                lambda x: x.sum(),
            ),  # Asume que es booleano (True/False)
            out_catalunya=(
                "catalunya",
                lambda x: (~x).sum(),
            ),  # Contar False como fuera de Cataluña
            web=("device", lambda x: (x == "web").sum()),  # Contar "web"
            app=("device", lambda x: (x == "app").sum()),  # Contar "app"
            observers=("user_id", "nunique"),
            embimos=("embimos", lambda x: (x).sum()),  # Contar True
            not_embimos=("embimos", lambda x: (~x).sum()),  # Contar False
        )
        .reset_index()
    )

    # Mostrar resultado
    return df_obs_year


def get_identifiers_by_period(period):
    session = requests.Session()

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
        identifiers = [result["user"]["login"] for result in results]
        identifiers_number = len(set(identifiers) - set(EXCLUDE_USERS))
        return identifiers_number

    else:
        print(f"Error fetching data for {period}")
        return None


@st.cache_data(ttl=360)
def create_obs_year_month_df(df_obs):

    # Convertir la columna de fecha a datetime
    df_obs["created_at"] = pd.to_datetime(df_obs["created_at"])
    df_obs["embimos"] = df_obs["user_login"].isin(EXCLUDE_USERS)

    # Extraer el año y el mes
    df_obs["year"] = df_obs["created_at"].dt.year
    df_obs["month"] = df_obs["created_at"].dt.month

    # Agrupar por año y mes, calculando los KPIs
    df_obs_year_month = (
        df_obs.groupby(["year", "month"])
        .agg(
            total_observations=("created_at", "size"),
            research_quality=("quality_grade", lambda x: (x == "research").sum()),
            in_catalunya=("catalunya", lambda x: x.sum()),  # Contar True
            out_catalunya=("catalunya", lambda x: (~x).sum()),  # Contar False
            web=("device", lambda x: (x == "web").sum()),  # Contar "web"
            app=("device", lambda x: (x == "app").sum()),  # Contar "app"
            observers=("user_id", "nunique"),
            embimos=("embimos", lambda x: (x).sum()),  # Contar True
            not_embimos=("embimos", lambda x: (~x).sum()),  # Contar False
        )
        .reset_index()
    )

    # Mostrar resultado
    return df_obs_year_month


@st.cache_data(ttl=360)
def create_obs_daily_df(df_obs):
    # Convertir la columna de fecha a datetime
    df_obs["created_at"] = pd.to_datetime(df_obs["created_at"])
    df_obs["embimos"] = df_obs["user_login"].isin(EXCLUDE_USERS)

    # Extraer la fecha sin la hora
    df_obs["date"] = df_obs["created_at"].dt.date

    # Agrupar por fecha y calcular los valores diarios
    df_daily = (
        df_obs.groupby("date")
        .agg(
            daily_total=("created_at", "size"),
            daily_research=("quality_grade", lambda x: (x == "research").sum()),
            daily_catalonia=("catalunya", lambda x: x.sum()),  # Contar True
            daily_outside_catalonia=("catalunya", lambda x: (~x).sum()),  # Contar False
            daily_web=("device", lambda x: (x == "web").sum()),  # Contar "web"
            daily_app=("device", lambda x: (x == "app").sum()),  # Contar "app"
            daily_users=("user_id", lambda x: set(x)),
            daily_embimos=("embimos", lambda x: (x).sum()),  # Contar True
            daily_not_embimos=("embimos", lambda x: (~x).sum()),  # Contar False
        )
        .reset_index()
    )

    # Calcular los valores acumulativos
    df_daily["cumulative_total"] = df_daily["daily_total"].cumsum()
    df_daily["cumulative_research"] = df_daily["daily_research"].cumsum()
    df_daily["cumulative_catalonia"] = df_daily["daily_catalonia"].cumsum()
    df_daily["cumulative_outside_catalonia"] = df_daily[
        "daily_outside_catalonia"
    ].cumsum()
    df_daily["cumulative_web"] = df_daily["daily_web"].cumsum()
    df_daily["cumulative_app"] = df_daily["daily_app"].cumsum()
    df_daily["cumulative_embimos"] = df_daily["daily_embimos"].cumsum()
    df_daily["cumulative_not_embimos"] = df_daily["daily_not_embimos"].cumsum()

    # Seleccionar las columnas finales
    df_cumulative = df_daily[
        [
            "date",
            "cumulative_total",
            "cumulative_research",
            "cumulative_catalonia",
            "cumulative_outside_catalonia",
            "cumulative_web",
            "cumulative_app",
            "cumulative_embimos",
            "cumulative_not_embimos",
        ]
    ].copy()

    # Mostrar resultado
    return df_cumulative


def create_radio_selector(key):
    visualization_type = st.radio(
        "Observations by year and month",
        [
            "Total observations",
            "By quality grade",
            "By location",
            "By device",
            "By EMBIMOS / Not EMBIMOS",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key=f"{key}_1",
    )
    return visualization_type


def create_yearly_bar_chart(df, key, visualization_type):

    # Configurar el gráfico según la selección
    if visualization_type == "Total observations":
        max_value = df["total_observations"].max()
        fig = px.bar(
            df,
            x="year",
            y="total_observations",
            title="Total observations by year",
            text="total_observations",  # Añadir etiquetas de texto
        )
        # Formatear números para eliminar decimales
        fig.update_traces(texttemplate="%{text:,.0f}")

    elif visualization_type == "By quality grade":

        df["non_research"] = df["total_observations"] - df["research_quality"]
        max_value = max(df["research_quality"].max(), df["non_research"].max())

        fig = px.bar(
            df,
            x="year",
            y=["research_quality", "non_research"],
            title="Observations by quality grade",
            labels={"value": "Number of observations", "variable": "Grade"},
            color_discrete_map={
                "research_quality": "#636EFA",
                "non_research": "#EF553B",
            },
            barmode="group",
            text_auto=",.0f",  # Añadir etiquetas de texto automáticamente
        )
        newnames = {"research_quality": "Research", "non_research": "No Research"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    elif visualization_type == "By location":
        max_value = max(df["in_catalunya"].max(), df["out_catalunya"].max())
        fig = px.bar(
            df,
            x="year",
            y=["in_catalunya", "out_catalunya"],
            title="Observations by Location",
            labels={"value": "Number of observations", "variable": "Location"},
            color_discrete_map={"in_catalunya": "#636EFA", "out_catalunya": "#EF553B"},
            barmode="group",
            text_auto=",.0f",  # Añadir etiquetas de texto automáticamente
        )
        newnames = {"in_catalunya": "Catalunya", "out_catalunya": "Rest of the world"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    elif visualization_type == "By EMBIMOS / Not EMBIMOS":
        max_value = max(df["embimos"].max(), df["not_embimos"].max())
        fig = px.bar(
            df,
            x="year",
            y=["embimos", "not_embimos"],
            title="Observations by members of EMBIMOS",
            labels={"value": "Number of observations", "variable": "EMBIMOS"},
            color_discrete_map={"embimos": "#636EFA", "not_embimos": "#EF553B"},
            barmode="group",
            text_auto=",.0f",
        )
        newnames = {"embimos": "EMBIMOS", "not_embimos": "Not EMBIMOS"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    else:  # Por dispositivo
        max_value = max(df["web"].max(), df["app"].max())
        fig = px.bar(
            df,
            x="year",
            y=["web", "app"],
            title="Observation by Device",
            labels={"value": "Number of observations", "variable": "Device"},
            color_discrete_map={"web": "#636EFA", "app": "#EF553B"},
            barmode="group",
            text_auto=",.0f",  # Añadir etiquetas de texto automáticamente
        )
        newnames = {"web": "Web", "app": "App"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    # Configurar el eje X para mostrar solo años enteros
    fig.update_xaxes(
        tickmode="array",
        tickvals=df["year"].unique(),
        ticktext=df["year"].unique().astype(int),
    )

    # Actualizar layout y posición de las etiquetas
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Number of observations",
        bargap=0.2,
        bargroupgap=0.1,
        showlegend=True if visualization_type != "Total observaciones" else False,
        # Aumentar el rango en un 10% por encima del valor máximo
        yaxis=dict(
            range=[
                0,
                max_value * 1.1,
            ]
        ),
    )

    # Ajustar la posición y el formato de las etiquetas
    fig.update_traces(
        textposition="outside",  # Coloca el texto encima de las barras
        textfont=dict(size=13),  # Tamaño del texto
        texttemplate="%{y:,.0f}",
    )

    # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_2")

    # Descargar datos
    obs_year = convert_df(df)

    st.download_button(
        label="Download data",
        data=obs_year,
        file_name="observations_by_year.csv",
        mime="text/csv",
        key=f"{key}_3",
    )


def create_monthly_line_chart(df, key, visualization_type):
    # Crear una columna de fecha para el eje X
    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

    if visualization_type == "Total observations":
        max_value = df["total_observations"].max()
        fig = px.line(
            df,
            x="date",
            y="total_observations",
            title="Total Observations by Month",
            markers=True,  # Agregar puntos en cada observación
        )

    elif visualization_type == "By quality grade":
        df["non_research"] = df["total_observations"] - df["research_quality"]
        max_value = max(df["research_quality"].max(), df["non_research"].max())

        fig = px.line(
            df,
            x="date",
            y=["research_quality", "non_research"],
            title="Observations by quality grade",
            labels={"value": "Número de observaciones", "variable": "Grado"},
            color_discrete_map={
                "research_quality": "#636EFA",
                "non_research": "#EF553B",
            },
            markers=True,
        )
        newnames = {"research_quality": "Research", "non_research": "No Research"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    elif visualization_type == "By location":
        max_value = max(df["in_catalunya"].max(), df["out_catalunya"].max())
        fig = px.line(
            df,
            x="date",
            y=["in_catalunya", "out_catalunya"],
            title="Observations by location",
            labels={"value": "Número de observaciones", "variable": "Ubicación"},
            color_discrete_map={
                "in_catalunya": "#636EFA",
                "out_catalunya": "#EF553B",
            },
            markers=True,
        )
        newnames = {"in_catalunya": "Catalunya", "out_catalunya": "Rest of the world"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    elif visualization_type == "By EMBIMOS / Not EMBIMOS":
        max_value = max(df["embimos"].max(), df["not_embimos"].max())
        fig = px.line(
            df,
            x="date",
            y=["embimos", "not_embimos"],
            title="Observations by members of EMBIMOS",
            labels={"value": "Number of observations", "variable": "EMBIMOS"},
            color_discrete_map={"embimos": "#636EFA", "not_embimos": "#EF553B"},
            markers=True,
        )
        newnames = {"embimos": "EMBIMOS", "not_embimos": "Not EMBIMOS"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    else:  # Por dispositivo
        max_value = max(df["web"].max(), df["app"].max())
        fig = px.line(
            df,
            x="date",
            y=["web", "app"],
            title="Observations by device",
            labels={"value": "Número de observaciones", "variable": "Dispositivo"},
            color_discrete_map={
                "web": "#636EFA",
                "app": "#EF553B",
            },
            markers=True,
        )
        newnames = {"web": "Web", "app": "App"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    # Configurar el formato del eje X para mostrar año-mes
    fig.update_xaxes(
        tickformat="%Y-%m",  # Formato YYYY-MM
        dtick="M1",  # Mostrar cada mes
        tickangle=-30,  # Rotar las etiquetas para mejor legibilidad
        range=["2022-03-15", datetime.today().strftime("%Y-%m-%d")],
    )

    # Actualizar layout con rango ajustado del eje Y
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of observations",
        showlegend=True if visualization_type != "Total observaciones" else False,
        yaxis=dict(range=[0, max_value * 1.15]),
        margin=dict(b=100),
    )

    fig.update_traces(
        hovertemplate="<b>Month:</b> %{x}<br>"
        + "<b>Observations:</b> %{y:,.0f}<extra></extra>"
    )

    # Agregar líneas verticales para separar los años
    unique_years = sorted(df["year"].unique())
    for year in unique_years:
        first_day_of_year = pd.to_datetime(f"{year}-01-01")
        fig.add_vline(
            x=first_day_of_year, line_color="black", opacity=0.5, line_width=0.8
        )

    # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_2")

    # Descargar datos
    obs_year_month = convert_df(df)

    st.download_button(
        label="Download data",
        data=obs_year_month,
        file_name="observations_by_month.csv",
        mime="text/csv",
        key=f"{key}_3",
    )


def create_daily_line_chart(df, key, visualization_type):
    # Crear una columna de fecha para el eje X

    # df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

    if visualization_type == "Total observations":
        max_value = df["cumulative_total"].max()
        fig = px.line(
            df,
            x="date",
            y="cumulative_total",
            title="Total Observations uploaded until this day",
            markers=False,  # Agregar puntos en cada observación
        )

    elif visualization_type == "By quality grade":
        df["non_research"] = df["cumulative_total"] - df["cumulative_research"]
        max_value = max(df["cumulative_research"].max(), df["non_research"].max())

        fig = px.line(
            df,
            x="date",
            y=["cumulative_research", "non_research"],
            title="Observations by quality grade",
            labels={"value": "Number of observations", "variable": "Grade"},
            color_discrete_map={
                "cumulative_research": "#636EFA",
                "non_research": "#EF553B",
            },
            markers=False,
        )
        newnames = {"cumulative_research": "Research", "non_research": "No Research"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    elif visualization_type == "By location":
        max_value = max(
            df["cumulative_catalonia"].max(), df["cumulative_outside_catalonia"].max()
        )
        fig = px.line(
            df,
            x="date",
            y=["cumulative_catalonia", "cumulative_outside_catalonia"],
            title="Observations by location",
            labels={"value": "Number in observations", "variable": "Location"},
            color_discrete_map={
                "cumulative_catalonia": "#636EFA",
                "cumulative_outside_catalonia": "#EF553B",
            },
            markers=False,
        )
        newnames = {
            "cumulative_catalonia": "Catalunya",
            "cumulative_outside_catalonia": "Rest of the world",
        }
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    elif visualization_type == "By EMBIMOS / Not EMBIMOS":
        max_value = max(
            df["cumulative_embimos"].max(), df["cumulative_not_embimos"].max()
        )
        fig = px.line(
            df,
            x="date",
            y=["cumulative_embimos", "cumulative_not_embimos"],
            title="Observations by members of EMBIMOS",
            labels={"value": "Number of observations", "variable": "EMBIMOS members"},
            color_discrete_map={
                "cumulative_embimos": "#636EFA",
                "cumulative_not_embimos": "#EF553B",
            },
            markers=False,
        )
        newnames = {
            "cumulative_embimos": "EMBIMOS",
            "cumulative_not_embimos": "Not EMBIMOS",
        }
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    else:  # Por dispositivo
        max_value = max(df["cumulative_web"].max(), df["cumulative_app"].max())
        fig = px.line(
            df,
            x="date",
            y=["cumulative_web", "cumulative_app"],
            title="Observations by device",
            labels={"value": "Number of observations", "variable": "Device"},
            color_discrete_map={
                "cumulative_web": "#636EFA",
                "cumulative_app": "#EF553B",
            },
            markers=False,
        )
        newnames = {"cumulative_web": "Web", "cumulative_app": "App"}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))

    # Configurar el formato del eje X para mostrar año-mes
    fig.update_xaxes(
        tickformat="%Y-%m-%d",  # Formato YYYY-MM-DD
        dtick="M1",  # Mostrar cada mes
        tickangle=-30,  # Rotar las etiquetas para mejor legibilidad
        range=["2022-03-15", datetime.today().strftime("%Y-%m-%d")],
    )

    # Actualizar layout con rango ajustado del eje Y
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of observations",
        showlegend=True if visualization_type != "Total observaciones" else False,
        yaxis=dict(range=[0, max_value * 1.15]),
        margin=dict(b=100),
    )

    fig.update_traces(
        hovertemplate="<b>Month:</b> %{x}<br>"
        + "<b>Observations:</b> %{y:,.0f}<extra></extra>"
    )

    # Agregar líneas verticales para separar los años
    unique_years = range(2022, datetime.today().year + 1)

    for year in unique_years:
        first_day_of_year = pd.to_datetime(f"{year}-01-01")
        fig.add_vline(
            x=first_day_of_year, line_color="black", opacity=0.5, line_width=0.8
        )

    # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_2")

    # Descargar datos
    obs_year_month = convert_df(df)

    st.download_button(
        label="Download data",
        data=obs_year_month,
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"{key}_3",
    )


def compare_total_observations(df_obs, days=30):
    # Asegúrate de que 'created_at' sea datetime
    df_obs["created_at"] = pd.to_datetime(df_obs["created_at"])

    # Filtra el rango de fechas para el periodo actual
    end_date = df_obs["created_at"].max()
    start_date = end_date - pd.Timedelta(days=days)
    current_period = df_obs[
        (df_obs["created_at"] >= start_date) & (df_obs["created_at"] <= end_date)
    ]

    # Calcula el total de observaciones para el periodo actual
    total_current = len(current_period)

    # Mismo periodo pero del año pasado
    start_date_last_year = start_date - pd.DateOffset(years=1)
    end_date_last_year = end_date - pd.DateOffset(years=1)
    last_year_period = df_obs[
        (df_obs["created_at"] >= start_date_last_year)
        & (df_obs["created_at"] <= end_date_last_year)
    ]

    # Calcula el total de observaciones para el periodo del año pasado
    total_last_year = len(last_year_period)

    # Resultados
    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "start_date_last_year": start_date_last_year.strftime("%Y-%m-%d"),
        "end_date_last_year": end_date_last_year.strftime("%Y-%m-%d"),
        "current_period_total": f"{total_current:,.0f}",
        "last_year_period_total": f"{total_last_year:,.0f}",
        "difference": f"{(total_current - total_last_year):,.0f}",
        "percentage_change": f"{round(((total_current - total_last_year) / total_last_year) * 100 if total_last_year != 0 else None, 2)}%",
    }


def create_comparative_lines(visualization_type="Total observations"):
    # Asegurar que el DataFrame está en session_state
    df = st.session_state.df_obs_year_month.copy()

    # Convertir "date" a datetime si no lo está
    df["date"] = pd.to_datetime(df["date"])

    # Convertir el mes a string para asegurarse de que se trata como una categoría
    df["month"] = df["month"].astype(str)

    # Crear una nueva columna que combine mes y año para evitar agrupaciones erróneas
    df["month_year"] = df["month"] + "-" + df["year"].astype(str)
    df["year"] = df["year"].astype(str)

    # Crear un diccionario de colores personalizados por año
    color_map = {
        "2022": "#A7D5FF",  # Azul claro
        "2023": "#4C9AFF",  # Azul medio
        "2024": "#FF6B6B",  # Rojo medio
        "2025": "#C91616",  # Rojo oscuro
        "2026": "#4CAF50",  # Verde fresco
        "2027": "#A1E887",  # Verde claro
        "2028": "#FFA500",  # Naranja cálido
        "2029": "#FFC966",  # Amarillo anaranjado
    }

    # Determinar la selección de datos
    if visualization_type == "Total observations":
        selection = "total_observations"
    else:
        option_map = {}
        if visualization_type == "By quality grade":
            option_map = {
                "Research": "research_quality",
                "No Research": "non_research",
            }
        elif visualization_type == "By location":
            option_map = {
                "Catalonia": "in_catalunya",
                "Outside Catalonia": "out_catalunya",
            }
        elif visualization_type == "By device":
            option_map = {
                "Web": "web",
                "App": "app",
            }
        elif visualization_type == "By EMBIMOS / Not EMBIMOS":
            option_map = {"embimos": "embimos", "not_embimos": "not_embimos"}

        # Mostrar opciones de selección sobre el gráfico
        selected_option = st.pills(
            "Select an option:",
            list(option_map.keys()),
            default=list(option_map.keys())[0],
        )
        selection = option_map[selected_option]

    # Crear el gráfico de barras
    fig = px.line(
        df,
        x="month",
        y=selection,
        color="year",
        labels={
            "month": "Month",
            "total_observations": "Number of observations",
            "year": "Year",
        },
        category_orders={"month": [str(i) for i in range(1, 13)]},
        color_discrete_map=color_map,
        markers=True,
    )

    # Forzar el eje x a ser categórico
    fig.update_layout(xaxis_type="category")

    # Ajustar la posición de las etiquetas sobre las barras
    # fig.update_traces(textposition="outside")

    # Mostrar en Streamlit
    st.plotly_chart(fig, use_container_width=True)


# Uso del dashboard
if __name__ == "__main__":
    if not check_password():
        st.stop()  # Do not continue if check_password is not True.

    # Carga origen de datos
    if "df_obs" not in st.session_state or st.session_state.df_obs is None:
        df_obs = pd.read_csv(f"{directory}/data/minka_obs.csv")
        # Eliminar observaciones importadas
        df_obs = df_obs[df_obs.imported == False].reset_index(drop=True)
        st.session_state.df_obs = df_obs

    # Selector de botones
    visualization_type = create_radio_selector("observations")
    if visualization_type == "By EMBIMOS / Not EMBIMOS":
        st.markdown(f'**EMBIMOS accounts**: :gray[{", ".join(EXCLUDE_USERS)}]')

    # Agrupación anual
    key1 = "obs_by_year"
    col1, col2 = st.columns([3, 2])
    with col1:
        st.header("Total number of observations submitted per year")
        if (
            "df_obs_year" not in st.session_state
            or st.session_state.df_obs_year is None
        ):
            st.session_state.df_obs_year = create_obs_year_df(st.session_state.df_obs)
        create_yearly_bar_chart(st.session_state.df_obs_year, key1, visualization_type)

    # Agrupación mensual
    key2 = "obs_by_year_month"
    col1, col2 = st.columns([6, 2])
    with col1:
        st.header("Total number of observations submitted per month")
        if (
            "df_obs_year_month" not in st.session_state
            or st.session_state.df_obs_year_month is None
        ):
            st.session_state.df_obs_year_month = create_obs_year_month_df(
                st.session_state.df_obs
            )
        create_monthly_line_chart(
            st.session_state.df_obs_year_month, key2, visualization_type
        )

    # Evolución diaria
    key3 = "cumulative_obs_by_day"
    st.header("Cumulative number of observations submitted by day")
    col1, col2 = st.columns([6, 2])
    with col1:
        df_ob_daily = create_obs_daily_df(st.session_state.df_obs)
        print(df_ob_daily.columns)
        create_daily_line_chart(df_ob_daily, key3, visualization_type)

    # Comparación meses de distintos años
    st.header("Comparative of monthly observations between years")
    create_comparative_lines(visualization_type)

    # Comparación de periodos
    st.header("Compare current period with same period of last year")
    num_days = st.select_slider(
        "Number of days to compare",
        options=[1] + list(range(10, 30, 10)) + list(range(30, 361, 10)),
        value=30,
    )
    results = compare_total_observations(st.session_state.df_obs, days=num_days)
    st.markdown(f"**Period compared**:")
    st.markdown(
        f"{results['start_date']} to {results['end_date']} || {results['start_date_last_year']} to {results['end_date_last_year']}"
    )

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        st.metric("Total for current period", results["current_period_total"])
    with col2:
        st.metric("Total for same period, last year", results["last_year_period_total"])
    with col3:
        st.metric("Difference", results["difference"])
    with col4:
        st.metric("Percentage change", results["percentage_change"])
