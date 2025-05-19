from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
import google.generativeai as genai
import os
import markdown
import re

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

def clean_markdown(md_text: str) -> str:
    # Remove extra blank lines
    md_text = re.sub(r'\n{2,}', '\n', md_text.strip())
    
    # Join lines that belong to the same bullet point:
    # if a line does NOT start with *, and previous line was a bullet, join with space
    lines = md_text.split('\n')
    cleaned_lines = []
    for i, line in enumerate(lines):
        if i > 0 and not line.strip().startswith('*') and cleaned_lines and cleaned_lines[-1].strip().startswith('*'):
            # Append this line to previous bullet line
            cleaned_lines[-1] += ' ' + line.strip()
        else:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

# Setup Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

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

@app.get("/preventive", response_class=HTMLResponse)
async def serve_preventive_care(request: Request):
    return templates.TemplateResponse("preventive.html", {"request": request})

# API routes
@app.post("/api/check-symptoms")
async def check_symptoms(data: SymptomRequest):
    prompt = (
        f"Given the symptoms: {data.primary_symptom} for {data.symptom_duration}, "
        f"severity {data.symptom_severity}, additional symptoms: {', '.join(data.additional_symptoms)}, "
        f"conditions: {', '.join(data.conditions)}, medications: {data.medications}, "
        f"and allergies: {data.allergies}, please provide exactly 2 possible diagnoses in simple terms. "
        f"For each, briefly explain the disease and suggest basic treatment or next steps. "
        f"Write in clear, easy-to-understand language suitable for a general reader."
    )
    try:
        raw_result = generate_with_gemini(prompt)
        html_result = markdown.markdown(raw_result)  # Converts markdown to HTML
        return {"result": html_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simplify-prescription")
async def simplify_prescription(data: PrescriptionRequest):
    prompt = (
        f"Please summarize the following medical prescription or notes in simple language that anyone can understand, "
        f"including people with little medical knowledge or education. "
        f"Use short sentences, clear explanations, and avoid medical jargon. "
        f"Format the summary using markdown, with bullet points for important instructions or key points, "
        f"and bold for crucial warnings or advice and give direct answer, dont tell this is a summary or anything\n\n"
        f"{data.text}"
    )
    try:
        raw_summary = generate_with_gemini(prompt)
        cleaned_summary = clean_markdown(raw_summary)
        html_summary = markdown.markdown(cleaned_summary)
        return {"summary": html_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-care-plan")
async def generate_care_plan(data: CarePlanRequest):
    conditions_str = ", ".join(data.conditions)
    prompt = (
        f"Hi! Based on your age ({data.age}) and gender ({data.gender}), "
        f"and knowing you have {conditions_str}, kindly suggest a brief, supportive preventive care plan. "
        f"Keep it warm and easy to follow, with just a few helpful daily, weekly and monthly tips. Dont say things like Okay, let's craft a simple, supportive preventive care plan tailored just for you. Just give the result directly no additional text"
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