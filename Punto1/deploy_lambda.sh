#!/bin/bash

# Variables
IMAGE_NAME=lambda_fastapi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
ECR_URL=${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${IMAGE_NAME}

# 1. Crear repositorio en ECR (si no existe)
aws ecr describe-repositories --repository-names ${IMAGE_NAME} >/dev/null 2>&1 || \
aws ecr create-repository --repository-name ${IMAGE_NAME}

# 2. Autenticarse en ECR
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# 3. Construir imagen Docker
docker build -t ${IMAGE_NAME} .

# 4. Etiquetar la imagen
docker tag ${IMAGE_NAME}:latest ${ECR_URL}:latest

# 5. Subir imagen a ECR
docker push ${ECR_URL}:latest

echo "✅ Imagen subida correctamente a ECR: ${ECR_URL}:latest"
