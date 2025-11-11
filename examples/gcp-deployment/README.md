# GCP Agent Deployment Files

This directory contains everything needed to deploy an A2A-compatible agent to Google Cloud Platform.

## Quick Start

1. **Customize the agent**:
   - Edit `gcp_agent_wrapper.py`
   - Implement your ADK logic in the `process_task()` function

2. **Deploy to GCP Cloud Run**:
   ```bash
   chmod +x deploy-to-cloudrun.sh
   ./deploy-to-cloudrun.sh
   ```

3. **Get your agent URL**:
   ```bash
   gcloud run services describe adk-agent \
     --region=us-central1 \
     --format='value(status.url)'
   ```

4. **Add to AKS orchestrator**:
   ```bash
   # Update orchestrator environment variable
   kubectl set env deployment/orchestrator \
     -n multiagent \
     AGENT_ENDPOINTS="http://travel-agent-service/.well-known/agent.json,https://YOUR-GCP-URL/.well-known/agent.json"
   ```

## Files

- `gcp_agent_wrapper.py` - A2A protocol wrapper for your ADK agent
- `Dockerfile` - Container image for deployment
- `requirements.txt` - Python dependencies
- `deploy-to-cloudrun.sh` - Automated deployment script
- `.env.example` - Configuration template

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python gcp_agent_wrapper.py

# Test discovery
curl http://localhost:8080/.well-known/agent.json

# Test execution
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Hello from local test"}'
```

## Security

### Enable API Key Protection

```bash
# Generate a secure API key
API_KEY=$(openssl rand -base64 32)

# Deploy with API key
gcloud run deploy adk-agent \
  --source . \
  --set-env-vars API_KEY=$API_KEY

# Update orchestrator to use API key
kubectl create secret generic gcp-agent-secrets \
  --from-literal=api-key=$API_KEY \
  -n multiagent
```

Then modify orchestrator to pass the API key in headers.

### Restrict Access to Specific IPs

```bash
# Get your AKS NAT Gateway IP
AZURE_IP=$(kubectl get svc orchestrator-service -n multiagent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Use Cloud Armor to restrict access
gcloud compute security-policies create azure-only \
  --description "Allow only from Azure"

gcloud compute security-policies rules create 1000 \
  --security-policy azure-only \
  --src-ip-ranges "$AZURE_IP/32" \
  --action allow
```

## Monitoring

View logs in Google Cloud Console or CLI:

```bash
gcloud run services logs read adk-agent --region=us-central1
```

## Cost Optimization

Cloud Run pricing is pay-per-use:
- **Free tier**: 2 million requests/month
- **After free tier**: $0.40 per million requests
- **Idle instances**: No charge

For high-traffic agents, consider:
- Setting min instances to reduce cold starts
- Using GKE for always-on workloads
