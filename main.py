# ✅ Updated app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper.generate_answer import generate_answer
import traceback
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

app = FastAPI(title="Nestlé Product Answer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class AnswerItem(BaseModel):
    title: str
    type: str
    description: str
    url: str
    category: Optional[str] = None
    weight: Optional[str] = None
    nutrition: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    top_ingredients: Optional[List[str]] = None

class AnswerResponse(BaseModel):
    summary: str
    items: List[AnswerItem]
    followups: List[str]

def clean_response_structure(raw):
    cleaned = {
        "summary": raw.get("summary", "").strip(),
        "items": [],
        "followups": raw.get("followups", []),
    }
    for item in raw.get("items", []):
        item.pop("followups", None)
        cleaned["items"].append(item)
    return cleaned

@app.post("/answer", response_model=AnswerResponse)
def answer_question(request: QueryRequest):
    try:
        raw = generate_answer(request.query)
        structured = clean_response_structure(raw)  # ✅ removed unnecessary json.loads()
        return {
            "summary": structured.get("summary", ""),
            "items": structured.get("items", []),
            "followups": structured.get("followups", [])
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

@app.get("/")
def health_check():
    return {"status": "OK"}
