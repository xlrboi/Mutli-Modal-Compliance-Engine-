import os          
import logging      
from azure.monitor.opentelemetry import configure_azure_monitor  

# ========== CREATE A DEDICATED LOGGER ==========
# Creates a named logger specifically for telemetry-related messages
# This separates telemetry logs from your main application logs
logger = logging.getLogger("Guardian-telemetry")


def setup_telemetry():
    """
    Initializes Azure Monitor OpenTelemetry.
    
    What does "hooks into FastAPI automatically" mean?
    - Once configured, it auto-captures every API request/response
    - No need to manually log each endpoint
    """
    
    # ========== STEP 1: RETRIEVE CONNECTION STRING ==========
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    # ========== STEP 2: CHECK IF CONFIGURED ==========
    if not connection_string:
        logger.warning("No Instrumentation Key found. Telemetry is DISABLED.")
        return 

    # ========== STEP 3: CONFIGURE AZURE MONITOR ==========
    try:
        # configure_azure_monitor() does the heavy lifting:
        # 1. Registers automatic instrumentation for:
        #    - HTTP requests (FastAPI endpoints)
        #    - Database calls (Azure Search queries)
        #    - Logging events
        # 2. Starts background thread to send data to Azure
        configure_azure_monitor(
            connection_string=connection_string,  # Where to send data
            logger_name="Guardian-tracer"   
        )
        # 
        logger.info(" Azure Monitor Tracking Enabled & Connected!")
        
    except Exception as e:
        # ========== ERROR HANDLING ==========
        logger.error(f"Failed to initialize Azure Monitor: {e}")
        # Note: Function doesn't raise the error - telemetry failure shouldn't crash the app