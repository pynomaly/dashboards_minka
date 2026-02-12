import os
import sys

import streamlit as st

# Set page config FIRST, before any other st commands or local imports
try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard Bioplatgesmet",
)

# Now import the rest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import create_footer, init_i18n, t
st.markdown(
    f"""
    <style>
        [data-testid="stSidebar"] {{
            width: 300px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            width: 300px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize i18n
init_i18n(current_page="eada_contribution")

# Fuente de datos
with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(f":blue[{t('header.eada_title')}]")
        st.markdown("")
        st.markdown("")
