import os
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st
from markdownlit import mdlit
from utils import get_last_obs, reindex

# Variable de entorno para el directorio
try:
    directory = f"{os.environ['DASHBOARDS']}/biomarato_25"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_icon=f"{directory}/images/minka-logo.png",
    page_title="Dashboard BioMARató 2025",
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

exclude_users = [
    "xasalva",
    "bertinhaco",
    "andrea",
    "laurabiomar",
    "guillermoalvarez_fecdas",
    "mediambient_ajelprat",
    "fecdas_mediambient",
    "planctondiving",
    "marinagm",
    "CEM",
    "jaume-piera",
    "sonialinan",
    "adrisoacha",
    "anellides",
    "irodero",
    "manelsalvador",
    "sara_riera",
    "anomalia",
    "amaliacardenas",
    "aluna",
    "carlosrodero",
    "lydia",
    "elibonfill",
    "marinatorresgi",
    "meri",
    "monyant",
    "ura4dive",
    "lauracoro",
    "pirotte_",
    "oceanicos",
    "abril",
    "alba_barrera",
    "amb_platges",
    "daniel_palacios",
    "davidpiquer",
    "laiamanyer",
    "rogerpuig",
    "guillemdavila",
    # vanessa,
    # teresa,
]
matomo_script = """
    <!-- Matomo -->
    <script>
    var _paq = window._paq = window._paq || [];
    /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
    _paq.push(['trackPageView']);
    _paq.push(['enableLinkTracking']);
    (function() {
        var u="//matomo.quanta-labs.com/";
        _paq.push(['setTrackerUrl', u+'matomo.php']);
        _paq.push(['setSiteId', '8']);
        var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
        g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
    })();
    </script>
    <!-- End Matomo Code -->
"""

base_url = "https://minka-sdg.org"
api_path = "https://api.minka-sdg.org/v1"


projects = [
    {"id": 418, "name": "Girona"},
    {"id": 419, "name": "Tarragona"},
    {"id": 420, "name": "Barcelona"},
    {"id": 417, "name": "Catalunya"},
]

main_project = 417
project_id_gir = next((p["id"] for p in projects if p["name"] == "Girona"), None)
project_id_tarr = next((p["id"] for p in projects if p["name"] == "Tarragona"), None)
project_id_bcn = next((p["id"] for p in projects if p["name"] == "Barcelona"), None)

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


def get_last_species_from_obs(df_obs, df_photos):
    df_obs2 = df_obs[df_obs["taxon_rank"] == "species"].reset_index(drop=True)
    df_obs3 = df_obs2.sort_values(by=["observed_on", "observed_on_time"]).reset_index(
        drop=True
    )
    df_obs4 = df_obs3.drop_duplicates(subset=["taxon_id"], keep="first")
    df_obs5 = df_obs4.sort_values(
        by=["observed_on", "observed_on_time"], ascending=False
    ).reset_index(drop=True)

    df_unique_photos = df_photos.drop_duplicates(subset=["id"], keep="first")
    df_result = pd.merge(
        df_obs5, df_unique_photos[["id", "photos_medium_url", "attribution"]], on="id"
    )
    return df_result


def show_last_species(df, provincia_name):
    """
    Show the last species added to the list.
    """
    try:
        df.reset_index(drop=True, inplace=True)
        df["observed_on"] = pd.to_datetime(df["observed_on"])
        df["observed_on"] = df["observed_on"].dt.strftime("%d-%m-%Y")
        df.loc[:, "obs_url"] = df["id"].apply(
            lambda x: f"https://minka-sdg.org/observations/{x}"
        )
        i = 0
        col1sp, col2sp, col3sp, col4sp = st.columns(4, gap="small")
        with col1sp:
            st.dataframe(
                df[["taxon_name", "observed_on", "obs_url"]].rename(
                    columns={"observed_on": "data"}
                ),
                column_config={
                    "obs_url": st.column_config.LinkColumn("link", display_text="Veure")
                },
                use_container_width=True,
                height=300,
                hide_index=True,
            )
        for col in [col2sp, col3sp, col4sp]:
            with col:
                photo_url = df.loc[i, "photos_medium_url"]
                taxon_name = df.loc[i, "taxon_name"]
                st.markdown(
                    f":link: [MINKA](https://minka-sdg.org/observations/{df.loc[i, 'id']})"
                )
                st.image(
                    photo_url,
                    caption=f"{taxon_name} | Foto: {df.loc[i, 'attribution']}",
                )
                i += 1
        for col in [col1sp, col2sp, col3sp, col4sp]:
            with col:
                photo_url = df.loc[i, "photos_medium_url"]
                taxon_name = df.loc[i, "taxon_name"]
                st.markdown(
                    f":link: [MINKA](https://minka-sdg.org/observations/{df.loc[i, 'id']})"
                )
                st.image(
                    photo_url,
                    caption=f"{taxon_name} | Foto: {df.loc[i, 'attribution']}",
                )
                i += 1
    except:
        pass


