DIRECTORY = "omb3_portugal"
DF_PATH = "data/df_obs.csv"

API_PATH = "https://api.minka-sdg.org/v1"
HOME_PATH = "https://minka-sdg.org"
OBSERVE_PATH = "https://observe.minka-sdg.org"

MAIN_PLACE = 701  # Biomaratona

COLORS = ["#F79256", "#FBD1A2", "#7DCFB6", "#00b6c4", "#5953a5"]

PAGE_TITLE = "Dashboard OMB3 Portugal"
PAGE_ICON = "minka-logo.png"
HEADER_LOGO = "ANERIS_logo.png"
HEADER_TITLE = f"ANERIS OMB product: [Portuguese coastline](https://observe.minka-sdg.org/places/{MAIN_PLACE})"


STARTING_DATE = "2021-01-01"

# Configuración de ModeBar de Plotly
CONFIG_MODEBAR = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "zoom2d",
        "pan2d",
        "lasso2d",
        "autoScale2d",
        "resetScale2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
        "zoomIn2d",
        "zoomOut2d",
    ],
    "displaylogo": False,
}

# Estilos CSS para el sidebar
SIDEBAR_WIDTH = 240

# Category translations (categories already in English, no translation needed)
CATEGORY_TRANSLATIONS = {}

# Archivos de especies
SPECIES_FILES = {
    "exotic": {
        "file": "data/species_non_indigenous.csv",
        "category_col": "category",
        "title": "Non-indigenous Species",
    },
    "protected": {
        "file": "data/sensitive_species.csv",
        "category_col": "category",
        "title": "Sensitive Species",
    },
}

# Orden de las categorías en las pestañas (las que no aparezcan irán al final)
CATEGORY_ORDER = {
    "protected": [
        "Critically Endangered",
        "Endangered",
        "Vulnerable",
        "Near Threatened",
    ],
    "exotic": [
        "non-indigenous",
    ],
}
