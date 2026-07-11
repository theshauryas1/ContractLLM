# Cloud Deployment Guide

This guide describes how to deploy the Tender Compliance Engine (AI Legal Intelligence Platform) to the cloud using either **Render & Vercel (Simplified PaaS)** or **Google Cloud Run & Cloud SQL (Production Serverless IaC)**.

---

## Option 1: PaaS Deployment (Render & Vercel)
This option uses the pre-configured PaaS blueprints in the `infrastructure/` directory.

### 1. Deploy the Backend (FastAPI + PostgreSQL) to Render
1. Commit and push the repository to GitHub.
2. Log in to [Render](https://render.com/).
3. Click **New +** ➔ **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically parse the `infrastructure/render.yaml` configuration.
6. Configure the secret environment variables in the Render dashboard:
   - `GEMINI_API_KEY`: Your active Gemini token.
   - `API_KEY`: Secret string securing backend endpoints.
   - `DATABASE_URL`: Automatically populated if using Render PostgreSQL.

### 2. Deploy the Frontend (React + Vite) to Vercel
1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New** ➔ **Project** and import your repository.
3. Configure the Root Directory setting to: `frontend`.
4. Set the Build Command: `npm run build`.
5. Set Output Directory: `dist`.
6. Add environment variables in Vercel:
   - `VITE_API_BASE`: `https://your-render-backend-url.onrender.com/api`
   - `VITE_API_KEY`: The API key protecting your backend.
7. Click **Deploy**.

---

## Option 2: Enterprise IaC (Google Cloud Run & Cloud SQL)
This option deploys the system in a highly scalable, serverless network on Google Cloud using the Terraform files in the `terraform/` directory.

### Prerequisites
- Install [Terraform](https://www.terraform.io/downloads.html).
- Install [Google Cloud SDK (gcloud CLI)](https://cloud.google.com/sdk/docs/install).
- Create a GCP project and enable billing.

### 1. Build and Push the Container to Artifact Registry
Authenticate with Google Cloud and push the image:
```bash
# 1. Login to GCP
gcloud auth login
gcloud auth configure-docker us-central1-docker.pkg.dev

# 2. Create Artifact Registry repository
gcloud artifacts repositories create cloudrun-source-deploy \
    --repository-format=docker \
    --location=us-central1

# 3. Build container using the production Dockerfile
docker build -t us-central1-docker.pkg.dev/[PROJECT_ID]/cloudrun-source-deploy/backend:latest -f docker/Dockerfile .

# 4. Push container
docker push us-central1-docker.pkg.dev/[PROJECT_ID]/cloudrun-source-deploy/backend:latest
```

### 2. Provision Infrastructure with Terraform
Initialize and apply the Terraform script:
```bash
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="project_id=[PROJECT_ID]" -var="db_password=[SECURE_DB_PASSWORD]"

# Deploy resources to GCP
terraform apply -var="project_id=[PROJECT_ID]" -var="db_password=[SECURE_DB_PASSWORD]"
```

### 3. Add Gemini API Key to Secret Manager
For safety, the Gemini API key is mapped from GCP Secret Manager:
```bash
echo -n "AQ.Ab8RN..." | gcloud secrets versions add gemini-api-key --data-file=-
```

This completes the deployment. Your Cloud Run endpoint will be outputted and is ready for use!
