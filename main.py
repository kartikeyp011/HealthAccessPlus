from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import openai
from typing import List

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class SymptomInput(BaseModel):
    symptoms: str

class PrescriptionInput(BaseModel):
    text: str

class PreventivePlanInput(BaseModel):
    age: int
    gender: str
    conditions: List[str]

def call_openai(prompt: str, max_tokens=150):
    response = openai.Completion.create(
        engine="gpt-4o-mini",  # or your preferred engine
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.7,
        n=1,
        stop=None,
    )
    return response.choices[0].text.strip()

@app.post("/symptom-check")
async def symptom_check(data: SymptomInput):
    prompt = f"Given the symptoms: {data.symptoms}, list possible conditions and indicate urgency level (low, medium, high). Respond in short bullet points."
    try:
        result = call_openai(prompt)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simplify-prescription")
async def simplify_prescription(data: PrescriptionInput):
    prompt = f"Summarize this medical prescription or notes in simple language for a patient:\n\n{data.text}"
    try:
        result = call_openai(prompt)
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
        result = call_openai(prompt)
        return {"plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
