import uuid        
import logging     
from fastapi import FastAPI, HTTPException  
from pydantic import BaseModel  
from typing import List, Optional  
from dotenv import load_dotenv

load_dotenv(override=True)  


# ========== STEP 1: INITIALIZE TELEMETRY ==========
from backend.src.api.telemetry import setup_telemetry
setup_telemetry() 


# ========== STEP 2: IMPORT WORKFLOW GRAPH ==========
from backend.src.graph.workflow import app as compliance_graph
# Imports LangGraph workflow (Indexer → Auditor)
# Renamed to 'compliance_graph' to avoid confusion with FastAPI's 'app'


# ========== STEP 3: CONFIGURE LOGGING ==========
logging.basicConfig(level=logging.INFO)  

logger = logging.getLogger("api-server")  


# ========== STEP 4: CREATE FASTAPI APPLICATION ==========
app = FastAPI(
    title="Guardian AI API",
    description="API for auditing video content against brand compliance rules.",
    version="1.0.0"
)


# ========== STEP 5: DEFINE DATA MODELS (PYDANTIC) ==========

# --- REQUEST MODEL ---
class AuditRequest(BaseModel):
    """
    Defines the expected structure of incoming API requests.
        
    Example valid request:
    {
        "video_url": "https://youtu.be/abc123"
    }
    
    Example invalid request (raises 422 error):
    {
        "video_url": 12345  ← Not a string!
    }
    """
    video_url: str  # Required string field


# --- NESTED MODEL ---
class ComplianceIssue(BaseModel):
    """
    Defines the structure of a single compliance violation.
    
    Used inside AuditResponse to represent each violation found.
    """
    category: str      # Example: "Misleading Claims"
    severity: str      # Example: "CRITICAL"
    description: str   # Example: "Absolute guarantee detected at 00:32"


# --- RESPONSE MODEL ---
class AuditResponse(BaseModel):
    """
    Defines the structure of API responses.
        
    Example response:
    {
        "session_id": "ce6c43bb-c71a-4f16-a377-8b493502fee2",
        "video_id": "vid_ce6c43bb",
        "status": "FAIL",
        "final_report": "Video contains 2 critical violations...",
        "compliance_results": [
            {
                "category": "Misleading Claims",
                "severity": "CRITICAL",
                "description": "Absolute guarantee at 00:32"
            }
        ]
    }
    """
    session_id: str                           # Unique audit session ID
    video_id: str                             # Shortened video identifier
    status: str                               # PASS or FAIL
    final_report: str                         # AI-generated summary
    compliance_results: List[ComplianceIssue] # List of violations (can be empty)


# ========== STEP 6: DEFINE MAIN ENDPOINT ==========
@app.post("/audit", response_model=AuditResponse)
# @app.post = Decorator that registers this function as a POST endpoint
# "/audit" = URL path (http://localhost:8000/audit)
# response_model = Tells FastAPI to validate response matches AuditResponse

async def audit_video(request: AuditRequest):
    """
    Main API endpoint that triggers the compliance audit workflow.
    
    HTTP Method: POST
    URL: http://localhost:8000/audit
    
    Request Body:
    {
        "video_url": "https://youtu.be/abc123"
    }
    
    Response: AuditResponse object (defined above)
    
    Process:
    1. Generate unique session ID
    2. Prepare input for LangGraph workflow
    3. Invoke the graph (Indexer → Auditor)
    4. Return formatted results
    """
    
    # ========== GENERATE SESSION ID ==========
    session_id = str(uuid.uuid4())  
    
    video_id_short = f"vid_{session_id[:8]}"  
    
    # ========== LOG INCOMING REQUEST ==========
    logger.info(f"Received Audit Request: {request.video_url} (Session: {session_id})")

    # ========== PREPARE GRAPH INPUT ==========
    initial_inputs = {
        "video_url": request.video_url,  # From the API request
        "video_id": video_id_short,      # Generated ID
        "compliance_results": [],        # Will be populated by Auditor
        "errors": []                     # Tracks any processing errors
    }

    try:
        # ========== INVOKE LANGGRAPH WORKFLOW ==========
        # This is the SAME logic from main.py - just wrapped in an API
        final_state = compliance_graph.invoke(initial_inputs)
        # Blocking call - waits for entire workflow to complete
        # Flow: START → Indexer → Auditor → END
        # Returns: Final state dictionary with all results
        
        # In production, you'd use:
        # await compliance_graph.ainvoke(initial_inputs)
        # Async version - doesn't block the server while processing
        
        # ========== MAP GRAPH OUTPUT TO API RESPONSE ==========
        return AuditResponse(
            session_id=session_id,
            video_id=final_state.get("video_id"),  
            # .get() safely retrieves value (None if missing)
            
            status=final_state.get("final_status", "UNKNOWN"),  
            # Defaults to "UNKNOWN" if key doesn't exist
            
            final_report=final_state.get("final_report", "No report generated."),
            
            compliance_results=final_state.get("compliance_results", [])
            # Returns empty list [] if no violations
        )
        # FastAPI automatically converts this Pydantic object to JSON

    except Exception as e:
        # ========== ERROR HANDLING ==========
        logger.error(f"Audit Failed: {str(e)}")  
        # Log the error for debugging
        
        raise HTTPException(
            status_code=500,  # 500 = Internal Server Error
            detail=f"Workflow Execution Failed: {str(e)}"
            # Returns this error message to the client
        )
        # Example error response:
        # {
        #     "detail": "Workflow Execution Failed: YouTube download error"
        # }


# ========== STEP 7: HEALTH CHECK ENDPOINT ==========
@app.get("/health")
# GET request at http://localhost:8000/health
def health_check():
    """
    Simple endpoint to verify the API is running.
        
    Example usage:
    curl http://localhost:8000/health
    
    Response:
    {
        "status": "healthy",
        "service": "Guardian AI"
    }
    """
    return {"status": "healthy", "service": "Guardian AI"}
    # FastAPI automatically converts dict to JSON response


# ========== STEP 8: RUN INSTRUCTIONS (IN COMMENTS) ==========
'''
To execute: 
uv run uvicorn backend.src.api.server:app --reload

Command breakdown:
- uv run          = Run with UV package manager
- uvicorn         = ASGI server (like Gunicorn but async)
- backend.src.api.server:app = Python path to FastAPI app object
- --reload        = Auto-restart server when code changes (dev mode)

Server starts at: http://localhost:8000

Access points:
- API Docs:    http://localhost:8000/docs (interactive Swagger UI)
- Health:      http://localhost:8000/health
- Main API:    POST http://localhost:8000/audit
'''

'''
## How the API Works (Request Flow)
```
1. Client sends POST request:
   POST http://localhost:8000/audit
   Body: {"video_url": "https://youtu.be/abc123"}
   
2. FastAPI receives request:
   - Validates request matches AuditRequest model
   - Calls audit_video() function
   
3. audit_video() executes:
   - Generates session ID
   - Prepares initial_inputs dict
   - Calls compliance_graph.invoke()
   
4. LangGraph workflow runs:
   START → Indexer → Auditor → END
   
5. Function returns AuditResponse:
   - FastAPI validates response matches model
   - Converts Pydantic object to JSON
   - Sends HTTP response to client
   
6. Azure Monitor captures:
   - Request duration
   - HTTP status code
   - Any errors
   - Graph execution trace

'''