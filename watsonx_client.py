"""
watsonx_client.py — IBM Watsonx.ai client wrapper.

Provides three high-level functions used by the Flask routes:
  • chat()                — conversational nutrition agent
  • analyse_nutrition()   — per-food calorie/macro breakdown
  • generate_meal_plan()  — personalised multi-day meal plan

All calls inject AGENT_INSTRUCTIONS from config.py as the system prompt.
"""

import json
import logging
import re

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

import config

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
#  Initialise the Watsonx.ai model once at import time
# ─────────────────────────────────────────────────────────────────
_credentials = Credentials(
    url=config.WATSONX_URL,
    api_key=config.IBM_API_KEY,
)

_model = ModelInference(
    model_id=config.WATSONX_MODEL_ID,
    credentials=_credentials,
    project_id=config.WATSONX_PROJECT_ID,
    params=config.WATSONX_PARAMS,
)


# ─────────────────────────────────────────────────────────────────
#  Internal helper — build a text prompt from messages
# ─────────────────────────────────────────────────────────────────
def _build_prompt(system: str, history: list[dict], user_message: str) -> str:
    """
    Assemble a prompt in Granite instruct format:
        <|system|> ... <|user|> ... <|assistant|> ...
    """
    parts = [f"<|system|>\n{system.strip()}\n"]
    for turn in history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        parts.append(f"<|{role}|>\n{content}\n")
    parts.append(f"<|user|>\n{user_message.strip()}\n<|assistant|>\n")
    return "".join(parts)


def _call_model(prompt: str) -> str:
    """Call the model and return the generated text, stripped of whitespace."""
    try:
        response = _model.generate_text(prompt=prompt)
        return response.strip()
    except Exception as exc:
        logger.error("Watsonx.ai call failed: %s", exc)
        return (
            "I'm having trouble connecting to the AI service right now. "
            "Please check your API credentials and try again."
        )


# ─────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────

def chat(
    user_message: str,
    profile: dict | None = None,
    history: list[dict] | None = None,
) -> str:
    """
    Send a chat message to the Nutrition Agent and return the reply.

    Args:
        user_message: The user's latest message.
        profile:      Optional family member profile dict for personalisation.
        history:      List of {role, content} dicts (max MAX_HISTORY_TURNS).

    Returns:
        The agent's reply as a plain string.
    """
    system = config.AGENT_INSTRUCTIONS

    if profile:
        bmi = round(
            profile["weight_kg"] / ((profile["height_cm"] / 100) ** 2), 1
        )
        profile_ctx = (
            f"\n\n[CURRENT USER PROFILE]\n"
            f"Name: {profile['name']}\n"
            f"Age: {profile['age']} years | Gender: {profile['gender']}\n"
            f"Weight: {profile['weight_kg']} kg | Height: {profile['height_cm']} cm | BMI: {bmi}\n"
            f"Activity Level: {profile['activity_level']}\n"
            f"Dietary Restrictions: {profile['dietary_restrictions'] or 'None'}\n"
            f"Health Goals: {profile['health_goals'] or 'General wellness'}\n"
            "Tailor all advice specifically to this person."
        )
        system = system + profile_ctx

    trimmed_history = (history or [])[-config.MAX_HISTORY_TURNS * 2:]
    prompt = _build_prompt(system, trimmed_history, user_message)
    return _call_model(prompt)


def analyse_nutrition(food_items: list[str]) -> dict:
    """
    Return a calorie and macronutrient breakdown for a list of food items.

    Args:
        food_items: e.g. ["2 chapati", "1 bowl dal", "100g paneer"]

    Returns:
        {
          "items": [
            {"name": "...", "calories": 0, "protein_g": 0,
             "carbs_g": 0, "fat_g": 0, "note": "..."},
            ...
          ],
          "total": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0},
          "raw": "..."   ← always present as fallback
        }
    """
    foods_str = "\n".join(f"- {item}" for item in food_items)
    prompt_text = (
        "Analyse the nutritional content of each food item listed below. "
        "Respond ONLY with a valid JSON object — no markdown, no explanation — "
        "in exactly this format:\n"
        '{"items":[{"name":"...","calories":0,"protein_g":0,"carbs_g":0,"fat_g":0,"note":"..."}]}'
        f"\n\nFood items:\n{foods_str}"
    )

    system = config.AGENT_INSTRUCTIONS
    prompt = _build_prompt(system, [], prompt_text)
    raw = _call_model(prompt)

    # Try to parse JSON; fall back gracefully
    try:
        # Extract first JSON object from the response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            items = data.get("items", [])
            total = {
                "calories":  sum(i.get("calories",  0) for i in items),
                "protein_g": sum(i.get("protein_g", 0) for i in items),
                "carbs_g":   sum(i.get("carbs_g",   0) for i in items),
                "fat_g":     sum(i.get("fat_g",     0) for i in items),
            }
            return {"items": items, "total": total, "raw": raw}
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Could not parse nutrition JSON: %s", exc)

    # Graceful fallback — return raw text for the UI to display
    return {"items": [], "total": {}, "raw": raw}


def generate_meal_plan(profile: dict, days: int = 7) -> str:
    """
    Generate a personalised meal plan for the given profile.

    Args:
        profile: Family member profile dict from db.py.
        days:    Number of days (1, 3, or 7).

    Returns:
        A formatted meal plan string.
    """
    bmi = round(
        profile["weight_kg"] / ((profile["height_cm"] / 100) ** 2), 1
    )
    prompt_text = (
        f"Create a detailed {days}-day personalised meal plan for:\n"
        f"- Name: {profile['name']}, Age: {profile['age']}, Gender: {profile['gender']}\n"
        f"- Weight: {profile['weight_kg']} kg, Height: {profile['height_cm']} cm, BMI: {bmi}\n"
        f"- Activity Level: {profile['activity_level']}\n"
        f"- Dietary Restrictions: {profile['dietary_restrictions'] or 'None'}\n"
        f"- Health Goals: {profile['health_goals'] or 'General wellness'}\n\n"
        "Format the plan exactly like this for each day:\n"
        "Day 1:\n"
        "  Breakfast: [dish] — [portion] — [approx calories]\n"
        "  Morning Snack: [dish] — [portion] — [approx calories]\n"
        "  Lunch: [dish] — [portion] — [approx calories]\n"
        "  Evening Snack: [dish] — [portion] — [approx calories]\n"
        "  Dinner: [dish] — [portion] — [approx calories]\n"
        "  Daily Total: ~[X] kcal | Protein: [X]g | Carbs: [X]g | Fat: [X]g\n\n"
        "Prioritise Indian foods. Include practical cooking tips where helpful."
    )

    system = config.AGENT_INSTRUCTIONS
    prompt = _build_prompt(system, [], prompt_text)
    return _call_model(prompt)
