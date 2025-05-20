from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper.generate_answer import generate_answer
import traceback

app = FastAPI(title="Nestlé Product Answer API")

class QueryRequest(BaseModel):
    query: str

class AnswerResponse(BaseModel):
    answer: str

@app.post("/answer", response_model=AnswerResponse)
def answer_question(request: QueryRequest):
    try:
        response = generate_answer(request.query)
        return {"answer": response}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

@app.get("/")
def health_check():
    return {"status": "OK"}
