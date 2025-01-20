# Fozzy API Infrastructure

This repository contains Infrastructure as Code for deploying the **Fozzy Wine Recommendation API** on **AWS Fargate** behind an **Application Load Balancer** with domain `fozzy-api.inbox.wine`. It uses **Terraform** to:

- Create an ECS cluster, service, and tasks (4 vCPUs / 8 GiB each).  
- Run **10 Fargate tasks** by default, scaling up to **15** and down to **2** based on **CPU usage**.  
- Provision an **ACM certificate** and **Route53** DNS for an HTTPS endpoint.  
- Deploy a minimal **VPC** with public/private subnets and NAT Gateway.  
- Optionally create an **ECR** repository to store the Docker image.

## Architecture Diagram

```
Client –> [HTTPS, fozzy-api.inbox.wine] –> ALB –> ECS (Fargate) –> [10 tasks, scaled]
|
|-> VPC (public/private subnets, NAT)
|-> Route53
|-> ACM for TLS
```

## Key Components

1. **VPC**  
   - Deployed via [terraform-aws-modules/vpc/aws](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws).  
   - Creates public + private subnets in two availability zones for high availability.  
   - NAT Gateway allows outbound connections from private subnets.

2. **ACM Certificate**  
   - Requested/validated for `fozzy-api.inbox.wine` using DNS validation in Route53.

3. **ECR** (Optional)  
   - Deployed via [terraform-aws-modules/ecr/aws](https://registry.terraform.io/modules/terraform-aws-modules/ecr/aws).  
   - Stores the Docker image with the FastAPI + Gunicorn code.

4. **ECS + Fargate Service**  
   - Deployed via [terraform-aws-modules/ecs/aws](https://registry.terraform.io/modules/terraform-aws-modules/ecs/aws).  
   - **Fargate Tasks** each have **4 vCPUs** and **8 GiB** memory to accommodate higher concurrency.  
   - Default **desired_count = 10** tasks.  
   - Autoscaling: min = 2, max = 15, scaling on CPU usage of 70%.

5. **ALB + HTTPS**  
   - Automatically provisions a load balancer, HTTP -> HTTPS redirects, and ties in the ACM certificate.  
   - A Route53 record points `fozzy-api.inbox.wine` to this ALB.

## Scaling & Metrics

### Autoscaling
- **CPU-based** autoscaling:
  - Target CPU utilization is **70%**.  
  - Min tasks = **2**, max tasks = **15**.  
  - If CPU usage remains above 70%, ECS will add tasks (up to 15).  
  - If usage goes below 70% for a sustained period, ECS will remove tasks (down to 2).  

### Performance Expectations
- **Base**: 10 tasks, each ~4 vCPU.  
- **Peak**: Up to 15 tasks.  
- The load balancer distributes traffic across tasks in private subnets.  
- For high concurrency (e.g., ~1,000+ RPS), you can adjust min/max counts or the CPU/memory in `main.tf` to achieve desired latency (e.g., <1s P95).

## Deployment

### Prerequisites

- **Terraform** v1.3+  
- **AWS CLI** configured with credentials  
- **Domain**: You must own `inbox.wine` and have access to the Route53 DNS zone.  
- **Docker Image** (optional): If using the provided ECR module, push your image to that ECR repo after creation. Otherwise, update the `container_definitions` in `main.tf` to reference an existing repo.

### Steps

1. **Clone this repo**  
   ```bash
   git clone https://github.com/example/fozzy-aws-infra.git
   cd fozzy-aws-infra
   terraform init
   terraform apply
   ```
2. **Retrieve ALB DNS / final URL**
	•	Once deployed, Terraform outputs alb_dns_name and service_url.
	•	The final endpoint is https://fozzy-api.inbox.wine (once DNS and certificate validation are complete).

3. **Updating the Docker Image**
```bash
docker build -t fozzy-api .

aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin <ECR_REPOSITORY_URI>

docker tag fozzy-api:latest <ECR_REPOSITORY_URI>:latest

docker push <ECR_REPOSITORY_URI>:latest
```