# Carrusel de últimas observaciones,
# con grado research, excluidos xasalva y mediambient_ajelprat
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Últimes observacions publicades]")

    # Visor de imágenes: 15 imágenes, máximo 3 por usuario
    # Excluye a Xavi y a mediambient_ajelprat en la función

    last_total = get_last_obs(main_project)

    # convertimos el df para que sólo aparezcan 5 obs de cada usuario como máximo
    results = pd.DataFrame()
    for user in last_total.user_login.unique():
        last_five = last_total[last_total.user_login == user][:3]
        results = pd.concat([results, last_five], axis=0)
    # results = results.reset_index(drop=True)
    results = (
        results.sort_values(by="id", ascending=False).reset_index(drop=True).head(15)
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    col = 0
    session = requests.Session()
    for index, row in results.iterrows():
        image = row["photos_medium_url"]
        id_obs = row["id"]
        taxon_name = row.taxon_name
        try:
            response = session.get(image)
        except:
            continue

        if col == 0:
            with c1:
                st.image(response.content)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col += 1
        elif col == 1:
            with c2:
                st.image(response.content)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col += 1
        elif col == 2:
            with c3:
                st.image(response.content)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col += 1
        elif col == 3:
            with c4:
                st.image(response.content)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col += 1
        elif col == 4:
            with c5:
                st.image(response.content)
                mdlit(f"@(https://minka-sdg.org/observations/{id_obs})")
            col = 0


st.divider()

# Últimas especies incorporadas
with st.container():
    col1, col2 = st.columns([1, 25])
    with col1:
        st.image(f"{directory}/images/Biomarato_logo_100.png")
    with col2:
        st.header(":orange[Últimes espècies registrades per província]")

    # usuarios excluidos
    excluded = []
    # excluded = ["xasalva", "mediambient_ajelprat"]

    # Dataframes de observaciones de cada provincia
    try:
        province_id = project_id_gir
        df_obs1 = pd.read_csv(f"{directory}/data/{province_id}_df_obs.csv")
        df_photos1 = pd.read_csv(f"{directory}/data/{province_id}_df_photos.csv")
        sp_girona = get_last_species_from_obs(df_obs1, df_photos1)
        sp_girona = sp_girona[-sp_girona.user_login.isin(excluded)]

    except:
        sp_girona = None
    try:
        province_id = project_id_tarr
        df_obs1 = pd.read_csv(f"{directory}/data/{province_id}_df_obs.csv")
        df_photos1 = pd.read_csv(f"{directory}/data/{province_id}_df_photos.csv")
        sp_tarragona = get_last_species_from_obs(df_obs1, df_photos1)
        sp_tarragona = sp_tarragona[-sp_tarragona.user_login.isin(excluded)]
    except FileNotFoundError:
        sp_tarragona = None

    try:
        province_id = project_id_bcn
        df_obs1 = pd.read_csv(f"{directory}/data/{province_id}_df_obs.csv")
        df_photos1 = pd.read_csv(f"{directory}/data/{province_id}_df_photos.csv")
        sp_barcelona = get_last_species_from_obs(df_obs1, df_photos1)
        sp_barcelona = sp_barcelona[-sp_barcelona.user_login.isin(excluded)]

    except FileNotFoundError:
        sp_barcelona = None

    for df in [sp_girona, sp_tarragona, sp_barcelona]:
        if df is not None:
            df = reindex(df)

    # Girona
    st.header("Girona")
    show_last_species(sp_girona, "Girona")

    st.divider()

    # Tarragona
    st.header("Tarragona")
    show_last_species(sp_tarragona, "Tarragona")

    st.divider()

    # Barcelona
    st.header("Barcelona")
    show_last_species(sp_barcelona, "Barcelona")

    st.divider()

# Nuevas especies en place BioMARató
df_species = pd.read_csv(f"{directory}/data/place_biomarato_species.csv")

with st.container():
    st.header("Noves espècies a l'àrea Biomarató en els darrers 30 dies")
    last_month = datetime.now() - timedelta(days=30)
    df_species.first_date = pd.to_datetime(df_species.first_date)
    df_species_filtered = df_species[df_species.first_date >= last_month]
    df_species_filtered = df_species_filtered.sort_values(
        by="first_date", ascending=False
    )
    df_species_filtered.rename(
        columns={
            "id": "taxon_id",
            "first_date": "observed_on",
            "name": "taxon_name",
            "photo_url": "photos_medium_url",
            "author": "attribution",
            "obs_id": "id",
        },
        inplace=True,
    )
    show_last_species(df_species_filtered, "BioMARató")

# Logos
st.divider()
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        st.markdown("##### Organitzadors:")
        col1, __ = st.columns([3, 1])
        with col1:
            st.image(f"{directory}/images/organizadores_2024_v2.png")

    with col_2:
        st.markdown("##### Amb el finançament dels projectes europeus:")
        st.image(f"{directory}/images/logos_financiacion_biomarato_v2.png")
