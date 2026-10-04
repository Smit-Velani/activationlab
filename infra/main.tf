terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
provider "aws" { region = var.aws_region }
# Starter infrastructure: ECR repositories for API and worker images.
resource "aws_ecr_repository" "api" { name = "activationlab-api" image_scanning_configuration { scan_on_push = true } }
resource "aws_ecr_repository" "worker" { name = "activationlab-worker" image_scanning_configuration { scan_on_push = true } }
output "api_repository_url" { value = aws_ecr_repository.api.repository_url }
output "worker_repository_url" { value = aws_ecr_repository.worker.repository_url }
