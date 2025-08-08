import os
import json
import re
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai  # Gemini SDK
import time


BASE_DIR = os.path.dirname(__file__)
app = Flask(__name__, static_folder="static", template_folder="templates")

# Loading products from JSON file
def load_products():
    with open(os.path.join(BASE_DIR, "products.json"), "r", encoding="utf-8") as f:
        return json.load(f)

PRODUCTS = load_products()

# Routes
@app.route("/")
def index():
    categories = sorted({p["category"] for p in PRODUCTS})
    return render_template("index.html", categories=categories)

@app.route("/api/products")
def api_products():
    return jsonify(PRODUCTS)

@app.route("/api/smart_search", methods=["POST"])
def smart_search():
    payload = request.get_json() or {}
    query = (payload.get("query") or "").strip()
    category = (payload.get("category") or "").strip()
    max_price = payload.get("max_price", None)
    use_ai = payload.get("use_ai", True)

    try:
        max_price = float(max_price) if (max_price is not None and max_price != "") else None
    except Exception:
        max_price = None

    filtered = PRODUCTS
    if category:
        filtered = [p for p in filtered if p["category"].lower() == category.lower()]
    if max_price is not None:
        filtered = [p for p in filtered if float(p["price"]) <= max_price]

    if not query:
        return jsonify(filtered)

    gemini_key = os.getenv("GEMINI_API_KEY")
    if use_ai and gemini_key:
        print("DEBUG: Gemini API key found, calling Gemini AI...")
        try:
            start_time = time.time()
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            # Building a strict prompt emphasizing exact matching
            prompt = f"""
You are a strict product filtering assistant.

You are given this JSON list of products (each has "name", "category", "price", "rating", "description"):

{json.dumps(filtered)}

User query: "{query}"

INSTRUCTIONS:
- Return ONLY the products from the provided list that EXACTLY match ALL constraints in the query.
- Constraints include price (e.g., "under $30", "over $50"), category, and rating filters.
- Do NOT invent new products or alter any product details.
- Return ONLY a valid JSON array with the matching products.
- If no products match, return an empty JSON array.

Output the JSON array only, with no extra text or explanation.
"""

            response = model.generate_content(prompt)
            elapsed = time.time() - start_time
            print(f"DEBUG: Gemini AI responded in {elapsed:.2f} seconds")
            text = response.text.strip()
            print("DEBUG: Gemini raw response:", text)

            # Cleaning markdown code fences if any
            text = re.sub(r"^```json\s*", "", text, flags=re.I)
            text = re.sub(r"\s*```$", "", text)

            result = json.loads(text)

            # Strictly keeping only products present in filtered list 
            valid_names = {p["name"] for p in filtered}
            result = [item for item in result if item.get("name") in valid_names]

            print(f"DEBUG: After AI filtering, {len(result)} products found")

            # Applying local strict filtering again for safety
            result = local_search(query, result)

            print(f"DEBUG: After local re-filtering, {len(result)} products remain")

            return jsonify(result)

        except Exception as e:
            print("Gemini error:", e)
            print("DEBUG: Falling back to local search due to error")
            return jsonify(local_search(query, filtered))

    # No AI or no key: fallback local search
    print("DEBUG: Using local fallback search")
    return jsonify(local_search(query, filtered))


# Local fallback search (strict)
def local_search(query, products_list):
    q = query.lower()

    # Parsing price constraints
    under = re.search(r"under\s*\$?(\d+)", q)
    below = re.search(r"below\s*\$?(\d+)", q)
    over = re.search(r"over\s*\$?(\d+)", q)
    maxp = None
    minp = None
    if under:
        maxp = float(under.group(1))
    if below:
        maxp = float(below.group(1))
    if over:
        minp = float(over.group(1))

    # Parsing rating constraints
    min_rating = None
    m = re.search(r"rating\s*(?:at least|>=)?\s*(\d(?:\.\d)?)", q)
    if m:
        try:
            min_rating = float(m.group(1))
        except:
            min_rating = None
    elif "good reviews" in q or "high rating" in q or "highly rated" in q:
        min_rating = 4.0
    elif re.search(r"(\d(?:\.\d)?)\s*\+?\s*stars?", q):
        mm = re.search(r"(\d(?:\.\d)?)\s*\+?\s*stars?", q)
        try:
            min_rating = float(mm.group(1))
        except:
            min_rating = None

    # Detecting category constraint from query matching available categories strictly
    cat = None
    categories = {p["category"].lower() for p in products_list}
    for c in categories:
        # Matching whole word category 
        if re.search(rf"\b{re.escape(c)}\b", q):
            cat = c
            break

    results = []
    for p in products_list:
        ok = True
        price = float(p["price"])
        rating = float(p.get("rating", 0))

        if maxp is not None and price > maxp:
            ok = False
        if minp is not None and price < minp:
            ok = False
        if min_rating is not None and rating < min_rating:
            ok = False
        if cat and p["category"].lower() != cat:
            ok = False

        if not ok:
            continue

        # Checking if product text contains all tokens from query for strict match
        text_blob = (p["name"] + " " + p["description"] + " " + p["category"]).lower()
        query_tokens = [tok for tok in q.split() if tok]

        # Require all tokens to be present in text_blob or allow if constraints only
        if all(tok in text_blob for tok in query_tokens) or (cat or maxp is not None or min_rating is not None or minp is not None):
            results.append(p)

    # Removing duplicates strictly
    seen = set()
    unique = []
    for r in results:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append(r)
    return unique


# Main
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
