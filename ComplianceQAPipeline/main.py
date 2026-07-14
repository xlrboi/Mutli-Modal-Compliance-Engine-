"""
Main Execution Entry Point for Brand Guardian AI.

This file is the "control center" that starts and manages the entire 
compliance audit workflow. Think of it as the master switch that:
1. Sets up the audit request
2. Runs the AI workflow
3. Displays the final compliance report
"""
import uuid      
import json      
import logging   
from pprint import pprint  
from dotenv import load_dotenv
from backend.src.graph.workflow import app

load_dotenv(override=True)  

# Configure logging 
logging.basicConfig(
    level=logging.INFO,        
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  
)
logger = logging.getLogger("Guardian-runner") 


def run_cli_simulation():
    """
    Simulates a Video Compliance Audit request.
    
    This function orchestrates the entire audit process:
    - Creates a unique session ID
    - Prepares the video URL and metadata
    - Runs it through the AI workflow
    - Displays the compliance results
    """
    
    # ========== STEP 1: GENERATE SESSION ID ==========
    # Creates a unique identifier for this audit session
    session_id = str(uuid.uuid4())  
    logger.info(f"Starting Audit Session: {session_id}")  

    # ========== STEP 2: DEFINE INITIAL STATE ==========
    # This dictionary contains all the input data for the workflow
    initial_inputs = {
        "video_url": "https://youtu.be/dT7S75eYhcQ",
        "video_id": f"vid_{session_id[:8]}",  # Shortened video ID for easier tracking (first 8 chars of session ID)
        
        # Empty list that will store compliance violations found
        # Will be populated by the Auditor node
        "compliance_results": [],
        
        # Empty list for any errors during processing
        # Example: ["Download failed", "Transcript unavailable"]
        "errors": []
    }

    # ========== DISPLAY SECTION: INPUT SUMMARY ==========
    print("\n--- 1. Input Payload: INITIALIZING WORKFLOW ---")
    # json.dumps() converts Python dict to formatted JSON string
    # indent=2 makes it readable with 2-space indentation
    print(f"Input Payload: {json.dumps(initial_inputs, indent=2)}")

    # ========== STEP 3: EXECUTE GRAPH ==========
    try:
        # app.invoke() triggers the LangGraph workflow
        # It passes through: START → Indexer → Auditor → END
        # Returns the final state with all results
        final_state = app.invoke(initial_inputs)
        
        # ========== DISPLAY SECTION: EXECUTION COMPLETE ==========
        print("\n--- 2. WORKFLOW EXECUTION COMPLETE ---")
        
        # ========== STEP 4: OUTPUT RESULTS ==========
        # Display a formatted compliance report
        
        print("\n=== COMPLIANCE AUDIT REPORT ===")
        
        # .get() safely retrieves values (returns None if key doesn't exist)
        # Displays the video ID that was audited
        print(f"Video ID:    {final_state.get('video_id')}")
        
        # Shows PASS or FAIL status
        print(f"Status:      {final_state.get('final_status')}")
        
        # ========== VIOLATIONS SECTION ==========
        print("\n[ VIOLATIONS DETECTED ]")
        
        # Extract the list of compliance violations
        # Default to empty list if no results
        results = final_state.get('compliance_results', [])
        
        if results:
            # Loop through each violation and display it
            for issue in results:
                # Each issue is a dict with: severity, category, description
                # Example output: "- [CRITICAL] Misleading Claims: Absolute guarantee detected"
                print(f"- [{issue.get('severity')}] {issue.get('category')}: {issue.get('description')}")
        else:
            # No violations found (clean video)
            print("No violations found.")

        # ========== SUMMARY SECTION ==========
        print("\n[ FINAL SUMMARY ]")
        # Displays the AI-generated natural language summary
        # Example: "Video contains 2 critical violations..."
        print(final_state.get('final_report'))

    except Exception as e:
        # ========== ERROR HANDLING ==========
        # If anything breaks, log the error
        logger.error(f"Workflow Execution Failed: {str(e)}")
        
        # Re-raise the exception so we see the full error traceback
        # This helps with debugging (shows exactly where/why it failed)
        raise e


# ========== PROGRAM ENTRY POINT ==========
# This block only runs when you execute: python main.py
# It won't run if you import this file as a module
if __name__ == "__main__":
    run_cli_simulation()  # Start the compliance audit simulation



'''
You have moved from "Coding" to "Product."

Ingestion:  (YouTube -> Azure)

Indexing:  (Speech-to-Text + OCR)

Retrieval:  (Found the rules about "Claims")

Reasoning:  (Applied rules to the specific claims in the video)

You are done. Your pipeline is fully operational.
'''