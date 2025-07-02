import hmac
import os
import sys
from contextlib import redirect_stdout
from io import StringIO

import pandas as pd
import streamlit as st
from mecoda_minka import get_dfs, get_obs

try:
    directory = f"{os.environ['DASHBOARDS']}/interno"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard Interno Minka",
)


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")


def reindex(df):
    df.index = range(df.index.start + 1, df.index.stop + 1)
    return df


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


if not check_password():
    st.stop()  # Do not continue if check_password is not True.


def get_marine_column(df_obs):
    if len(df_obs) > 0:
        df_obs["taxon_id"] = pd.to_numeric(df_obs["taxon_id"], errors="coerce")
        tree = pd.read_csv(f"{directory}/data_marines/taxon_tree_with_marines.csv")
        df_obs_with_marine = pd.merge(
            df_obs, tree[["taxon_id", "marine"]], how="left", on="taxon_id"
        )
        return df_obs_with_marine
    else:
        print("Ninguna observación")
        return None


# Main Streamlit app starts here
if __name__ == "__main__":

    st.title("Descargar observaciones de MINKA")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Proyecto**")
    with col2:
        id_project = st.number_input("ID del proyecto:", value=0)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Place**")
    with col2:
        id_place = st.number_input("ID del place:", value=0)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**User name**")
    with col2:
        user_login = st.text_input("Name:", value="")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Grado de las observaciones**")
    with col2:
        grade = st.selectbox(
            "Grado:",
            ("todas", "research"),
            # label_visibility="collapsed",
        )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Fecha de observación:**")
    with col2:
        starts_on = st.text_input("Observado desde (YYYY/MM/DD):", "")
        ends_on = st.text_input("Observado hasta (YYYY/MM/DD):", "")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Fecha de subida:**")
    with col2:
        created_d1 = st.text_input("Subido desde (YYYY/MM/DD):", "")
        created_d2 = st.text_input("Subido hasta (YYYY/MM/DD):", "")

    # Diccionario con las variables y sus valores iniciales
    variables = {
        "id_project": id_project,
        "id_place": id_place,
        "grade": grade,
        "starts_on": starts_on,
        "ends_on": ends_on,
        "created_d1": created_d1,
        "created_d2": created_d2,
        "user_login": user_login,
    }

    # Función para actualizar los valores
    def update_value(value, default):
        if value == default:
            return None
        return value

    # Actualización de los valores en el diccionario
    variables["id_project"] = update_value(variables["id_project"], 0)
    variables["id_place"] = update_value(variables["id_place"], 0)
    variables["grade"] = update_value(variables["grade"], "todas")
    variables["starts_on"] = update_value(variables["starts_on"], "")
    variables["ends_on"] = update_value(variables["ends_on"], "")
    variables["created_d1"] = update_value(variables["created_d1"], "")
    variables["created_d2"] = update_value(variables["created_d2"], "")
    variables["user_login"] = update_value(variables["user_login"], "")

    if st.button("Descargar"):

        # Crear un contenedor para la salida
        output_container = st.empty()

        # Crear un buffer personalizado que actualice la UI
        class StreamlitOutput(StringIO):
            def write(self, text):
                super().write(text)
                # Actualizar el contenedor con todo el contenido acumulado
                output_container.code(self.getvalue(), language="text")

        # Redirigir stdout a nuestro buffer personalizado
        with redirect_stdout(StreamlitOutput()):
            st.write("#### Paso 1: Descargando observaciones...")
            try:
                obs = get_obs(
                    id_project=variables["id_project"],
                    place_id=variables["id_place"],
                    grade=variables["grade"],
                    starts_on=variables["starts_on"],
                    ends_on=variables["ends_on"],
                    created_d1=variables["created_d1"],
                    created_d2=variables["created_d2"],
                    user=variables["user_login"],
                )
            except:
                st.markdown("Revisa los parámetros que has indicado")
                obs = []

        with redirect_stdout(StreamlitOutput()):
            if len(obs) > 0:
                st.write("#### Paso 2: Construyendo dataframe...")
                df_obs, df_photos = get_dfs(obs)
                df_obs = df_obs.sort_values(by="id", ascending=False)
                st.write("#### Paso 3: Añadiendo columna marina...")
                df_obs = get_marine_column(df_obs)
                st.session_state.df_obs = df_obs

                # Primero elimina el contenedor de output antes de mostrar los resultados
                output_container.empty()

                st.subheader(
                    f"**Número de observaciones:** {len(st.session_state.df_obs)}"
                )
                st.dataframe(st.session_state.df_obs, hide_index=True)

                csv2 = convert_df(st.session_state.df_obs)
                st.download_button(
                    label="Descarga CSV",
                    data=csv2,
                    file_name="observations.csv",
                    mime="text/csv",
                )
            else:
                output_container.empty()  # Limpiar también en caso de no haber observaciones
                st.markdown("Ninguna observación")
