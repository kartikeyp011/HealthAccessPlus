from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
import google.generativeai as genai
import os

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API"))

app = FastAPI(title="HealthAccessPlus Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # path to backend folder

FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")  # one level up + frontend

templates = Jinja2Templates(directory=FRONTEND_DIR)
# app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
# NEW (mount static files at /static)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Serve frontend HTML and static assets from "frontend" folder
# templates = Jinja2Templates(directory="frontend")
# app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Data Models
class SymptomRequest(BaseModel):
    age: int
    sex: str
    primary_symptom: str
    symptom_duration: str
    symptom_severity: int
    additional_symptoms: List[str]
    conditions: List[str]
    medications: Optional[str] = None
    allergies: Optional[str] = None
    additional_info: Optional[str] = None

class PrescriptionRequest(BaseModel):
    text: str

class CarePlanRequest(BaseModel):
    age: int
    gender: str
    conditions: Optional[List[str]] = []

# Gemini helper
def generate_with_gemini(prompt: str):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/symptom-checker", response_class=HTMLResponse)
async def serve_symptom_checker(request: Request):
    return templates.TemplateResponse("symptom-checker.html", {"request": request})

@app.get("/prescription-simplifier", response_class=HTMLResponse)
async def serve_prescription_simplifier(request: Request):
    return templates.TemplateResponse("prescription-simplifier.html", {"request": request})

@app.get("/preventive-care", response_class=HTMLResponse)
async def serve_preventive_care(request: Request):
    return templates.TemplateResponse("preventive.html", {"request": request})

# API routes
@app.post("/api/check-symptoms")
async def check_symptoms(data: SymptomRequest):
    prompt = (
        f"Given the symptoms: {data.primary_symptom} for {data.symptom_duration}, "
        f"severity {data.symptom_severity}, additional symptoms: {', '.join(data.additional_symptoms)}, "
        f"conditions: {', '.join(data.conditions)}, medications: {data.medications}, "
        f"and allergies: {data.allergies}, what are possible diagnoses? Respond in short bullet points."
    )
    try:
        result = generate_with_gemini(prompt)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simplify-prescription")
async def simplify_prescription(data: PrescriptionRequest):
    prompt = f"Summarize this medical prescription or notes in simple language for a patient:\n\n{data.text}"
    try:
        result = generate_with_gemini(prompt)
        return {"summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-care-plan")
async def generate_care_plan(data: CarePlanRequest):
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

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}