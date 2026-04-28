from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from ddgs import DDGS
import re

app = FastAPI()

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# INPUT MODEL
# =========================
class RequestData(BaseModel):
    domain: str
    country: str
    max_results: int = 5


# =========================
# CLEANING FUNCTIONS
# =========================
BAD_WORDS = [
    "top", "list", "best", "guide", "ranking",
    "wikipedia", "news", "article", "definition",
    "companies in", "list of", "how to"
]


def is_bad_title(text: str) -> bool:
    low = text.lower()
    return any(b in low for b in BAD_WORDS)


def extract_name(title: str):
    if not title:
        return None

    # couper les titres inutiles
    name = title.split("-")[0].split("|")[0].strip()

    # filtre longueur
    if len(name) < 2:
        return None

    # supprimer caractères spéciaux
    name = re.sub(r"[^\w\s&.,'-]", "", name).strip()

    # filtrer junk
    if is_bad_title(name):
        return None

    return name


# =========================
# SEARCH ENGINE
# =========================
def search_companies(query: str, limit: int):
    results = []

    with DDGS() as ddgs:
        data = ddgs.text(query, max_results=limit * 5)

        for r in data:
            title = r.get("title", "")
            name = extract_name(title)

            if name:
                results.append(name)

            if len(results) >= limit:
                break

    return results


# =========================
# API ROUTE
# =========================
@app.get("/")
def home():
    return {"message": "Company Finder API Running 🚀"}


@app.post("/find-companies")
def find_companies(data: RequestData):

    queries = [
        f"{data.domain} companies in {data.country}",
        f"{data.domain} entreprises {data.country}",
        f"{data.domain} firms {data.country}",
        f"{data.country} {data.domain} companies"
    ]

    seen = set()
    final_results = []

    try:
        for q in queries:
            raw_results = search_companies(q, data.max_results)

            for company in raw_results:
                key = company.lower()

                if key not in seen:
                    seen.add(key)
                    final_results.append(company)

                if len(final_results) >= data.max_results:
                    break

            if len(final_results) >= data.max_results:
                break

    except Exception as e:
        return {"error": str(e)}

    return {
        "domain": data.domain,
        "country": data.country,
        "results": final_results
    }
