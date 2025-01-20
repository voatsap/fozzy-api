#######################################################################################
# main.tf - Infrastructure code to deploy fozzy service to handle 1000 Concurrent Users
# 4 vCPU / 8 GiB Fargate configuration with 10 tasks, autoscaling, and ALB
######################################################################################
terraform {
  required_version = ">= 1.3.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
}

data "aws_availability_zones" "available" {}

data "aws_route53_zone" "inbox_wine" {
  name         = "inbox.wine."
  private_zone = false
}

resource "aws_acm_certificate" "fozzy_cert" {
  domain_name       = "fozzy-api.inbox.wine"
  validation_method = "DNS"
}

resource "aws_route53_record" "fozzy_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.fozzy_cert.domain_validation_options :
    dvo.resource_record_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }

  zone_id = data.aws_route53_zone.inbox_wine.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.value]
}

resource "aws_acm_certificate_validation" "fozzy_validation" {
  certificate_arn         = aws_acm_certificate.fozzy_cert.arn
  validation_record_fqdns = [for r in aws_route53_record.fozzy_cert_validation : r.fqdn]
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 3.0"

  name = "fozzy-api-vpc"
  cidr = "10.0.0.0/16"

  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.3.0/24", "10.0.4.0/24"]

  enable_nat_gateway = true
}

# ECR repo
module "ecr" {
  source  = "terraform-aws-modules/ecr/aws"
  version = "~> 1.0"

  name = "fozzy-api-ecr"
}

module "ecs" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 4.0"

  name                    = "fozzy-api-service"
  vpc_id                  = module.vpc.vpc_id
  subnets                 = module.vpc.private_subnets
  create_ecs_cluster      = true
  create_ecs_service      = true
  create_ecs_task         = true
  create_alb              = true
  create_alb_listener     = true
  create_load_balancer_sg = true
  create_ecs_service_sg   = true
  create_route53_record   = true

  alb_certificate_arn = aws_acm_certificate_validation.fozzy_validation.certificate_arn
  route53_zone_name   = data.aws_route53_zone.inbox_wine.name
  route53_record_name = "fozzy-api"

  # 10 tasks to handle peak load
  desired_count = 10

  # Optional: autoscaling
  min_count          = 2
  max_count          = 15
  enable_autoscaling = true
  scaling_cpu_target = 70  # scale target based on CPU usage (percent)
  # Optionally  request-based or step-scaling policies as well

  # 4 vCPU / 8 GiB
  cpu    = 4096
  memory = 8192

  container_definitions = <<EOF
[
  {
    "name": "fozzy-api",
    "image": "${module.ecr.repository_url}:latest",
    "essential": true,
    "portMappings": [
      {
        "containerPort": 80,
        "protocol": "tcp"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/fozzy-api-service",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "fozzy-api"
      }
    }
  }
]
EOF
}

output "alb_dns_name" {
  description = "Public DNS name of the ALB"
  value       = module.ecs.alb_dns_name
}

output "service_url" {
  description = "Full URL for the service"
  value       = "https://${module.ecs.route53_record_fqdn}"
}