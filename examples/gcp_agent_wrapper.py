"""
A2A Protocol Wrapper for GCP ADK Agents

This wrapper makes any GCP ADK agent discoverable by A2A orchestrators.
It exposes the required A2A endpoints:
- GET /.well-known/agent.json - Agent discovery
- POST /execute - Task execution

Usage:
1. Implement your ADK agent logic in process_task()
2. Deploy to GCP Cloud Run or GKE
3. Add the agent URL to your orchestrator's AGENT_ENDPOINTS
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GCP ADK Agent - A2A Compatible",
    description="Agent wrapper for A2A protocol compliance",
    version="1.0.0"
)

# ============================================================================
# CONFIGURATION - Customize these for your agent
# ============================================================================

AGENT_NAME = os.getenv("AGENT_NAME", "gcp-adk-agent")
AGENT_DESCRIPTION = os.getenv(
    "AGENT_DESCRIPTION", 
    "ADK-based agent running in Google Cloud"
)
AGENT_CAPABILITIES = os.getenv(
    "AGENT_CAPABILITIES",
    "general,nlp,conversation"
).split(",")
AGENT_KEYWORDS = os.getenv(
    "AGENT_KEYWORDS",
    "chat,assistant,help"
).split(",")

# Security
API_KEY = os.getenv("API_KEY")  # Optional: Set for authentication
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

# ============================================================================
# DATA MODELS
# ============================================================================

class TaskRequest(BaseModel):
    """Incoming task request from orchestrator"""
    task: str
    user_id: Optional[str] = "anonymous"
    context: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}

class TaskResponse(BaseModel):
    """Response sent back to orchestrator"""
    result: str
    agent: str
    status: str = "completed"
    metadata: Optional[Dict[str, Any]] = {}

class AgentCapability(BaseModel):
    """Agent capability definition"""
    name: str
    description: str
    parameters: Optional[List[str]] = []

# ============================================================================
# YOUR ADK AGENT LOGIC - IMPLEMENT THIS
# ============================================================================

async def process_task(task: str, user_id: str, context: Dict) -> str:
    """
    Process task using your ADK agent logic.
    
    Replace this function with your actual ADK agent implementation.
    
    Args:
        task: The task description from the orchestrator
        user_id: User identifier
        context: Additional context (conversation history, preferences, etc.)
    
    Returns:
        str: The agent's response
    
    Example integrations:
    
    # If using Vertex AI Agent Builder:
    from google.cloud import discoveryengine_v1beta
    
    client = discoveryengine_v1beta.ConversationalSearchServiceClient()
    request = discoveryengine_v1beta.ConverseConversationRequest(
        name=f"projects/{PROJECT}/locations/{LOCATION}/...",
        query=discoveryengine_v1beta.TextInput(input=task),
    )
    response = client.converse_conversation(request=request)
    return response.reply.summary.text
    
    # If using custom ADK agent:
    from your_adk_module import YourAgent
    
    agent = YourAgent()
    result = await agent.process(task, context)
    return result
    """
    
    # TODO: Replace with your ADK agent logic
    logger.info(f"Processing task: {task} for user: {user_id}")
    
    # Example placeholder response
    result = f"Processed by {AGENT_NAME}: {task}"
    
    return result

# ============================================================================
# A2A PROTOCOL ENDPOINTS
# ============================================================================

@app.get("/.well-known/agent.json")
async def agent_discovery():
    """
    A2A Discovery Endpoint
    
    Returns agent metadata, capabilities, and endpoints.
    This is how the orchestrator discovers what this agent can do.
    """
    logger.info("Agent discovery request received")
    
    return {
        "name": AGENT_NAME,
        "description": AGENT_DESCRIPTION,
        "version": "1.0.0",
        "protocol": "a2a",
        "capabilities": AGENT_CAPABILITIES,
        "keywords": AGENT_KEYWORDS,
        "endpoints": {
            "execute": "/execute",
            "health": "/health",
            "metrics": "/metrics"
        },
        "contact": {
            "platform": "Google Cloud Platform",
            "region": os.getenv("GCP_REGION", "us-central1"),
            "service": os.getenv("K_SERVICE", "cloud-run")  # Cloud Run service name
        },
        "limits": {
            "max_task_length": 10000,
            "timeout_seconds": 30,
            "rate_limit": "100/minute"
        }
    }

@app.post("/execute", response_model=TaskResponse)
async def execute_task(
    request: TaskRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> TaskResponse:
    """
    A2A Task Execution Endpoint
    
    Receives tasks from the orchestrator and processes them using the ADK agent.
    
    Security: Validates API key if configured.
    """
    
    # Optional API key validation
    if API_KEY and x_api_key != API_KEY:
        logger.warning(f"Unauthorized access attempt from user: {request.user_id}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    
    logger.info(f"Task execution request from user: {request.user_id}")
    logger.debug(f"Task: {request.task[:100]}...")  # Log first 100 chars
    
    try:
        # Process task using your ADK agent
        result = await process_task(
            task=request.task,
            user_id=request.user_id,
            context=request.context or {}
        )
        
        logger.info(f"Task completed successfully for user: {request.user_id}")
        
        return TaskResponse(
            result=result,
            agent=AGENT_NAME,
            status="completed",
            metadata={
                "platform": "gcp",
                "service": "cloud-run",
                "region": os.getenv("GCP_REGION", "unknown")
            }
        )
        
    except Exception as e:
        logger.error(f"Task execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Task execution failed: {str(e)}"
        )

# ============================================================================
# HEALTH & MONITORING ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "service": AGENT_NAME,
        "platform": "gcp",
        "version": "1.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint (extend with Prometheus if needed)"""
    return {
        "agent": AGENT_NAME,
        "uptime": "healthy",
        "platform": "gcp"
    }

@app.get("/")
async def root():
    """Root endpoint - redirects to discovery"""
    return {
        "message": f"Welcome to {AGENT_NAME}",
        "discovery": "/.well-known/agent.json",
        "protocol": "a2a"
    }

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    logger.info(f"Starting {AGENT_NAME}")
    logger.info(f"Capabilities: {AGENT_CAPABILITIES}")
    logger.info(f"Keywords: {AGENT_KEYWORDS}")
    logger.info(f"API Key Protection: {'Enabled' if API_KEY else 'Disabled'}")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
