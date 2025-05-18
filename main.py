from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API"))

app = FastAPI()

class SymptomInput(BaseModel):
    symptoms: str

class PrescriptionInput(BaseModel):
    text: str

class PreventivePlanInput(BaseModel):
    age: int
    gender: str
    conditions: List[str]

# Helper function to query Gemini
def generate_with_gemini(prompt: str):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

@app.post("/symptom-check")
async def symptom_check(data: SymptomInput):
    prompt = f"Given the symptoms: {data.symptoms}, list possible conditions and indicate urgency level (low, medium, high). Respond in short bullet points."
    try:
        result = generate_with_gemini(prompt)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simplify-prescription")
async def simplify_prescription(data: PrescriptionInput):
    prompt = f"Summarize this medical prescription or notes in simple language for a patient:\n\n{data.text}"
    try:
        result = generate_with_gemini(prompt)
        return {"summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preventive-plan")
async def preventive_plan(data: PreventivePlanInput):
    conditions_str = ", ".join(data.conditions)
    prompt = (
        f"Create a simple preventive care plan for a {data.age}-year-old {data.gender} "
        f"with these conditions: {conditions_str}. Provide daily/weekly tips."
    )
    try:
        result = generate_with_gemini(prompt)
        return {"plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))