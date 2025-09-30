import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Excuse Email Draft Tool",
    description="AI-powered excuse email generator using Databricks Model Serving",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development and Databricks Apps
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Environment configuration
DATABRICKS_API_TOKEN = os.getenv("DATABRICKS_API_TOKEN")
DATABRICKS_ENDPOINT_URL = os.getenv(
    "DATABRICKS_ENDPOINT_URL", 
    "https://dbc-32cf6ae7-cf82.staging.cloud.databricks.com/serving-endpoints/databricks-gpt-oss-120b/invocations"
)
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Pydantic models
class ExcuseRequest(BaseModel):
    category: str = Field(..., description="Excuse category")
    tone: str = Field(..., description="Email tone")
    seriousness: int = Field(..., ge=1, le=5, description="Seriousness level 1-5")
    recipient_name: str = Field(..., description="Recipient name")
    sender_name: str = Field(..., description="Sender name")
    eta_when: str = Field(..., description="ETA or when information")

class ExcuseResponse(BaseModel):
    subject: str
    body: str
    success: bool
    error: Optional[str] = None

# LLM Integration
async def call_databricks_llm(request_data: ExcuseRequest) -> Dict[str, Any]:
    """Call Databricks Model Serving endpoint"""
    if not DATABRICKS_API_TOKEN:
        raise HTTPException(
            status_code=500, 
            detail="DATABRICKS_API_TOKEN not configured"
        )
    
    # Create the prompt
    prompt = f"""
You are an AI assistant that generates professional excuse emails. Generate a JSON response with "subject" and "body" fields.

Context:
- Category: {request_data.category}
- Tone: {request_data.tone}
- Seriousness Level: {request_data.seriousness}/5 (1=very silly, 5=serious)
- Recipient: {request_data.recipient_name}
- Sender: {request_data.sender_name}
- ETA/When: {request_data.eta_when}

Generate an email with:
1. A professional subject line
2. A complete email body with greeting, apology/excuse, reason, next step, and sign-off
3. Match the tone and seriousness level appropriately

Respond ONLY with valid JSON in this format:
{{"subject": "Subject Line", "body": "Dear [Recipient],\\n\\nEmail body content...\\n\\nBest regards,\\n[Sender]"}}
"""
    
    # Prepare request payload
    payload = {
        "dataframe_records": [
            {
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {DATABRICKS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DATABRICKS_ENDPOINT_URL,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Databricks API response: {result}")
            
            # Parse the response
            if "predictions" in result and len(result["predictions"]) > 0:
                prediction = result["predictions"][0]
                
                # Handle different response formats
                content = ""
                if isinstance(prediction, dict):
                    if "candidates" in prediction:
                        content = prediction["candidates"][0]["message"]["content"]
                    elif "content" in prediction:
                        content = prediction["content"]
                    elif "text" in prediction:
                        content = prediction["text"]
                    else:
                        content = str(prediction)
                else:
                    content = str(prediction)
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(content)
                    return {
                        "subject": parsed.get("subject", "Excuse Email"),
                        "body": parsed.get("body", content),
                        "success": True,
                        "error": None
                    }
                except json.JSONDecodeError:
                    # Fallback: treat as plain text
                    lines = content.strip().split('\n')
                    subject = lines[0] if lines else "Excuse Email"
                    body = '\n'.join(lines[1:]) if len(lines) > 1 else content
                    
                    return {
                        "subject": subject,
                        "body": body,
                        "success": True,
                        "error": None
                    }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Invalid response format from Databricks API"
                )
                
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from Databricks API: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Databricks API error: {e.response.text}"
        )
    except httpx.TimeoutException:
        logger.error("Timeout calling Databricks API")
        raise HTTPException(
            status_code=504,
            detail="Timeout calling Databricks API"
        )
    except Exception as e:
        logger.error(f"Unexpected error calling Databricks API: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

# API Endpoints
@app.post("/api/generate-excuse", response_model=ExcuseResponse)
async def generate_excuse(request: ExcuseRequest):
    """Generate excuse email using Databricks LLM"""
    try:
        logger.info(f"Generating excuse for request: {request.dict()}")
        result = await call_databricks_llm(request)
        return ExcuseResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating excuse: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate excuse: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "service": "excuse-gen-app"
    }

@app.get("/healthz")
async def healthz():
    """Kubernetes-style health check"""
    return {"status": "ok"}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready"}

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    return {
        "app_info": {
            "name": "excuse-gen-app",
            "version": "1.0.0",
            "status": "running"
        },
        "environment": {
            "port": PORT,
            "host": HOST,
            "has_token": bool(DATABRICKS_API_TOKEN),
            "endpoint_configured": bool(DATABRICKS_ENDPOINT_URL)
        }
    }

@app.get("/debug")
async def debug_info():
    """Debug information endpoint"""
    return {
        "environment": {
            "port": PORT,
            "host": HOST,
            "has_databricks_token": bool(DATABRICKS_API_TOKEN),
            "databricks_endpoint": DATABRICKS_ENDPOINT_URL,
            "python_version": os.sys.version,
            "working_directory": os.getcwd(),
            "files_in_public": list(Path("public").glob("*")) if Path("public").exists() else []
        },
        "paths": {
            "current_dir": os.getcwd(),
            "public_dir": str(Path("public").absolute()),
            "index_html": str(Path("public/index.html").absolute())
        }
    }

# Static file serving for React app
def get_public_path():
    """Get the correct path to public directory"""
    possible_paths = [
        Path("public"),  # Current directory
        Path("../public"),  # Parent directory
        Path("excuse-gen-app/public"),  # From project root
        Path("/app/public"),  # Databricks Apps container
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            logger.info(f"Found public directory at: {path.absolute()}")
            return path
    
    logger.warning("Public directory not found in any expected location")
    return None

@app.get("/", response_class=HTMLResponse)
async def serve_react_app():
    """Serve the React application"""
    public_path = get_public_path()
    
    if not public_path:
        return HTMLResponse("""
        <html>
            <head><title>Excuse Gen App</title></head>
            <body>
                <h1>Application Error</h1>
                <p>Public directory not found. Please check the application deployment.</p>
            </body>
        </html>
        """)
    
    index_file = public_path / "index.html"
    
    if not index_file.exists():
        return HTMLResponse("""
        <html>
            <head><title>Excuse Gen App</title></head>
            <body>
                <h1>Application Error</h1>
                <p>index.html not found in public directory.</p>
            </body>
        </html>
        """)
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content)
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return HTMLResponse(f"""
        <html>
            <head><title>Excuse Gen App</title></head>
            <body>
                <h1>Application Error</h1>
                <p>Error reading index.html: {str(e)}</p>
            </body>
        </html>
        """)

# Additional static file serving for assets
public_path = get_public_path()
if public_path:
    app.mount("/static", StaticFiles(directory=str(public_path)), name="static")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting Excuse Email Draft Tool")
    logger.info(f"Environment: PORT={PORT}, HOST={HOST}")
    logger.info(f"Databricks endpoint configured: {bool(DATABRICKS_ENDPOINT_URL)}")
    logger.info(f"Databricks token configured: {bool(DATABRICKS_API_TOKEN)}")
    
    public_path = get_public_path()
    if public_path:
        logger.info(f"Serving static files from: {public_path.absolute()}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info"
    )
