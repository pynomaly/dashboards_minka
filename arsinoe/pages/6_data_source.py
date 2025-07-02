import os

import streamlit as st

try:
    directory = f"{os.environ['DASHBOARDS']}/arsinoe"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

st.markdown(
    """
    <style>
        body {
            background-color: white !important;
            color: black !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Fuente de datos
with st.container():
    # Título
    col1, col2 = st.columns([1, 15])
    with col1:
        st.image(f"{directory}/images/ARSINOE.png")
    with col2:
        st.title("Data source")
        st.markdown("")
        st.markdown("")

text = """
Data available in this Dashboard is a visualization of the information collected through MINKA, on a voluntary basis, by the participants of the Arsinoe project. They can be consulted at: [https://minka-sdg.org/projects/arsinoe_educational-community](https://minka-sdg.org/projects/arsinoe_educational-community).

MINKA is a citizen observation platform developed by the ICM-CSIC. It is an infrastructure that offers tools and services to promote citizen participation and the collection of data on biodiversity and environmental parameters. It allows sharing geolocated observations of biodiversity and environmental variables to contribute to the monitoring of the Sustainable Development Goals (SDGs). It is designed to facilitate collaboration between citizens, the academic community, public administration, industry and other sectors.

Communicating to our users about the use of their data is essential to encourage their participation and recognize the voluntary work they carry out. If you make use of this panel, MINKA data and/or the Arsinoe project, please take into account the **MINKA Data Citation Guide** available at: [https://zenodo.org/records/14216256](https://zenodo.org/records/14216256).

Cite the data and inform us about its use is key to keeping the community engaged. Thank you for your contribution.

**Data source:** MINKA Citizen Observatory. MINKA API Data Feed. EMBIMOS research group, Institut de Ciències del Mar (ICM-CSIC). Barcelona, Spain. Available at: [https://minka-sdg.org](https://minka-sdg.org).
"""

st.markdown(text)
st.container(height=100, border=False)

# Footer
with st.container(border=True):
    col1, col2 = st.columns([10, 7], gap="small")
    with col1:
        st.markdown("##### Organizers")
        st.image(
            f"{directory}/images/organizers_arsinoe.png",
        )
    with col2:
        st.markdown("##### With the funding of European projects")
        st.image(
            f"{directory}/images/funders_arsinoe.png",
        )
