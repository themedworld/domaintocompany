from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from ddgs import DDGS

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    domain: str
    country: str
    max_results: int = 5

@app.get("/")
def home():
    return {"message": "Company Finder API Running"}

@app.post("/find-companies")
def find_companies(data: RequestData):

    query = f"{data.domain} companies in {data.country}"
    rows = []
    seen = set()

    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=data.max_results * 3)

            for r in results:
                name = r["title"].split("-")[0].split("|")[0].strip()

                if name.lower() not in seen:
                    seen.add(name.lower())

                    rows.append({
                        "company": name,
                        "url": r["href"]
                    })

                if len(rows) >= data.max_results:
                    break

    except Exception as e:
        return {"error": str(e)}

    return {"results": rows}
