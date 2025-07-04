import os

import streamlit as st

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

# Fuente de datos
with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/Logo_BioplatgesMet.png")
    with col2:
        st.header(":blue[Font de dades]")
        st.markdown("")
        st.markdown("")

text = """
Les dades disponibles en aquest Panell de Seguiment són una visualització de la informació recollida a través de MINKA, de manera voluntària, pels participants del projecte BioPlatgesMet. Es poden consultar a: [https://minka-sdg.org/projects/bioplatgesmet](https://minka-sdg.org/projects/bioplatgesmet).

MINKA és una plataforma d’observació ciutadana desenvolupada per l’ICM-CSIC. És una infraestructura que ofereix eines i serveis per promoure la participació ciutadana i la recopilació de dades sobre biodiversitat i paràmetres ambientals. Permet compartir observacions geolocalitzades de biodiversitat i variables ambientals per contribuir al seguiment dels Objectius de Desenvolupament Sostenible (ODS). Està dissenyada per facilitar la col·laboració entre la ciutadania, la comunitat acadèmica, l’administració pública, la indústria i altres sectors.

Les dades recopilades amb MINKA es poden descarregar a través de la **Infraestructura Mundial de Dades sobre Biodiversitat (GBIF)**. Si vols descarregar el conjunt de dades, pots fer-ho a través de l’enllaç: [https://www.gbif.org/dataset/9a51436f-3c81-4b1a-92d6-6f0c1dbb05de](https://www.gbif.org/dataset/9a51436f-3c81-4b1a-92d6-6f0c1dbb05de).

Comunicar als nostres usuaris sobre l’ús de les seves dades és fonamental per incentivar la seva participació i reconèixer la tasca voluntària que duen a terme. Si fas ús d’aquest panell, de les dades de MINKA i/o del projecte BioPlatgesMet, tingues en compte la **Guia de Citació de Dades de MINKA** disponible a: [https://zenodo.org/records/14216256](https://zenodo.org/records/14216256).

Citar les dades i informar-nos sobre el seu ús és clau perquè la comunitat continuï participant. Gràcies per la teva contribució.

**Font de les dades:** MINKA Citizen Observatory. MINKA API Data Feed. EMBIMOS research group, Institut de Ciències del Mar (ICM-CSIC). Barcelona, Spain. Available at: [https://minka-sdg.org](https://minka-sdg.org).
"""

st.markdown(text)
st.markdown("")
st.markdown("")
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
