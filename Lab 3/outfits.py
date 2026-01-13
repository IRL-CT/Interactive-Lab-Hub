# outfits.py
THEMES = {
    "Sports": [
        "White Lululemon Scuba full-zip hoodie with white Softstreme wide-leg pants.",
        "Pink short-sleeve top with black Lululemon wide-leg yoga pants.",
        "Purple short-sleeve top with blue-purple athletic shorts.",
    ],
    "Social": [
        "White tank with black wide-leg pants.",
        "Gray tank with blue wide-leg jeans and black boots.",
        "Sleeveless plaid shirt with a plaid skirt.",
    ],
    "Color": [
        "Red: red sweater over a white tank with coffee-colored casual pants.",
        "Blue: blue Beta jacket over a bluish-purple tee with blue wide-leg jeans.",
        "Yellow: beige short-sleeve top with coffee-colored casual pants.",
    ],
    "Interview": [
        "Khaki shirt with a khaki skirt.",
        "Beige top with black jeans.",
        "White tank with black suit pants and a green blazer.",
    ],
    "Daily": [
        "Gray skirt with black boots.",
        "Blue sweater with blue wide-leg jeans and a brown wool coat.",
        "Beige short-sleeve top with a brown midi skirt.",
    ],
}

ORDER = ["Sports", "Social", "Color", "Interview", "Daily"]

def pick_daily_by_temp(temp_c: float) -> str:
    if temp_c >= 25:
        return THEMES["Daily"][2]
    if temp_c <= 12:
        return THEMES["Daily"][1]
    return THEMES["Daily"][0]

def resolve_theme_from_query(q: str) -> str:
    s = q.lower()
    if "sport" in s or "gym" in s or "workout" in s: return "Sports"
    if "social" in s or "party" in s or "hang out" in s: return "Social"
    if "interview" in s or "job" in s: return "Interview"
    if "color" in s or "colour" in s: return "Color"
    if "school" in s or "class" in s or "daily" in s or "today" in s: return "Daily"
    return "Daily"

def color_from_query(q: str) -> str|None:
    s = q.lower()
    if "red" in s: return "red"
    if "blue" in s: return "blue"
    if "yellow" in s: return "yellow"
    return None

def answer_for_query(q: str, temp_c: float|None = None) -> str:
    theme = resolve_theme_from_query(q)
    if theme == "Daily":
        if temp_c is None:
            return "For school today, try: " + THEMES["Daily"][0]
        return "For school today, try: " + pick_daily_by_temp(temp_c)
    if theme == "Sports":
        return "For sports today, try: " + THEMES["Sports"][0]
    if theme == "Social":
        return "For social today, try: " + THEMES["Social"][0]
    if theme == "Interview":
        return "For your interview, try: " + THEMES["Interview"][0]
    if theme == "Color":
        c = color_from_query(q)
        if c == "red":   return "For a red look, try: " + THEMES["Color"][0]
        if c == "blue":  return "For a blue look, try: " + THEMES["Color"][1]
        if c == "yellow":return "For a yellow look, try: " + THEMES["Color"][2]
        return "For a color-themed outfit, say red, blue, or yellow."
    return "Sorry, I didn't get the theme. Try sports, social, color, interview, or daily."

# ---- added: thin wrapper so router can import rule_answer ----
def rule_answer(q: str, temp_c: float|None = None) -> str:
    return answer_for_query(q, temp_c)
