"""
Internationalization module for BioPlatgesMet dashboard.
Provides translation functions and custom navigation menu.
"""

import json
import os
from pathlib import Path

import streamlit as st

# Get the directory where this module is located
MODULE_DIR = Path(__file__).parent
LOCALES_DIR = MODULE_DIR / "locales"

# Available languages
LANGUAGES = {
    "ca": "Català",
    "es": "Español",
    "en": "English",
}

# Default language
DEFAULT_LANG = "ca"


def load_translations(lang: str) -> dict:
    """Load translations from JSON file for the specified language."""
    file_path = LOCALES_DIR / f"{lang}.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback to default language
        with open(LOCALES_DIR / f"{DEFAULT_LANG}.json", "r", encoding="utf-8") as f:
            return json.load(f)


def get_lang() -> str:
    """Get current language from session state."""
    if "lang" not in st.session_state:
        st.session_state.lang = DEFAULT_LANG
    return st.session_state.lang


def set_lang(lang: str) -> None:
    """Set current language in session state."""
    if lang in LANGUAGES:
        st.session_state.lang = lang
        # Reload translations
        st.session_state.translations = load_translations(lang)


def get_translations() -> dict:
    """Get current translations dictionary."""
    current_lang = get_lang()
    # Always reload if language changed or translations not loaded
    if (
        "translations" not in st.session_state
        or st.session_state.get("_translations_lang") != current_lang
    ):
        st.session_state.translations = load_translations(current_lang)
        st.session_state._translations_lang = current_lang
    return st.session_state.translations


def t(key: str) -> str:
    """
    Translate a key using dot notation.
    Example: t("metrics.observations") -> "Observacions"
    """
    translations = get_translations()
    keys = key.split(".")
    value = translations

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Return the key if translation not found
            return key

    return value


def hide_default_navigation():
    """Hide Streamlit's default sidebar navigation."""
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def create_language_selector():
    """Create a language selector in the sidebar using segmented control."""
    current_lang = get_lang()
    lang_keys = list(LANGUAGES.keys())

    selected = st.sidebar.segmented_control(
        "🌐 **Language**:",
        options=lang_keys,
        default=current_lang,
        format_func=lambda x: LANGUAGES[x],
        key="language_selector",
    )

    if selected and selected != current_lang:
        set_lang(selected)
        st.rerun()


def create_nav_menu(current_page: str = None):
    """
    Create custom navigation menu in sidebar.

    Args:
        current_page: The current page identifier to highlight
    """
    # Page definitions with their file paths
    pages = {
        "main": "1_main.py",
        "municipalities": "pages/2_municipalities.py",
        "sectors": "pages/3_sectors.py",
        "taxonomy": "pages/4_taxonomy.py",
        "species": "pages/5_species.py",
        "participants": "pages/6_participants.py",
        "highlights": "pages/7_highlights.py",
        "data_source": "pages/8_data_source.py",
        "eada_contribution": "pages/9_EADA_contribution.py",
    }

    st.sidebar.markdown("---")

    for page_id, page_file in pages.items():
        label = t(f"nav.{page_id}")

        # Check if file exists before showing in menu
        full_path = MODULE_DIR / page_file
        if not full_path.exists():
            continue

        # Use page_link with icon to highlight current page
        if current_page == page_id:
            st.sidebar.page_link(
                page_file, label=f"**{label}**", use_container_width=True
            )
        else:
            st.sidebar.page_link(page_file, label=label, use_container_width=True)


def init_i18n(current_page: str = None, show_nav: bool = True):
    """
    Initialize i18n for a page.

    Args:
        current_page: The current page identifier
        show_nav: Whether to show the navigation menu
    """
    # Hide default navigation
    hide_default_navigation()

    # Create language selector
    create_language_selector()

    # Create custom navigation if requested
    if show_nav:
        create_nav_menu(current_page)


def create_sidebar_content():
    """Create the sidebar description content."""
    st.sidebar.markdown("---")
    # st.sidebar.markdown(t("sidebar.description"))


def create_footer():
    """Create the standard footer with organizers and funding logos."""
    try:
        directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet_new"
    except KeyError:
        directory = str(MODULE_DIR)

    st.container(height=50, border=False)

    with st.container(border=True):
        col1, __, col2 = st.columns([10, 1, 5], gap="small")
        with col1:
            st.markdown(f"##### {t('footer.organizers')}")
            st.image(f"{directory}/images/organizadores_bioplatgesmet_logos2.png")
        with col2:
            st.markdown(f"##### {t('footer.funding')}")
            st.image(f"{directory}/images/financiadores_bioplatgesmet_logos.png")
