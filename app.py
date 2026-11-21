"""SmartRecipe AI: generate zero-waste recipes from ingredients you have."""

import json
import os
import re
from html import escape
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types


# Configure Streamlit before rendering any page elements.
st.set_page_config(
    page_title="SmartRecipe AI",
    page_icon="🍳",
    layout="wide",
)

# Load the secret from this project's .env file. The key is never displayed.
load_dotenv(Path(__file__).resolve().parent / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

MODEL_FALLBACKS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
]
BASIC_PANTRY = (
    "salt, black pepper, red chilli powder, turmeric, cumin, cooking oil, and water"
)

INGREDIENT_OPTIONS = [
    "Potato",
    "Onion",
    "Tomato",
    "Rice",
    "Peas",
    "Carrot",
    "Bread",
    "Cheese",
    "Paneer",
    "Capsicum",
    "Banana",
    "Milk",
    "Sugar",
    "Eggs",
    "Garlic",
    "Ginger",
    "Spinach",
    "Lentils/Dal",
    "Wheat Flour",
    "Curd/Yogurt",
    "Lemon",
    "Green Chilli",
    "Coriander",
]

# Editorial type and warm, high-contrast styling.
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        :root {
            --page: #FAF8F5;
            --card: #FFFFFF;
            --espresso: #1C1917;
            --slate: #57534E;
            --line: #E7E5E4;
            --accent: #EA580C;
            --herb: #15803D;
            --amber: #D97706;
        }
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background: var(--page) !important;
            color: var(--espresso) !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }
        h1, h2, h3, h4, .hero-banner h1, .recipe-title {
            font-family: 'Playfair Display', Georgia, serif !important;
            color: var(--espresso) !important;
        }
        p, label, span, .stMarkdown, [data-testid="stWidgetLabel"] {
            color: var(--espresso);
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        [data-testid="stSidebar"] {
            background: #F1ECE5 !important;
            border-right: 1px solid #E7E0D6;
        }
        [data-testid="stSidebar"] > div { background: #F1ECE5 !important; }
        .sidebar-card {
            padding: 1.15rem;
            border-radius: 18px;
            color: #FFF7ED !important;
            background: linear-gradient(145deg, #29211C, #3B2A20);
            box-shadow: 0 8px 24px rgba(41, 33, 28, .14);
        }
        .sidebar-card * { color: #FFF7ED !important; }
        .sidebar-eyebrow { color: #FDBA74 !important; font-size: .68rem; font-weight: 800; letter-spacing: .13em; }
        .sidebar-card h3 { color: #FFF7ED !important; margin: .3rem 0 .25rem; }
        .sidebar-card p { color: #E7D9CE !important; font-size: .82rem; line-height: 1.55; }
        .spice-pills { display: flex; flex-wrap: wrap; gap: .35rem; margin: .7rem 0; }
        .spice-pill { padding: .28rem .5rem; border: 1px solid rgba(255,255,255,.18); border-radius: 999px; color: #FFE7D1 !important; background: rgba(255,255,255,.08); font-size: .68rem; }
        .how-step { display: flex; gap: .55rem; margin: .48rem 0; color: #F1E7DF !important; font-size: .77rem; }
        .how-step b { color: #FDBA74 !important; }
        .hero-banner {
            position: relative;
            overflow: hidden;
            padding: clamp(1.6rem, 4vw, 3rem);
            margin: .2rem 0 1.7rem;
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 24px;
            color: #FFF7ED !important;
            background: radial-gradient(circle at 85% 15%, rgba(234,88,12,.38), transparent 30%), linear-gradient(135deg, #1C1917 0%, #431407 55%, #9A3412 100%);
            box-shadow: 0 18px 45px rgba(67,20,7,.18);
        }
        .hero-banner * { color: #FFF7ED !important; }
        .hero-badge { display: inline-block; padding: .42rem .7rem; border: 1px solid rgba(255,237,213,.26); border-radius: 999px; background: rgba(255,255,255,.08); color: #FED7AA !important; font-size: .68rem; font-weight: 800; letter-spacing: .12em; }
        .hero-banner h1 { margin: .85rem 0 .35rem; color: #FFF7ED !important; font-size: clamp(2.35rem, 5vw, 4rem); line-height: 1.04; letter-spacing: -.04em; }
        .hero-banner p { max-width: 46rem; margin: 0; color: #F5E7DC !important; font-size: 1rem; line-height: 1.65; }
        .hero-note { margin-top: 1rem; color: #FDBA74 !important; font-size: .78rem; font-weight: 700; letter-spacing: .04em; }
        .section-kicker { margin: .2rem 0 .3rem; color: var(--accent) !important; font-size: .72rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
        .section-title { margin: 0 0 .25rem; color: var(--espresso) !important; font-size: 1.65rem; font-weight: 750; }
        .section-help { color: var(--slate) !important; margin-bottom: .85rem; }
        [data-testid="stVerticalBlockBorderWrapper"] { border: 1px solid var(--line) !important; border-radius: 16px !important; background: var(--card) !important; box-shadow: 0 4px 20px rgba(0,0,0,.05) !important; }
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
        [data-testid="stTextInput"] [data-baseweb="input"] {
            min-height: 2.9rem;
            border: 1px solid #D6D3D1 !important;
            border-radius: 12px !important;
            background: #FFFFFF !important;
            box-shadow: none !important;
        }
        [data-testid="stMultiSelect"] [data-baseweb="select"] *,
        [data-testid="stTextInput"] input { color: #1C1917 !important; background-color: #FFFFFF !important; }
        [data-testid="stTextInput"] input::placeholder { color: #78716C !important; }
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div, [data-testid="stSelectbox"] div[data-baseweb="select"] > div { background: #FFFFFF !important; border: 1px solid #D6D3D1 !important; border-radius: 12px !important; }
        div.stButton > button { min-height: 2.75rem; border-radius: 12px; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; }
        div.stButton > button[kind="primary"] { background: #EA580C; border: 1px solid #EA580C; color: #FFFFFF !important; font-weight: 800 !important; }
        div.stButton > button[kind="primary"]:hover { background: #C2410C; border-color: #C2410C; }
        div.stButton > button[kind="secondary"] { background: #FFFFFF !important; border: 1px solid #EA580C !important; color: #1C1917 !important; }
        div.stButton > button[kind="secondary"] span { color: #1C1917 !important; }
        .ingredient-summary { padding: .95rem 1.1rem; margin: .65rem 0 1.25rem; border: 1px solid #FED7AA; border-radius: 14px; background: #FFF7ED; color: #7C2D12 !important; }
        .ingredient-summary * { color: #7C2D12 !important; }
        .active-pantry-strip { display: flex; flex-wrap: wrap; align-items: center; gap: .6rem; padding: .82rem 1rem; margin: .85rem 0 .9rem; border: 1px solid #E7E5E4; border-radius: 14px; background: #FFFFFF; box-shadow: 0 3px 12px rgba(28,25,23,.04); }
        .active-pantry-label { color: #57534E !important; font-size: .76rem; font-weight: 800; }
        .active-pantry-pills { display: flex; flex-wrap: wrap; gap: .35rem; }
        .active-pantry-pill { padding: .27rem .55rem; border-radius: 999px; color: #166534 !important; background: #DCFCE7; font-size: .72rem; font-weight: 700; }
        .zero-waste-callout { margin-top: 1.15rem; padding: .78rem .85rem; border-left: 3px solid #D97706; border-radius: 0 10px 10px 0; background: #FFFBEB; color: #78350F !important; font-size: .76rem; line-height: 1.5; }
        .zero-waste-callout strong { color: #92400E !important; }
        .recipe-card { height: 100%; overflow: hidden; border: 1px solid #E7E5E4; border-radius: 16px; background: #FFFFFF; box-shadow: 0 8px 24px rgba(28,25,23,.055); transition: transform .2s ease, box-shadow .2s ease; }
        .recipe-card:hover { transform: translateY(-4px); box-shadow: 0 16px 32px rgba(28,25,23,.12); }
        .card-accent { height: 4px; background: #EA580C; }
        .accent-2 .card-accent { background: #15803D; }
        .accent-3 .card-accent { background: #D97706; }
        .recipe-card-body { padding: 1.2rem 1.25rem 1.35rem; }
        .recipe-number { color: #78716C !important; font-size: .67rem; font-weight: 800; letter-spacing: .14em; }
        .recipe-title { min-height: 3.4rem; margin: .45rem 0 .45rem; font-size: 1.48rem; line-height: 1.2; }
        .recipe-tagline { min-height: 3.3rem; margin: 0 0 .95rem; color: #57534E !important; font-size: .84rem; font-style: italic; line-height: 1.55; }
        .recipe-meta { display: flex; flex-wrap: wrap; gap: .4rem; margin: .85rem 0 1.15rem; }
        .meta-pill { display: inline-flex; align-items: center; gap: .3rem; padding: .4rem .55rem; border: 1px solid #E7E5E4; border-radius: 999px; background: #FAF8F5; color: #44403C !important; font-size: .69rem; }
        .difficulty-pill { border: 0; font-weight: 800; }
        .difficulty-easy { color: #166534 !important; background: #DCFCE7; }
        .difficulty-medium { color: #92400E !important; background: #FEF3C7; }
        .difficulty-hard { color: #991B1B !important; background: #FEE2E2; }
        .card-section-title { margin: 1rem 0 .55rem; color: #292524 !important; font-size: .75rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
        .ingredient-list, .step-list { display: grid; gap: .48rem; margin: 0; padding: 0; list-style: none; }
        .ingredient-item { display: flex; align-items: flex-start; gap: .5rem; padding: .52rem .58rem; border-radius: 10px; background: #F0FDF4; color: #292524 !important; font-size: .78rem; line-height: 1.45; }
        .ingredient-check { flex: 0 0 auto; color: #15803D !important; font-weight: 900; }
        .step-item { display: flex; align-items: flex-start; gap: .62rem; color: #44403C !important; font-size: .78rem; line-height: 1.55; }
        .step-number { display: inline-flex; flex: 0 0 1.45rem; width: 1.45rem; height: 1.45rem; align-items: center; justify-content: center; border-radius: 50%; background: #FFF7ED; color: #C2410C !important; font-size: .68rem; font-weight: 800; }
        @media (max-width: 700px) { .hero-banner { border-radius: 18px; } .recipe-card-body { padding: 1rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)
# Session state stores selections and results so Reset can clear the whole form.
def clear_recipe_state():
    """Clear ingredient inputs and any recipe results."""
    st.session_state["ingredient_select"] = []
    st.session_state["custom_ingredients"] = ""
    st.session_state["recipes"] = []
    st.session_state["generated_ingredients"] = []
    st.session_state["generation_error"] = ""
    st.session_state["dietary_preference"] = "All"
    st.session_state["meal_type"] = "Any Meal"
    st.session_state["max_cooking_time"] = "Any Duration"


for state_key, initial_value in (
    ("recipes", []),
    ("generated_ingredients", []),
    ("generation_error", ""),
):
    if state_key not in st.session_state:
        st.session_state[state_key] = initial_value


QUICK_TRY_COMBOS = {
    "🥔 Aloo Tamatar": ["Potato", "Onion", "Tomato"],
    "🍚 Veg Pulao": ["Rice", "Peas", "Carrot", "Onion"],
    "🧀 Cheesy Toast": ["Bread", "Cheese", "Tomato"],
    "🥘 Kadai Paneer": ["Paneer", "Capsicum", "Onion", "Tomato"],
}


def apply_quick_try(ingredients):
    """Fill the selector with a preset and clear stale output."""
    st.session_state["ingredient_select"] = list(ingredients)
    st.session_state["custom_ingredients"] = ""
    st.session_state["recipes"] = []
    st.session_state["generated_ingredients"] = []
    st.session_state["generation_error"] = ""

# Project details and pantry assumptions live in the sidebar.
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-eyebrow">B.TECH GENAI MINI PROJECT</div>
            <h3>SmartRecipe AI</h3>
            <p>Roll No. 54<br>Turn everyday ingredients into thoughtful, low-waste meals.</p>
            <div class="sidebar-eyebrow">PANTRY BASICS ASSUMED</div>
            <div class="spice-pills">
                <span class="spice-pill">Salt</span><span class="spice-pill">Black pepper</span>
                <span class="spice-pill">Red chilli</span><span class="spice-pill">Turmeric</span>
                <span class="spice-pill">Cumin</span><span class="spice-pill">Cooking oil</span>
                <span class="spice-pill">Water</span>
            </div>
            <div class="sidebar-eyebrow" style="margin-top:1.05rem">HOW IT WORKS</div>
            <div class="how-step"><b>01</b><span>Choose what is already in your kitchen.</span></div>
            <div class="how-step"><b>02</b><span>Chef AI creates three ingredient-aware ideas.</span></div>
            <div class="how-step"><b>03</b><span>Cook, enjoy, and waste less.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="hero-banner">
        <span class="hero-badge">AI-POWERED ZERO-WASTE KITCHEN • ROLL NO. 54</span>
        <h1>SmartRecipe AI</h1>
        <p>Make something wonderful with what you already have. Personalised recipe ideas, less food waste, and more joy at the table.</p>
        <div class="hero-note">Good food starts with a well-used pantry.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not GEMINI_API_KEY:
    st.error(
        "Your Gemini API key is missing. Add GEMINI_API_KEY to the project's .env file, "
        "save it, then restart the app. Your key is never shown on this page."
    )

st.markdown('<div class="section-kicker">Start with your pantry</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">What sounds good today?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-help">Choose what you have on hand. Add anything else in the text field.</div>',
    unsafe_allow_html=True,
)

with st.container(border=True, key="pantry_selector"):
    st.markdown("### 🧺 Pantry Selector")
    st.caption("Pick a quick combination or build your own ingredient list.")
    st.markdown("**Quick Try Combos**")
    quick_columns = st.columns(4, gap="small")
    for (combo_name, combo_ingredients), combo_column in zip(QUICK_TRY_COMBOS.items(), quick_columns):
        combo_key = re.sub(r"[^a-z0-9]+", "_", combo_name.casefold()).strip("_")
        with combo_column:
            st.button(
                combo_name,
                key=f"quick_try_{combo_key}",
                on_click=apply_quick_try,
                args=(combo_ingredients,),
                use_container_width=True,
            )

    preference_columns = st.columns(3, gap="small")
    with preference_columns[0]:
        dietary_preference = st.selectbox(
            "Dietary Preference",
            ["All", "Pure Veg", "Eggetarian", "Non-Veg"],
            key="dietary_preference",
        )
    with preference_columns[1]:
        meal_type = st.selectbox(
            "Meal Type",
            ["Any Meal", "Breakfast", "Lunch / Dinner", "Quick Snack"],
            key="meal_type",
        )
    with preference_columns[2]:
        max_cooking_time = st.selectbox(
            "Max Cooking Time",
            ["Any Duration", "Under 15 mins", "Under 30 mins", "Under 45 mins"],
            key="max_cooking_time",
        )

    st.multiselect(
        "Choose ingredients",
        options=INGREDIENT_OPTIONS,
        key="ingredient_select",
        placeholder="Search and select ingredients…",
        help="Select every ingredient you want the recipes to use.",
    )
    st.text_input(
        "Add your own ingredients",
        key="custom_ingredients",
        placeholder="sweet corn, butter, oregano",
        help="Enter extra ingredients separated by commas.",
    )
def collect_ingredients(selected, custom_text):
    """Combine selected and typed ingredients while preserving their order."""
    combined = []
    seen = set()
    for ingredient in list(selected) + custom_text.split(","):
        cleaned = " ".join(ingredient.strip().split())
        normalized = cleaned.casefold()
        if cleaned and normalized not in seen:
            combined.append(cleaned)
            seen.add(normalized)
    return combined


def make_recipe_prompt(ingredients, preferences):
    """Build an ingredient-only recipe request shaped by user preferences."""
    ingredients_text = ", ".join(ingredients)
    return f"""Suggest exactly 3 distinct recipes using ONLY the user's provided ingredients plus basic spices/pantry essentials (salt, pepper, turmeric, chilli powder, cumin, basic oil, water). Do NOT silently introduce any extra vegetables, meats, dairy, grains, or main ingredients not listed by the user.

User-provided ingredients: {ingredients_text}

Cooking preferences: dietary preference={preferences['dietary_preference']}; meal type={preferences['meal_type']}; maximum cooking time={preferences['max_cooking_time']}.
Use the dietary preference to guide combinations among the provided ingredients; use meal type and maximum cooking time to guide recipe style and timing. Preferences never authorize adding ingredients. If they cannot be met with the provided ingredients and basic pantry staples, explain the limitation briefly and still use only the allowed ingredients.

The only additional ingredients allowed are {BASIC_PANTRY}. Give each recipe a short appetizing description, prep and cook times, difficulty (Easy, Medium, or Hard), servings as a string (for example, "2 servings"), calories as a string (for example, "~280 kcal / serving"), one short practical zero_waste_tip, approximate ingredient quantities, and clear numbered instructions. Return only valid JSON without markdown fences. Use a top-level object with a "recipes" list of exactly 3 recipe objects. Each recipe must include name, description, prep_time, cook_time, difficulty, servings, calories, zero_waste_tip, ingredients_used, and instructions. A JSON list of the 3 recipes is also acceptable."""

def clean_error_detail(error):
    """Return a readable error message without a traceback."""
    detail = getattr(error, "message", None) or str(error)
    return re.sub(r"\s+", " ", str(detail)).strip()


class RecipeGenerationError(Exception):
    """Collect the error message for each model that could not generate recipes."""

    def __init__(self, failures):
        self.failures = failures
        details = "\n".join(f"{model_name}: {message}" for model_name, message in failures)
        super().__init__(details)


def parse_recipe_response(response_text):
    """Remove optional Markdown fences and accept either supported JSON shape."""
    if not response_text or not response_text.strip():
        raise ValueError("Gemini returned an empty response.")

    cleaned_text = re.sub(
        r"^\s*```(?:json)?\s*", "", response_text.strip(), flags=re.IGNORECASE
    )
    cleaned_text = re.sub(r"\s*```\s*$", "", cleaned_text)
    data = json.loads(cleaned_text)

    if isinstance(data, list):
        recipes = data
    elif isinstance(data, dict):
        recipes = data.get("recipes")
    else:
        recipes = None

    if not isinstance(recipes, list) or len(recipes) != 3:
        raise ValueError("The response must contain exactly three recipes.")
    if not all(isinstance(recipe, dict) for recipe in recipes):
        raise ValueError("Each recipe in the response must be a JSON object.")
    return recipes


def generate_recipes(ingredients, preferences):
    """Try the configured models in order and retain each model's failure detail."""
    try:
        client = genai.Client()
    except Exception as exc:
        raise RecipeGenerationError(
            [("client initialization", clean_error_detail(exc))]
        ) from exc

    prompt = make_recipe_prompt(ingredients, preferences)
    failures = []

    for model_name in MODEL_FALLBACKS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )
            return parse_recipe_response(response.text)
        except Exception as exc:
            failures.append((model_name, clean_error_detail(exc)))

    raise RecipeGenerationError(failures)

active_ingredients = collect_ingredients(
    st.session_state.get("ingredient_select", []),
    st.session_state.get("custom_ingredients", ""),
)
active_pantry_pills = "".join(
    f"<span class='active-pantry-pill'>{escape(item)}</span>"
    for item in active_ingredients
)
if not active_pantry_pills:
    active_pantry_pills = "<span class='active-pantry-pill'>Choose ingredients to begin</span>"
st.markdown(
    f"<div class='active-pantry-strip'><span class='active-pantry-label'>🧺 Active Pantry ({len(active_ingredients)} items)</span><div class='active-pantry-pills'>{active_pantry_pills}</div></div>",
    unsafe_allow_html=True,
)

button_col, reset_col = st.columns([1, 1], gap="medium")
with button_col:
    generate_clicked = st.button(
        "Generate Recipes",
        type="primary",
        use_container_width=True,
    )
with reset_col:
    st.button(
        "Reset / Clear Ingredients",
        on_click=clear_recipe_state,
        use_container_width=True,
    )

if generate_clicked:
    ingredients_to_use = collect_ingredients(
        st.session_state.get("ingredient_select", []),
        st.session_state.get("custom_ingredients", ""),
    )
    if not ingredients_to_use:
        st.warning("Please select or enter at least one ingredient before generating recipes.")
    elif not GEMINI_API_KEY:
        st.error("Add GEMINI_API_KEY to your .env file before generating recipes.")
    else:
        st.session_state["generation_error"] = ""
        try:
            with st.spinner("Chef AI is crafting 3 zero-waste recipes..."):
                preferences = {
                    "dietary_preference": dietary_preference,
                    "meal_type": meal_type,
                    "max_cooking_time": max_cooking_time,
                }
                st.session_state["recipes"] = generate_recipes(ingredients_to_use, preferences)
                st.session_state["generated_ingredients"] = ingredients_to_use
        except RecipeGenerationError as exc:
            error_lines = "\n".join(
                f"- **{model_name}**: {message}"
                for model_name, message in exc.failures
            )
            st.session_state["generation_error"] = (
                "All Gemini model attempts failed:\n\n" + error_lines
            )
        except Exception as exc:
            st.session_state["generation_error"] = (
                f"Recipe generation failed: {clean_error_detail(exc)}"
            )
if st.session_state.get("generation_error"):
    st.error(st.session_state["generation_error"])

recipes = st.session_state.get("recipes", [])
def strip_instruction_number(instruction):
    """Remove existing numeric prefixes so the visual badges number steps once."""
    cleaned = str(instruction).strip()
    while re.match(r"^(?:(?:step)\s*)?\d+\s*[.)\-:]\s*", cleaned, flags=re.IGNORECASE):
        cleaned = re.sub(r"^(?:(?:step)\s*)?\d+\s*[.)\-:]\s*", "", cleaned, count=1, flags=re.IGNORECASE)
    return cleaned


def make_recipe_download(recipes, ingredients):
    """Build a readable plain-text copy of the generated recipes."""
    lines = [
        "SMARTRECIPE AI — YOUR RECIPES",
        "=" * 38,
        "Ingredients used: " + ", ".join(ingredients),
        "",
    ]
    for recipe_number, recipe in enumerate(recipes, start=1):
        lines.extend([
            f"RECIPE {recipe_number:02d}: {recipe.get('name', 'Recipe')}",
            str(recipe.get("description", "")),
            f"Prep: {recipe.get('prep_time', '—')} | Cook: {recipe.get('cook_time', '—')} | Difficulty: {recipe.get('difficulty', '—')}",
            f"Servings: {recipe.get('servings', 'Not specified')} | Calories: {recipe.get('calories', 'Not specified')}",
            f"Zero-waste tip: {recipe.get('zero_waste_tip', 'Use suitable prep scraps in another meal.')}",
            "",
            "INGREDIENTS USED",
        ])
        lines.extend(f"• {item}" for item in recipe.get("ingredients_used", []))
        lines.extend(["", "STEP-BY-STEP METHOD"])
        lines.extend(
            f"{step_number}. {strip_instruction_number(step)}"
            for step_number, step in enumerate(recipe.get("instructions", []), start=1)
        )
        lines.append("")
    return "\n".join(lines)


recipes = st.session_state.get("recipes", [])
if recipes:
    used_ingredients = st.session_state.get("generated_ingredients", []) or []
    ingredient_summary = escape(", ".join(str(item) for item in used_ingredients))
    st.markdown(
        f"<div class='ingredient-summary'><strong>🌿 Recipes made with:</strong> {ingredient_summary}</div>",
        unsafe_allow_html=True,
    )
    view_mode = st.radio(
        "Recipe view",
        ["Side-by-Side Cards", "Detailed Recipe Tabs"],
        horizontal=True,
        key="recipe_view",
    )

    def build_recipe_card(recipe, index):
        """Render a rich recipe card while tolerating older partial responses."""
        recipe_name = escape(str(recipe.get("name") or "A tasty idea"))
        description = escape(str(recipe.get("description") or ""))
        prep_time = escape(str(recipe.get("prep_time") or "—"))
        cook_time = escape(str(recipe.get("cook_time") or "—"))
        servings = escape(str(recipe.get("servings") or "Not specified"))
        calories = escape(str(recipe.get("calories") or "Not specified"))
        zero_waste_tip = escape(
            str(recipe.get("zero_waste_tip") or "Save suitable prep scraps for another meal.")
        )
        difficulty = str(recipe.get("difficulty") or "Medium").strip()
        difficulty_class = {
            "easy": "difficulty-easy",
            "medium": "difficulty-medium",
            "hard": "difficulty-hard",
        }.get(difficulty.casefold(), "difficulty-medium")
        difficulty_label = escape(difficulty)

        ingredient_items = recipe.get("ingredients_used") or []
        if isinstance(ingredient_items, str):
            ingredient_items = [ingredient_items]
        ingredient_markup = "".join(
            f"<li class='ingredient-item'><span class='ingredient-check'>✓</span><span>{escape(str(item))}</span></li>"
            for item in ingredient_items
        ) or "<li class='ingredient-item'>Ingredient details unavailable.</li>"

        instruction_items = recipe.get("instructions") or []
        if isinstance(instruction_items, str):
            instruction_items = [instruction_items]
        instruction_markup = "".join(
            "<li class='step-item'>"
            f"<span class='step-number'>{step_number}</span>"
            f"<span>{escape(strip_instruction_number(step))}</span></li>"
            for step_number, step in enumerate(instruction_items, start=1)
        ) or "<li class='step-item'>Cooking steps unavailable.</li>"

        return f"""
        <article class="recipe-card {['accent-1', 'accent-2', 'accent-3'][index % 3]}">
            <div class="card-accent"></div>
            <div class="recipe-card-body">
                <div class="recipe-number">RECIPE {index + 1:02d}</div>
                <h3 class="recipe-title">{recipe_name}</h3>
                <p class="recipe-tagline">{description}</p>
                <div class="recipe-meta">
                    <span class="meta-pill">⏱ <strong>Prep</strong> {prep_time}</span>
                    <span class="meta-pill">♨ <strong>Cook</strong> {cook_time}</span>
                    <span class="meta-pill difficulty-pill {difficulty_class}">{difficulty_label}</span>
                    <span class="meta-pill">🍽 <strong>Serves</strong> {servings}</span>
                    <span class="meta-pill">✦ <strong>Energy</strong> {calories}</span>
                </div>
                <div class="card-section-title">Ingredients Used</div>
                <ul class="ingredient-list">{ingredient_markup}</ul>
                <div class="card-section-title">Step-by-Step Method</div>
                <ol class="step-list">{instruction_markup}</ol>
                <div class="zero-waste-callout"><strong>♻ Chef's zero-waste tip</strong><br>{zero_waste_tip}</div>
            </div>
        </article>
        """

    if view_mode == "Side-by-Side Cards":
        recipe_columns = st.columns(3, gap="large")
        for index, (column, recipe) in enumerate(zip(recipe_columns, recipes)):
            with column:
                st.markdown(build_recipe_card(recipe, index), unsafe_allow_html=True)
    else:
        tab_labels = [f"Recipe {index + 1:02d}" for index in range(len(recipes))]
        recipe_tabs = st.tabs(tab_labels)
        for index, (recipe_tab, recipe) in enumerate(zip(recipe_tabs, recipes)):
            with recipe_tab:
                st.markdown(build_recipe_card(recipe, index), unsafe_allow_html=True)

    st.download_button(
        "⬇ Download Recipes (.txt)",
        data=make_recipe_download(recipes, used_ingredients),
        file_name="smartrecipe-ai-recipes.txt",
        mime="text/plain",
        use_container_width=True,
    )
