#asked ChatGPT to help me get code to query wikipedia for food items and download a relevant image

import os, re, requests
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urlparse

UA = "RPi5WikipediaBot/1.0 (xia14@att.net)"
session = requests.Session()
session.headers.update({"User-Agent": UA})
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=5, backoff_factor=0.4, status_forcelist=[429,500,502,503,504],
    allowed_methods=["GET","HEAD","OPTIONS"]
)))

GOOD_EXTS = [".jpg", ".jpeg", ".png", ".webp"]
FOOD_CATEGORY_HINTS = [
    "food", "foods", "dishes", "cuisine", "cuisines", "beverages", "drinks",
    "desserts", "confectionery", "baked goods", "snack foods", "ingredients",
    "condiments", "sauces", "soups", "stews", "salads", "rice dishes",
    "noodle dishes", "pasta dishes", "meat dishes", "seafood dishes", "bread"
]

def sanitize_filename(title: str) -> str:
    safe = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    safe = safe.replace(" ", "_")

    return (safe or "image")[:120]

# ---------- Food-first title resolver ----------
def resolve_food_title(query: str):
    """
    1) Try exact pages with food suffixes.
    2) Else search top results and pick first non-disambiguation with food-like categories.
    Returns the chosen title or None.
    """
    api = "https://en.wikipedia.org/w/api.php"

    # 1) Try exact common foody suffixes
    suffixes = [" (food)", " (dish)", " (cuisine)", " (drink)", " (beverage)", " (ingredient)"]
    exact_titles = [query] + [query + s for s in suffixes]

    # Batch check exact titles; get pageprops (for disambiguation) & categories
    params = {
        "action": "query", "prop": "pageprops|categories", "cllimit": "max", "clshow": "!hidden",
        "titles": "|".join(exact_titles), "redirects": 1, "format": "json"
    }
    try:
        r = session.get(api, params=params, timeout=10); r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        # Prefer the earliest exact match that isn't a disambiguation and looks food-like
        def looks_foody(page):
            if "pageprops" in page and "disambiguation" in page["pageprops"]:
                return False
            cats = [c["title"].split(":",1)[-1].lower() for c in page.get("categories", [])]
            return any(any(h in c for h in FOOD_CATEGORY_HINTS) for c in cats)

        # Check the titles in our priority order
        by_title = {p.get("title",""): p for p in pages.values() if "missing" not in p}
        for t in exact_titles:
            p = by_title.get(t)
            if p and looks_foody(p):
                return p["title"]
        # Accept a non-disambig exact even if categories aren’t loaded/food-like
        for t in exact_titles:
            p = by_title.get(t)
            if p and not ("pageprops" in p and "disambiguation" in p["pageprops"]):
                return p["title"]
    except requests.RequestException:
        pass

    # 2) Short search fallback (top 5), then pick first non-disambig with food-like categories
    try:
        r = session.get(api, params={
            "action":"query","list":"search","srsearch":query,"srlimit":5,"srnamespace":0,"format":"json"
        }, timeout=10); r.raise_for_status()
        hits = r.json().get("query", {}).get("search", [])
        if not hits:
            return None
        titles = "|".join(h["title"] for h in hits)
        r2 = session.get(api, params={
            "action":"query","prop":"pageprops|categories","cllimit":"max","clshow":"!hidden",
            "titles":titles,"redirects":1,"format":"json"
        }, timeout=10); r2.raise_for_status()
        pages = r2.json().get("query", {}).get("pages", {})

        def is_good(page):
            if "pageprops" in page and "disambiguation" in page["pageprops"]:
                return False
            cats = [c["title"].split(":",1)[-1].lower() for c in page.get("categories", [])]
            return any(any(h in c for h in FOOD_CATEGORY_HINTS) for c in cats)

        # Keep original search order
        title_map = {p.get("title",""): p for p in pages.values() if "missing" not in p}
        for h in hits:
            p = title_map.get(h["title"])
            if p and is_good(p):
                return p["title"]
        # Fallback: first non-disambig
        for h in hits:
            p = title_map.get(h["title"])
            if p and not ("pageprops" in p and "disambiguation" in p["pageprops"]):
                return p["title"]
        return hits[0]["title"]
    except requests.RequestException:
        return None

# ---------- Food-friendly image pick ----------
def pick_wiki_image_url(title: str):
    api = "https://en.wikipedia.org/w/api.php"
    candidates = []

    for params in [
        {"action":"query","titles":title,"prop":"pageimages","piprop":"original",
         "redirects":1,"format":"json"},
        {"action":"query","titles":title,"prop":"pageimages","pithumbsize":1200,
         "redirects":1,"format":"json"},
    ]:
        try:
            r = session.get(api, params=params, timeout=10); r.raise_for_status()
            for page in r.json().get("query", {}).get("pages", {}).values():
                if "original" in page: candidates.append(page["original"]["source"])
                if "thumbnail" in page: candidates.append(page["thumbnail"]["source"])
        except requests.RequestException:
            pass

    if not candidates:
        return None

    # Prefer real photos (avoid SVG/diagrams/icons/logos)
    def score(u):
        name = os.path.basename(u.split("?")[0]).lower()
        ext = os.path.splitext(name)[1]
        s = 0
        if ext in GOOD_EXTS: s += 5
        bad_words = ["svg", "icon", "diagram", "logo", "map", "flag", "coat_of_arms", "symbol"]
        if any(b in name for b in bad_words): s -= 5
        # Light nudge for edible-y names
        if any(w in name for w in ["food","dish","cuisine","meal","cookie","cake","bread","fruit","vegetable","meat","sauce","soup","pasta","rice","noodle","salad"]):
            s += 2
        return s

    best = max(candidates, key=score)
    # Ensure a photo extension; if not, we’ll still download but name as .jpg
    return best

def download_image(url: str, path: str):
    r = session.get(url, timeout=15, allow_redirects=True, stream=True)
    if r.status_code != 200 or "image" not in r.headers.get("Content-Type","").lower():
        print("Failed to download image.")
        return False
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk: f.write(chunk)
    return True

# ---------- Main helper ----------
def get_food_image(spoken_phrase: str, save_dir="/home/pi/Documents/Interactive-Lab-Hub/Lab 3/ollama/fridgely/images"):
    os.makedirs(save_dir, exist_ok=True)
    title = resolve_food_title(spoken_phrase)
    if not title:
        print(f"No Wikipedia page found for: {spoken_phrase}")
        return None
    url = pick_wiki_image_url(title)
    if not url:
        print(f"No image found for: {title}")
        return None
    path = create_food_path(spoken_phrase, url, save_dir)
    print(path)
    if download_image(url, path):
        print(f"[{title}] -> {path}")
        return path
    print("Download failed.")
    return None

def create_food_path(title, url, ext=".jpg", save_dir="/home/pi/Documents/Interactive-Lab-Hub/Lab 3/ollama/fridgely/images"):
    ext = os.path.splitext(urlparse(url).path)[1].lower()  
    if ext not in GOOD_EXTS: ext = ".jpg"
    path = os.path.join(save_dir, sanitize_filename(title.lower()) + ext)
    return path

# Example:
if __name__ == "__main__":
    for food in ["Tomato", "Eggplant","spinach", "cabbage", "asparagus", "Milk", "Eggs", "Cheese", "Yogurt", "Butter"]:
        get_food_image(food)