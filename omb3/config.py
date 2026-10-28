DIRECTORY = "omb3"
DF_PATH = "data/df_obs_catalunya.csv"

API_PATH = "https://api.minka-sdg.org/v1"
HOME_PATH = "https://minka-sdg.org"
OBSERVE_PATH = "https://observe.minka-sdg.org"

COLORS = ["#F79256", "#FBD1A2", "#7DCFB6", "#00b6c4", "#5953a5"]

PAGE_TITLE = "Dashboard OMB3"
PAGE_ICON = "minka-logo.png"
HEADER_LOGO = "ANERIS_logo.png"
HEADER_TITLE = "OMB product, case Study 3: Catalan coastline"

MAIN_PLACE = 737  # Catalunya

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

# Traducciones de categorías de especies (Catalán → Inglés)
CATEGORY_TRANSLATIONS = {
    # Exotic species
    "Exòtica": "Non-indigenous",
    "Exòtica invasora": "Invasive Alien",
    # Protected species
    "En perill d'extinció": "Endangered",
    "Espècie amb protecció de l’hàbitat/ZEC": "Habitat Protected",
    "Espècie amb regulació de l’explotació o del comerç": "Trade Regulated",
    "Espècie protegida": "Protected",
    "Extinta com a reproductora a Catalunya": "Extinct as Breeders",
    "Vulnerable": "Vulnerable",
}

# Archivos de especies
SPECIES_FILES = {
    "exotic": {
        "file": "data/species_exotic.csv",
        "category_col": "categoria",
        "title": "Non-indigenous Species",
    },
    "protected": {
        "file": "data/species_protected.csv",
        "category_col": "category",
        "title": "Sensitive Species",
    },
}

# Orden de las categorías en las pestañas (las que no aparezcan irán al final)
CATEGORY_ORDER = {
    "protected": [
        "Endangered",
        "Vulnerable",
        "Protected",
        "Trade Regulated",
        "Habitat Protected",
        "Extinct as Breeders",
    ],
    "exotic": [
        "Invasive Alien",
        "Non-indigenous",
    ],
}
