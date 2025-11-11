#!/bin/bash
# Deploy GCP ADK Agent to Cloud Run

set -e

# Configuration
export GCP_PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
export SERVICE_NAME="${SERVICE_NAME:-adk-agent}"
export REGION="${REGION:-us-central1}"
export AGENT_NAME="${AGENT_NAME:-gcp-adk-agent}"
export AGENT_DESCRIPTION="${AGENT_DESCRIPTION:-ADK agent running in GCP}"
export AGENT_CAPABILITIES="${AGENT_CAPABILITIES:-general,nlp,conversation}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Deploying A2A Agent to Google Cloud Run${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Configuration:"
echo "  Project ID: $GCP_PROJECT_ID"
echo "  Service Name: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  Agent Name: $AGENT_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo -e "${GREEN}Setting GCP project...${NC}"
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
echo -e "${GREEN}Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Deploy to Cloud Run
echo -e "${GREEN}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=10 \
  --set-env-vars "AGENT_NAME=$AGENT_NAME,AGENT_DESCRIPTION=$AGENT_DESCRIPTION,AGENT_CAPABILITIES=$AGENT_CAPABILITIES,GCP_REGION=$REGION"

# Get service URL
echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format='value(status.url)')

echo "================================================"
echo "  Service URL: $SERVICE_URL"
echo "================================================"
echo ""

# Test discovery endpoint
echo -e "${GREEN}Testing agent discovery...${NC}"
curl -s "$SERVICE_URL/.well-known/agent.json" | jq .

echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Test the agent:"
echo "   curl -X POST $SERVICE_URL/execute \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"task\": \"Hello from test\"}'"
echo ""
echo "2. Add to your AKS orchestrator:"
echo "   kubectl set env deployment/orchestrator -n multiagent \\"
echo "     AGENT_ENDPOINTS=\"http://travel-agent-service/.well-known/agent.json,$SERVICE_URL/.well-known/agent.json\""
echo ""
echo "3. Verify orchestrator can discover it:"
echo "   curl http://YOUR_ORCHESTRATOR_IP/agents"
echo ""
