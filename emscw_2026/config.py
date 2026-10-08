DIRECTORY = "emscw_2026"

API_PATH = "https://api.minka-sdg.org/v1"
HOME_PATH = "https://observe.minka-sdg.org"

COLORS = ["#013164", "#015e91", "#49b8cd", "#e2f3fc"]

PROJ_NAME = "European Marine Citizen Science Week 2026"

PROJ_DATES = "Sep 14, 2026 - Sep 20, 2026"

START_DAY = "2026-09-14"
END_DAY = "2026-09-20"

PROJ_LOGO = "emscw_2026_logo.png"

PROJECT_ID = 650

METRIC_TYPE = "place_id"

# Places con sus IDs y nombres
PLACES = {
    825: "Portugal Coast",
    886: "Gotland",
    885: "Azores",
    55: "Spain",
}

# Coordenadas de centro para los mapas de cada place
PLACE_CENTERS = {
    825: [39.5, -8.5],  # Portugal coast
    886: [57.5, 18.5],  # Gotland
    885: [38.5, -28.0],  # Açores
    55: [40.0, -3.7],  # Spain
}

# Zoom para cada place
PLACE_ZOOM = {
    825: 6,
    886: 8,
    885: 7,
    55: 5,
}

EXCLUDE_USERS = []
