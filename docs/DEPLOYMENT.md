# Deployment Guide

## Overview

This guide covers various deployment options for the AI Text Detector application.

## Table of Contents

1. [Local Deployment](#local-deployment)
2. [Docker Deployment](#docker-deployment)
3. [Heroku Deployment](#heroku-deployment)
4. [AWS Deployment](#aws-deployment)
5. [Azure Deployment](#azure-deployment)
6. [Google Cloud Deployment](#google-cloud-deployment)

---

## Local Deployment

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ai-text-detector.git
cd ai-text-detector
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download NLTK data**
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('brown')"
```

5. **Run the application**
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

---

## Docker Deployment

### Prerequisites

- Docker installed
- Docker Compose (optional)

### Using Docker

1. **Build the image**
```bash
docker build -t ai-text-detector .
```

2. **Run the container**
```bash
docker run -p 8501:8501 ai-text-detector
```

### Using Docker Compose

1. **Start services**
```bash
docker-compose up -d
```

2. **View logs**
```bash
docker-compose logs -f
```

3. **Stop services**
```bash
docker-compose down
```

### Environment Variables

Create a `.env` file:
```env
LOG_LEVEL=INFO
NGRAM_ORDER=2
GPT2_MODEL=gpt2
MIN_TEXT_LENGTH=10
MAX_TEXT_LENGTH=50000
```

---

## Heroku Deployment

### Prerequisites

- Heroku account
- Heroku CLI installed

### Steps

1. **Login to Heroku**
```bash
heroku login
```

2. **Create Heroku app**
```bash
heroku create your-app-name
```

3. **Set buildpacks**
```bash
heroku buildpacks:set heroku/python
```

4. **Configure environment**
```bash
heroku config:set LOG_LEVEL=INFO
heroku config:set NGRAM_ORDER=2
```

5. **Deploy**
```bash
git push heroku main
```

6. **Scale dyno**
```bash
heroku ps:scale web=1
```

7. **Open app**
```bash
heroku open
```

### Heroku Configuration

The `Procfile` is already configured:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

---

## AWS Deployment

### Option 1: EC2

1. **Launch EC2 instance**
   - Choose Ubuntu 20.04 LTS
   - Instance type: t2.medium or better
   - Configure security group (port 8501)

2. **SSH into instance**
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

3. **Install dependencies**
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
```

4. **Clone and setup**
```bash
git clone https://github.com/yourusername/ai-text-detector.git
cd ai-text-detector
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. **Run with systemd**

Create `/etc/systemd/system/ai-detector.service`:
```ini
[Unit]
Description=AI Text Detector
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/ai-text-detector
Environment="PATH=/home/ubuntu/ai-text-detector/venv/bin"
ExecStart=/home/ubuntu/ai-text-detector/venv/bin/streamlit run app.py --server.port=8501

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-detector
sudo systemctl start ai-detector
```

### Option 2: ECS (Docker)

1. **Create ECR repository**
```bash
aws ecr create-repository --repository-name ai-text-detector
```

2. **Build and push image**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account-id.dkr.ecr.us-east-1.amazonaws.com
docker build -t ai-text-detector .
docker tag ai-text-detector:latest your-account-id.dkr.ecr.us-east-1.amazonaws.com/ai-text-detector:latest
docker push your-account-id.dkr.ecr.us-east-1.amazonaws.com/ai-text-detector:latest
```

3. **Create ECS cluster and service** (via AWS Console or CLI)

### Option 3: Lambda + API Gateway (Serverless)

Create `lambda_handler.py`:
```python
import json
from src.analyzers import EnsembleAnalyzer

analyzer = EnsembleAnalyzer()

def lambda_handler(event, context):
    text = json.loads(event['body'])['text']
    result = analyzer.analyze(text)
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

Deploy with AWS SAM or Serverless Framework.

---

## Azure Deployment

### Azure Web App

1. **Create resource group**
```bash
az group create --name ai-detector-rg --location eastus
```

2. **Create App Service plan**
```bash
az appservice plan create --name ai-detector-plan --resource-group ai-detector-rg --sku B1 --is-linux
```

3. **Create web app**
```bash
az webapp create --resource-group ai-detector-rg --plan ai-detector-plan --name your-app-name --runtime "PYTHON|3.10"
```

4. **Configure deployment**
```bash
az webapp config appsettings set --resource-group ai-detector-rg --name your-app-name --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

5. **Deploy from git**
```bash
az webapp deployment source config --name your-app-name --resource-group ai-detector-rg --repo-url https://github.com/yourusername/ai-text-detector --branch main --manual-integration
```

### Azure Container Instances

```bash
az container create --resource-group ai-detector-rg --name ai-detector --image your-registry.azurecr.io/ai-text-detector:latest --cpu 2 --memory 4 --ports 8501
```

---

## Google Cloud Deployment

### Cloud Run

1. **Build and push to Container Registry**
```bash
gcloud builds submit --tag gcr.io/your-project-id/ai-text-detector
```

2. **Deploy to Cloud Run**
```bash
gcloud run deploy ai-text-detector --image gcr.io/your-project-id/ai-text-detector --platform managed --region us-central1 --allow-unauthenticated
```

### App Engine

1. **Create `app.yaml`**
```yaml
runtime: python310
entrypoint: streamlit run app.py --server.port=$PORT

instance_class: F2

automatic_scaling:
  target_cpu_utilization: 0.65
  min_instances: 1
  max_instances: 10
```

2. **Deploy**
```bash
gcloud app deploy
```

---

## Performance Optimization

### Caching

Enable Streamlit caching in your code:
```python
@st.cache_resource
def load_analyzer():
    return EnsembleAnalyzer()
```

### Load Balancing

For production deployments:
- Use NGINX as reverse proxy
- Configure SSL/TLS certificates
- Enable rate limiting
- Add health check endpoints

### Monitoring

Set up monitoring with:
- **CloudWatch** (AWS)
- **Application Insights** (Azure)
- **Cloud Monitoring** (GCP)
- **Datadog/New Relic** (any platform)

---

## Security Best Practices

1. **Environment Variables**: Never commit secrets
2. **HTTPS**: Always use SSL/TLS in production
3. **Rate Limiting**: Prevent abuse
4. **Authentication**: Add auth for sensitive deployments
5. **Input Validation**: Sanitize all inputs
6. **CORS**: Configure properly for API access

---

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port 8501
lsof -i :8501
kill -9 <PID>
```

**Memory errors with GPT-2:**
- Use smaller model variant
- Increase container memory
- Enable model caching

**NLTK data not found:**
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('brown')"
```

---

## Scaling

### Horizontal Scaling

- Deploy behind load balancer
- Use container orchestration (Kubernetes, ECS)
- Configure auto-scaling policies

### Vertical Scaling

- Increase instance size
- Allocate more CPU/memory
- Use GPU instances for faster inference

---

## Cost Optimization

- Use spot/preemptible instances
- Configure auto-scaling to zero when idle
- Use serverless for sporadic traffic
- Enable caching to reduce compute

---

## Support

For deployment issues, please open an issue on GitHub or contact support.
