import base64
import os

import streamlit as st


def image_with_link(image_path, url, width="100%"):
    """Render an image as a clickable link."""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = image_path.split(".")[-1]
    st.markdown(
        f'<a href="{url}" target="_blank"><img src="data:image/{ext};base64,{data}" width="{width}"></a>',
        unsafe_allow_html=True,
    )


# Set page config FIRST, before any other st commands or local imports
try:
    directory = f"{os.environ['DASHBOARDS']}/home"
except KeyError:
    directory = os.path.dirname(os.path.abspath(__file__))
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


st.set_page_config(
    layout="wide",
    page_title="Dashboards MINKA",
    page_icon=f"{directory}/images/minka-logo.png",
)

# Apply custom fonts
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    * {
        font-family: 'Inter', 'Trebuchet MS', Arial, sans-serif !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


col1, col2 = st.columns([1, 20])
with col1:
    st.image(f"{directory}/images/minka-logo.png")
with col2:
    st.markdown(
        '<h1 style="color: #fa4338;">Dashboards MINKA</h1>', unsafe_allow_html=True
    )
st.divider()

col1, col2, col3, col4 = st.columns([1, 10, 1, 10])
with col1:
    st.image(f"{directory}/images/Biomarato_logo.png")
with col2:
    st.subheader("BioMARató")
with col3:
    st.image(f"{directory}/images/Biomarato_logo.png")
with col4:
    st.subheader("Biomaratona Portugal")

# Biomarato
col1, col2, col3, col4, col5 = st.columns([10, 10, 1, 10, 10])

with col1:
    st.markdown("**[2025](https://dashboard.minka-sdg.org/biomarato25/)**")
    image_with_link(
        f"{directory}/images/minka_biomarato_2025.png",
        "https://dashboard.minka-sdg.org/biomarato25/",
    )
with col2:
    st.markdown("**[2026](https://dashboard.minka-sdg.org/biomarato26)**")
    image_with_link(
        f"{directory}/images/minka_biomarato_2026.png",
        "https://dashboard.minka-sdg.org/biomarato26/",
    )
with col4:
    st.markdown("**[2025](https://dashboard.minka-sdg.org/biomaratona25/)**")
    image_with_link(
        f"{directory}/images/minka_biomaratona_25.png",
        "https://dashboard.minka-sdg.org/biomaratona25/",
    )
with col5:
    st.markdown("**[2026](https://dashboard.minka-sdg.org/biomaratona26/)**")
    image_with_link(
        f"{directory}/images/minka_biomaratona_26.png",
        "https://dashboard.minka-sdg.org/biomaratona26/",
    )

st.divider()

col1, col2, col3, col4, col5, col6 = st.columns([1, 10, 1, 4.5, 1, 4.5])
with col1:
    st.image(f"{directory}/images/logo_biodiverciutat.png")
with col2:
    st.subheader("Biodiverciutat")
with col3:
    st.image(f"{directory}/images/Logo_BioplatgesMet.png")
with col4:
    st.subheader("Bioplatgesmet")
with col5:
    st.image(f"{directory}/images/logo_arsinoe.png")
with col6:
    st.subheader("Arsinoe")

col1, col2, col3, col4, col5 = st.columns([10, 10, 1, 10, 10])

# Biodiverciutat
with col1:
    st.markdown("**[2025](https://dashboard.minka-sdg.org/biodiverciutat25/)**")
    image_with_link(
        f"{directory}/images/minka_biodiverciutat_2025.png",
        "https://dashboard.minka-sdg.org/biodiverciutat25/",
    )
with col2:
    st.markdown("**[2026](https://dashboard.minka-sdg.org/biodiverciutat26/)**")
    image_with_link(
        f"{directory}/images/minka_biodiverciutat_2026.png",
        "https://dashboard.minka-sdg.org/biodiverciutat26/",
    )

# Proyectos de gestión
with col4:
    st.markdown("[Bioplatgesmet](https://dashboard.minka-sdg.org/bioplatgesmet)")
    image_with_link(
        f"{directory}/images/minka_bioplatgesmet.png",
        "https://dashboard.minka-sdg.org/bioplatgesmet/",
    )

with col5:
    st.markdown("[Arsinoe](https://dashboard.minka-sdg.org/arsinoe/)")
    image_with_link(
        f"{directory}/images/minka_arsinoe.png",
        "https://dashboard.minka-sdg.org/arsinoe/",
    )

st.divider()

# International dashboards
col1, col2, col3, col4, col5, col6 = st.columns([1, 10, 1, 4.5, 1, 4.5])
with col1:
    st.image(f"{directory}/images/Biomarato_logo.png")
with col2:
    st.subheader("International dashboards")

col1, col2, col3, col4, col5 = st.columns([10, 10, 1, 10, 10])

with col1:
    st.markdown(
        "**[BioMARathon France Occitanie 2026](https://dashboard.minka-sdg.org/biomarathon-france)**"
    )
    image_with_link(
        f"{directory}/images/minka_biomarathon_france_2026.png",
        "https://dashboard.minka-sdg.org/biomarathon-france/",
    )

st.divider()
