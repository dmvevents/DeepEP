#!/bin/bash
set -e  # Exit on any error

# Configuration
IMAGE_NAME="deepep-efa-h100"
TAG="latest"
LOCAL_IMAGE="${IMAGE_NAME}:${TAG}"
AWS_REGION="us-east-2"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${IMAGE_NAME}"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${TAG}"


# Build Docker image
echo "Building Docker image: ${LOCAL_IMAGE}..."
docker build --progress=plain -t "${LOCAL_IMAGE}" .

# # Create ECR repository if needed
# if ! aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${AWS_REGION}" &>/dev/null; then
#     echo "Creating ECR repository..."
#     aws ecr create-repository --repository-name "${ECR_REPO}" --region "${AWS_REGION}"
# fi

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
    docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Tag and push
echo "Pushing image to ECR..."
docker tag "${LOCAL_IMAGE}" "${ECR_URI}"
docker push "${ECR_URI}"

echo "Done! Image available at: ${ECR_URI}"
