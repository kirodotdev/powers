---
_fragment: terraform
_of_phase: generate
_contributes:
  - terraform/main.tf
  - terraform/variables.tf
  - terraform/outputs.tf
  - terraform/security.tf
  - terraform/beanstalk.tf
  - terraform/pipeline.tf
  - .github/workflows/deploy-eb.yml
  - terraform/.gitignore
  - terraform/terraform.tfvars.example
---

# Generate Phase: Terraform Configuration Generation

**Execute ALL steps in order. Do not skip or optimize.**

## Overview

Transform `aws-design.json` into deployable Terraform HCL configurations. Produces a `terraform/` directory in `$MIGRATION_DIR/` containing valid, `terraform validate`-passing configurations for all designed AWS resources, plus the selected Elastic Beanstalk deploy artifact when EB is present.

## Output Structure

Generate `$MIGRATION_DIR/terraform/` with the following file organization. Only emit domain files that have resources in `aws-design.json`:

| File           | Domain     | Contains                                                   |
| -------------- | ---------- | ---------------------------------------------------------- |
| `main.tf`      | core       | Provider config, backend, data sources                     |
| `variables.tf` | core       | All input variables with types and defaults                |
| `outputs.tf`   | core       | Resource outputs and migration summary                     |
| `vpc.tf`       | networking | VPC, subnets, route tables, internet gateway, NAT, peering |
| `compute.tf`   | compute    | ECS cluster, Fargate task definitions, services, ALBs      |
| `beanstalk.tf` | compute    | Elastic Beanstalk applications and environments            |
| `pipeline.tf`  | deploy     | Optional CodePipeline source-to-EB deploy path             |
| `database.tf`  | database   | RDS/Aurora instances, parameter groups, RDS Proxy          |
| `cache.tf`     | cache      | ElastiCache replication groups, subnet groups              |
| `messaging.tf` | messaging  | MSK clusters, configurations                               |
| `security.tf`  | security   | Security groups, IAM roles/policies                        |

**File emission rules:**

- `main.tf`, `variables.tf`, `outputs.tf` — ALWAYS emitted
- `vpc.tf` — Emitted when `vpc_design` is present in `aws-design.json` (either existing or new VPC)
- `compute.tf` — Emitted when `aws_service` contains "Fargate" or "ALB" entries
- `beanstalk.tf` — Emitted when `aws_service` contains "Elastic Beanstalk" entries
- `.github/workflows/deploy-eb.yml` — Emitted when `aws_service` contains "Elastic Beanstalk" entries and `preferences.design_constraints.eb_deploy_method.value` is `"github_actions"` or absent (default)
- `pipeline.tf` — Emitted only when `aws_service` contains "Elastic Beanstalk" entries and `preferences.design_constraints.eb_deploy_method.value` is `"codepipeline"`
- `database.tf` — Emitted when `aws_service` contains "RDS" or "Aurora" entries
- `cache.tf` — Emitted when `aws_service` contains "ElastiCache" entries
- `messaging.tf` — Emitted when `aws_service` contains "MSK" entries
- `security.tf` — ALWAYS emitted (security groups required for all deployments)

**Service-to-file routing:**

| AWS Service in `aws-design.json`   | Target File                                                                                                     |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Fargate, ALB                       | `compute.tf`                                                                                                    |
| Elastic Beanstalk                  | `beanstalk.tf`; plus `.github/workflows/deploy-eb.yml` for `github_actions` or `pipeline.tf` for `codepipeline` |
| RDS PostgreSQL, Aurora PostgreSQL  | `database.tf`                                                                                                   |
| ElastiCache Redis                  | `cache.tf`                                                                                                      |
| Amazon MSK                         | `messaging.tf`                                                                                                  |
| VPC, Subnet, Route Table, IGW, NAT | `vpc.tf`                                                                                                        |
| Security Group, IAM Role/Policy    | `security.tf`                                                                                                   |
| CloudWatch Logs                    | `compute.tf`                                                                                                    |

**Unmapped services:** If `aws-design.json` contains a `service_id` with an `aws_service` value that has no Terraform resource mapping in this file (e.g., CloudWatch + X-Ray composite, Amazon SES, Amazon SNS), **skip** that resource and record a warning in `generation-warnings.json` (which is ALWAYS written — see Step 10 — with an empty `warnings` array when nothing is skipped). Do NOT halt generation.

---

## Step 1: Generate `main.tf`

```hcl
# Heroku-to-AWS Migration — Terraform Configuration
#
# Generated by the heroku-to-aws migration skill.
# This configuration implements the architecture designed in aws-design.json.
#
# Apply sequence:
#   1. terraform init
#   2. terraform plan -out=tfplan
#   3. terraform apply tfplan

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      MigrationId = var.migration_id
      Source      = "heroku-to-aws"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}
```

**Customization rules:**

- `region` value: Use `var.aws_region` (populated from `preferences.json.global.target_region`)
- `MigrationId` tag: Use the migration run ID from `.phase-status.json`

---

## Step 2: Generate `variables.tf`

**Always include these global variables:**

```hcl
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "<preferences.json.global.target_region>"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "<heroku_app_name or migration_id>"
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "<preferences.json.global.environment_naming>"
}

variable "migration_id" {
  description = "Migration run identifier"
  type        = string
  default     = "<migration_id from .phase-status.json>"
}
```

**Per-service variables** — Extract from `aws-design.json` `aws_config` for each designed service. Include:

- Compute: `container_image_*` (one per Fargate service), `desired_count_*`, EB `instance_type_*`, `min_instances_*`, `max_instances_*`
- Database: `db_instance_class`, `db_storage_gb`, `db_engine_version`, `db_multi_az`
- Cache: `cache_node_type`, `cache_engine_version`, `cache_multi_az`
- Messaging: `msk_broker_instance_type`, `msk_broker_count`, `msk_storage_gb`
- Network: `vpc_id` (when referencing existing), `subnet_ids` (when referencing existing), `vpc_cidr` (when creating new)

**Naming convention:** `<resource_type>_<heroku_app>_<attribute>` (sanitize app names: replace `-` with `_`).

Use `aws_config` values from `aws-design.json` as defaults. Add Heroku source as comment:

```hcl
variable "fargate_cpu_my_web_app_web" {
  description = "Fargate CPU units for my-web-app web process"
  type        = number
  default     = 512
  # Heroku source: standard-2x dyno
}
```

---

## Step 3: Generate `outputs.tf`

```hcl
output "migration_summary" {
  description = "Summary of migrated Heroku resources"
  value = {
    source_platform   = "heroku"
    target_region     = var.aws_region
    migration_id      = var.migration_id
    services_migrated = <count of services in aws-design.json>
  }
}
```

Add per-service outputs for connection information:

```hcl
# Compute outputs
output "alb_dns_name" {
  description = "ALB DNS name for Fargate web traffic"
  value       = aws_lb.web.dns_name
}

# EB web outputs: emit only when a web process exists. Worker-only apps have no public EB CNAME.
output "eb_environment_url" {
  description = "Elastic Beanstalk web environment URL"
  value       = aws_elastic_beanstalk_environment.<app_name>_web.cname
}

# Database outputs
output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "rds_proxy_endpoint" {
  description = "RDS Proxy endpoint for connection pooling"
  value       = aws_db_proxy.postgres.endpoint
  sensitive   = true
}

# Cache outputs
output "elasticache_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true
}

# Messaging outputs
output "msk_bootstrap_brokers" {
  description = "MSK bootstrap broker connection string"
  value       = aws_msk_cluster.kafka.bootstrap_brokers_tls
  sensitive   = true
}
```

Only emit outputs for services present in `aws-design.json`. Mark connection strings as `sensitive = true`.

---

## Step 4: Generate `vpc.tf`

Read `aws-design.json.vpc_design.mode` to determine which path to follow.

### Path A: Existing VPC (peering detected — `mode: "existing_vpc"`)

When `vpc_design.mode == "existing_vpc"`, reference the existing VPC and subnets as data sources or variables. Do NOT create new VPC resources.

```hcl
# VPC — Referencing existing VPC from Heroku Private Space peering
# Heroku source: Private Space with VPC peering to vpc-0123456789abcdef0

variable "existing_vpc_id" {
  description = "Existing AWS VPC ID (from Heroku Private Space peering)"
  type        = string
  default     = "<vpc_design.existing_vpc_id>"
}

variable "existing_subnet_ids" {
  description = "Existing subnet IDs within the peered VPC"
  type        = list(string)
  default     = <vpc_design.subnet_ids as HCL list>
}

data "aws_vpc" "existing" {
  id = var.existing_vpc_id
}

data "aws_subnet" "existing" {
  for_each = toset(var.existing_subnet_ids)
  id       = each.value
}
```

### Path B: New VPC (no peering — `mode: "new_vpc"`)

When `vpc_design.mode == "new_vpc"`, generate a complete VPC configuration:

```hcl
# VPC — New VPC for Heroku migration (no Private Space peering detected)

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the new VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# Public subnets (for ALB)
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-public-${count.index + 1}"
    Tier = "public"
  }
}

# Private subnets (for Fargate, RDS, ElastiCache, MSK)
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-${var.environment}-private-${count.index + 1}"
    Tier = "private"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-igw"
  }
}

# NAT Gateway (for private subnet internet access)
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.project_name}-${var.environment}-nat"
  }

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-public-rt"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-private-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
```

**VPC rules:**

- Always use at least 2 subnets across separate AZs (per Requirement 9.4)
- Public subnets host ALBs; private subnets host Fargate, databases, caches, and messaging
- Single NAT gateway for cost optimization (user can expand for HA post-apply)

---

## Step 5: Generate `security.tf`

Generate security groups based on `aws-design.json.vpc_design.security_groups` and the services present.

### Private Space Migration (restricted inbound rules)

When the source inventory contains Private Space resources, generate security groups that restrict inbound traffic to declared dependency CIDRs/ports only:

```hcl
# Security Groups — Restricted inbound for Private Space migration
# Only declared dependency CIDRs and ports are permitted inbound.

resource "aws_security_group" "app" {
  name_prefix = "${var.project_name}-${var.environment}-app-"
  vpc_id      = <vpc_id_reference>
  description = "Security group for migrated Heroku app (Private Space)"

  # Inbound: Only declared dependencies
  dynamic "ingress" {
    for_each = var.app_ingress_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = [ingress.value.cidr]
      description = ingress.value.description
    }
  }

  # Outbound: Allow all (required for Fargate tasks to pull images, etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-app-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

variable "app_ingress_rules" {
  description = "Ingress rules for application security group (from Private Space dependencies)"
  type = list(object({
    port        = number
    protocol    = string
    cidr        = string
    description = string
  }))
  default = [
    # Populated from aws-design.json vpc_design.security_groups[].inbound_rules
    # Example:
    # { port = 443, protocol = "tcp", cidr = "0.0.0.0/0", description = "HTTPS from internet" },
    # { port = 5432, protocol = "tcp", cidr = "10.0.0.0/16", description = "PostgreSQL from VPC" }
  ]
}
```

### Standard Migration (no Private Space)

When no Private Space is involved, generate standard security groups:

```hcl
# ALB Security Group
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-${var.environment}-alb-"
  vpc_id      = <vpc_id_reference>
  description = "Security group for Application Load Balancer"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from internet"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP from internet (redirects to HTTPS)"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Application Security Group
resource "aws_security_group" "app" {
  name_prefix = "${var.project_name}-${var.environment}-app-"
  vpc_id      = <vpc_id_reference>
  description = "Security group for migrated application compute"

  # {{IF has_fargate}}
  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Traffic from Terraform-managed ALB (Fargate path only)"
  }
  # {{ENDIF}}
  # For EB-only designs, omit ingress here. EB manages load balancer-to-instance ingress;
  # SingleInstance non-web environments do not need inbound traffic.

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-app-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Database Security Group
resource "aws_security_group" "database" {
  name_prefix = "${var.project_name}-${var.environment}-db-"
  vpc_id      = <vpc_id_reference>
  description = "Security group for RDS/Aurora databases"

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "PostgreSQL from application compute"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-db-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Cache Security Group
resource "aws_security_group" "cache" {
  name_prefix = "${var.project_name}-${var.environment}-cache-"
  vpc_id      = <vpc_id_reference>
  description = "Security group for ElastiCache"

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "Redis from application compute"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cache-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Messaging Security Group (MSK)
resource "aws_security_group" "messaging" {
  name_prefix = "${var.project_name}-${var.environment}-msk-"
  vpc_id      = <vpc_id_reference>
  description = "Security group for Amazon MSK"

  ingress {
    from_port       = 9094
    to_port         = 9094
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "Kafka TLS from application compute"
  }

  ingress {
    from_port       = 9092
    to_port         = 9092
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "Kafka plaintext from application compute"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-msk-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}
```

**Security group rules:**

- Only emit security groups for services present in `aws-design.json`
- App SG allows traffic from Terraform-managed ALB SG for the Fargate path. For EB web environments, EB manages the load balancer security group and instance ingress rule; SingleInstance non-web environments do not need inbound traffic.
- Database/Cache/MSK SGs allow traffic from the app SG only
- ALB SG allows 80 and 443 from 0.0.0.0/0
- All SGs allow all outbound (compute needs ECR/source bundle access, package downloads, and service connectivity)

### IAM Roles

Generate ECS task execution and task roles:

```hcl
# ECS Task Execution Role
resource "aws_iam_role" "ecs_execution" {
  name = "${var.project_name}-${var.environment}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-execution"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role (application permissions)
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${var.environment}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-task"
  }
}
```

---

## Step 6: Generate `compute.tf`

For each service in `aws-design.json` where `aws_service` is "Fargate" or "ALB":

### ECS Cluster

```hcl
# ECS Cluster for migrated Heroku applications
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cluster"
  }
}
```

### CloudWatch Log Groups (per Fargate service)

```hcl
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project_name}-${var.environment}/<process_type>"
  retention_in_days = <preferences.json.operational.log_retention_days || 30>

  tags = {
    Name        = "${var.project_name}-${var.environment}-<process_type>-logs"
    HerokuApp   = "<heroku_app>"
    ProcessType = "<process_type>"
  }
}
```

### Fargate Task Definitions

Generate one task definition per formation entry in `aws-design.json`:

```hcl
# Fargate Task Definition — <heroku_app>:<process_type>
# Heroku source: <dyno_type> dyno, quantity <desired_count>
resource "aws_ecs_task_definition" "<app_sanitized>_<process_type>" {
  family                   = "${var.project_name}-${var.environment}-<process_type>"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = <aws_config.task_cpu>
  memory                   = <aws_config.task_memory>
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "<process_type>"
    image = var.<container_image_variable>
    portMappings = [
      {
        containerPort = <port: 8080 for web, omit for workers>
        hostPort      = <port: 8080 for web, omit for workers>
        protocol      = "tcp"
      }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.<ref>.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "<process_type>"
      }
    }
    essential = true
  }])

  tags = {
    Name        = "${var.project_name}-${var.environment}-<process_type>-task"
    HerokuApp   = "<heroku_app>"
    ProcessType = "<process_type>"
  }
}
```

**Task definition rules:**

- `cpu` and `memory` come from `aws_config.task_cpu` and `aws_config.task_memory` (mapped from Dyno Type Table)
- `portMappings` included only for `web` process types (port 8080 default)
- Workers, clock, and custom process types: no `portMappings`. Release process types are run-once hooks and should not be generated as persistent services.
- Container image: use variable reference (placeholder image at generation time)

### Fargate Services

```hcl
# Fargate Service — <heroku_app>:<process_type>
resource "aws_ecs_service" "<app_sanitized>_<process_type>" {
  name            = "${var.project_name}-${var.environment}-<process_type>"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.<app_sanitized>_<process_type>.arn
  desired_count   = <aws_config.desired_count>
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = <private_subnet_references>
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }

  # Load balancer block included ONLY for web process types
  load_balancer {
    target_group_arn = aws_lb_target_group.<app_sanitized>_web.arn
    container_name   = "web"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.https]

  tags = {
    Name        = "${var.project_name}-${var.environment}-<process_type>-svc"
    HerokuApp   = "<heroku_app>"
    ProcessType = "<process_type>"
  }
}
```

**Service rules:**

- `desired_count` from `aws_config.desired_count` (maps directly from Heroku formation quantity, 0–100)
- `load_balancer` block included ONLY when `aws_config.load_balancer == true` (web process types)
- Workers, clock, and custom processes: omit `load_balancer` block and `depends_on`. Release process types are skipped because they are run-once hooks.
- `assign_public_ip = false` — tasks run in private subnets behind NAT

### Application Load Balancer (web process types only)

Generate ALB resources only when `aws-design.json` contains ALB service entries:

```hcl
# Application Load Balancer — <heroku_app> web traffic
# Heroku source: web dyno routing
resource "aws_lb" "<app_sanitized>_web" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = <false for internet-facing, true for internal>
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = <public_subnet_references>

  tags = {
    Name      = "${var.project_name}-${var.environment}-alb"
    HerokuApp = "<heroku_app>"
  }
}

resource "aws_lb_target_group" "<app_sanitized>_web" {
  name        = "${var.project_name}-${var.environment}-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = <vpc_id_reference>
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/"
    protocol            = "HTTP"
    matcher             = "200-399"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-tg"
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.<app_sanitized>_web.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.<app_sanitized>_web.arn
  }
}

resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.<app_sanitized>_web.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS listener"
  type        = string
  # TODO: Provide your ACM certificate ARN
}
```

**ALB rules:**

- `scheme` from `aws_config.scheme` in `aws-design.json` (default: "internet-facing")
- HTTP listener always redirects to HTTPS
- TLS 1.3 policy for new deployments
- Health check path defaults to `/` (user should customize)
- ACM certificate ARN as variable with TODO marker

---

## Step 6.5: Generate `beanstalk.tf` and EB deploy artifacts

Skip this step if no services in `aws-design.json` have `aws_service: "Elastic Beanstalk"`.

Read `preferences.design_constraints.eb_deploy_method.value`; default to `"github_actions"` when the field is absent. Always generate `beanstalk.tf` for EB services, then generate exactly one deploy path:

- `"github_actions"` → generate `$MIGRATION_DIR/.github/workflows/deploy-eb.yml`
- `"codepipeline"` → generate `$MIGRATION_DIR/terraform/pipeline.tf`
- `"manual"` → generate neither deploy automation artifact; document CLI deployment in `MIGRATION_GUIDE.md`

### `beanstalk.tf` — EB Application and Environments

```hcl
# Select the latest Elastic Beanstalk Docker platform for Amazon Linux 2023.
# The regex intentionally constrains the lookup to Docker on AL2023 while
# avoiding a hardcoded platform version that can go stale.
data "aws_elastic_beanstalk_solution_stack" "docker" {
  most_recent = true
  name_regex  = "^64bit Amazon Linux 2023 .* running Docker$"
}

resource "aws_elastic_beanstalk_application" "<app_name>" {
  name        = var.project_name
  description = "Migrated from Heroku app: <heroku_app>"
}

resource "aws_elastic_beanstalk_environment" "<app_name>_<process_type>" {
  name                = "${var.project_name}-<process_type>"
  application         = aws_elastic_beanstalk_application.<app_name>.name
  solution_stack_name = data.aws_elastic_beanstalk_solution_stack.docker.name
  tier                = "WebServer"

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "InstanceType"
    value     = var.eb_instance_type_<app_name>_<process_type>
  }

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "IamInstanceProfile"
    value     = aws_iam_instance_profile.eb_<app_name>.name
  }

  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MinSize"
    value     = var.eb_min_instances_<app_name>_<process_type>
  }

  setting {
    namespace = "aws:autoscaling:asg"
    name      = "MaxSize"
    value     = var.eb_max_instances_<app_name>_<process_type>
  }

  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "EnvironmentType"
    value     = "<LoadBalanced for web, SingleInstance for worker/clock/custom>"
  }

  # {{IF process_type == "web"}}
  setting {
    namespace = "aws:elasticbeanstalk:environment:process:default"
    name      = "HealthCheckPath"
    value     = "/health"
  }
  # {{ENDIF}}

  # {{IF process_type != "web"}}
  setting {
    namespace = "aws:elasticbeanstalk:healthreporting:system"
    name      = "SystemType"
    value     = "basic"
  }
  # {{ENDIF}}

  setting {
    namespace = "aws:ec2:vpc"
    name      = "VPCId"
    value     = <vpc_id from vpc_design>
  }

  setting {
    namespace = "aws:ec2:vpc"
    name      = "Subnets"
    value     = <comma-separated subnet IDs>
  }

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name      = "SecurityGroups"
    value     = aws_security_group.app.id
  }

  setting {
    namespace = "aws:elasticbeanstalk:command"
    name      = "DeploymentPolicy"
    value     = var.eb_deployment_policy
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "PORT"
    value     = "5000"
  }

  setting {
    namespace = "aws:elasticbeanstalk:application:environment"
    name      = "PROCESS_TYPE"
    value     = "<process_type>"
  }

  # Emit one environmentsecrets setting per sensitive Heroku config var.
  setting {
    namespace = "aws:elasticbeanstalk:application:environmentsecrets"
    name      = "DATABASE_URL"
    value     = "<secret-or-parameter-arn>"
  }
}

resource "aws_iam_instance_profile" "eb_<app_name>" {
  name = "${var.project_name}-eb-profile"
  role = aws_iam_role.eb_instance_<app_name>.name
}

resource "aws_iam_role" "eb_instance_<app_name>" {
  name = "${var.project_name}-eb-instance"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eb_web_tier_<app_name>" {
  role       = aws_iam_role.eb_instance_<app_name>.name
  policy_arn = "arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"
}

resource "aws_iam_role_policy" "eb_read_secrets_<app_name>" {
  name = "${var.project_name}-eb-read-secrets"
  role = aws_iam_role.eb_instance_<app_name>.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "ssm:GetParameter",
        "ssm:GetParameters"
      ]
      Resource = [
        "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/*",
        "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/*"
      ]
    }]
  })
}
```

**Per-environment rules:**

- Web process types: `environment_type = "LoadBalanced"`; EB auto-provisions the ALB.
- Worker/clock/custom process types: `environment_type = "SingleInstance"`; no ALB, no public endpoint, persistent Docker CMD process.
- Do NOT use EB Worker tier. Heroku workers are persistent processes, not SQS consumers.
- Do NOT generate persistent EB environments for `release` process types. Heroku release-phase commands are run-once deployment hooks and must be handled manually or by a deployment hook.
- Use `data.aws_elastic_beanstalk_solution_stack.docker.name`, not a hardcoded platform version.

### `.github/workflows/deploy-eb.yml` — GitHub Actions EB Deploy (Default)

Emit this file when `eb_deploy_method.value` is `"github_actions"` or absent. The workflow uses GitHub OIDC role assumption, packages the source bundle, creates one EB application version, and updates every generated EB environment for the app (web, worker, clock, custom).

```yaml
name: Deploy Elastic Beanstalk

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

env:
  AWS_REGION: <target_region>
  EB_APPLICATION_NAME: <app_name>
  EB_ENVIRONMENTS: "<space-separated EB environment names from aws-design.json>"

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Package source bundle
        run: |
          zip -r app.zip . -x '.git/*' 'node_modules/*'

      - name: Create application version
        run: |
          VERSION_LABEL="${GITHUB_SHA}-${GITHUB_RUN_NUMBER}"
          BUCKET="$(aws elasticbeanstalk create-storage-location --query S3Bucket --output text)"
          aws s3 cp app.zip "s3://${BUCKET}/${EB_APPLICATION_NAME}/${VERSION_LABEL}.zip"
          aws elasticbeanstalk create-application-version \
            --application-name "${EB_APPLICATION_NAME}" \
            --version-label "${VERSION_LABEL}" \
            --source-bundle "S3Bucket=${BUCKET},S3Key=${EB_APPLICATION_NAME}/${VERSION_LABEL}.zip"
          for ENVIRONMENT in ${EB_ENVIRONMENTS}; do
            aws elasticbeanstalk update-environment \
              --environment-name "${ENVIRONMENT}" \
              --version-label "${VERSION_LABEL}"
          done
```

**GitHub Actions rules:**

- Emit one workflow per repository/migration, not one per EB environment.
- `EB_ENVIRONMENTS` MUST include every generated EB environment for the app, not only `<app_name>-web`.
- The workflow assumes a GitHub OIDC role through `secrets.AWS_ROLE_ARN`; document the required role setup in `MIGRATION_GUIDE.md`.
- Do not emit `pipeline.tf` when this method is selected.

### `pipeline.tf` — CodePipeline GitHub Source to EB Deploy (Optional)

Emit this file only when `eb_deploy_method.value` is `"codepipeline"`.

```hcl
resource "aws_codepipeline" "<app_name>_deploy" {
  name     = "${var.project_name}-deploy"
  role_arn = aws_iam_role.codepipeline_<app_name>.arn

  artifact_store {
    location = aws_s3_bucket.pipeline_artifacts_<app_name>.bucket
    type     = "S3"
  }

  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = var.github_connection_arn
        FullRepositoryId = var.github_repo
        BranchName       = var.github_branch
      }
    }
  }

  stage {
    name = "Deploy"

    # Emit one action per generated EB environment for this app (web, worker, clock, custom).
    action {
      name            = "Deploy_<process_type>"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ElasticBeanstalk"
      input_artifacts = ["source_output"]
      version         = "1"
      run_order       = 1

      configuration = {
        ApplicationName = aws_elastic_beanstalk_application.<app_name>.name
        EnvironmentName = aws_elastic_beanstalk_environment.<app_name>_<process_type>.name
      }
    }
  }
}

resource "aws_s3_bucket" "pipeline_artifacts_<app_name>" {
  bucket_prefix = "${var.project_name}-artifacts-"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "pipeline_artifacts_<app_name>" {
  bucket = aws_s3_bucket.pipeline_artifacts_<app_name>.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_iam_role" "codepipeline_<app_name>" {
  name = "${var.project_name}-codepipeline"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "codepipeline.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "codepipeline_policy_<app_name>" {
  name = "${var.project_name}-codepipeline-policy"
  role = aws_iam_role.codepipeline_<app_name>.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "codestar-connections:UseConnection",
          "codeconnections:UseConnection"
        ]
        Resource = var.github_connection_arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:GetBucketVersioning"
        ]
        Resource = [
          aws_s3_bucket.pipeline_artifacts_<app_name>.arn,
          "${aws_s3_bucket.pipeline_artifacts_<app_name>.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "elasticbeanstalk:CreateApplicationVersion",
          "elasticbeanstalk:CreateStorageLocation",
          "elasticbeanstalk:DescribeApplications",
          "elasticbeanstalk:DescribeApplicationVersions",
          "elasticbeanstalk:DescribeEnvironments",
          "elasticbeanstalk:UpdateEnvironment"
        ]
        Resource = "*"
      }
    ]
  })
}
```

**CodePipeline rules:**

- CodePipeline is an explicit override, not the EB default.
- Emit one Deploy action per generated EB environment for the app; do not update only the web environment.
- The CodeStar/CodeConnections GitHub connection still requires one-time authorization in the AWS console.

---

## Step 7: Generate `database.tf`

For each service in `aws-design.json` where `aws_service` is "RDS PostgreSQL" or "Aurora PostgreSQL":

### DB Subnet Group (always needed for database services)

```hcl
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = <private_subnet_references>

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet"
  }
}
```

### RDS PostgreSQL (when `aws_service == "RDS PostgreSQL"`)

```hcl
# RDS PostgreSQL — <heroku_app>
# Heroku source: heroku-postgresql:<plan>
resource "aws_db_instance" "<app_sanitized>_postgres" {
  identifier     = "${var.project_name}-${var.environment}-postgres"
  engine         = "postgres"
  engine_version = "<aws_config.engine_version>"
  instance_class = "<aws_config.instance_class>"

  allocated_storage     = <aws_config.storage_gb>
  max_allocated_storage = <aws_config.storage_gb * 2>
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  multi_az               = <aws_config.multi_az>
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]

  backup_retention_period = 7
  backup_window           = "<preferences.json.global.maintenance_window formatted>"
  maintenance_window      = "<preferences.json.global.maintenance_window formatted>"

  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project_name}-${var.environment}-postgres-final"

  parameter_group_name = aws_db_parameter_group.<app_sanitized>_postgres.name

  tags = {
    Name      = "${var.project_name}-${var.environment}-postgres"
    HerokuApp = "<heroku_app>"
  }
}

resource "aws_db_parameter_group" "<app_sanitized>_postgres" {
  name   = "${var.project_name}-${var.environment}-postgres-params"
  family = "postgres<major_version>"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres-params"
  }
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "app"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}
```

### Aurora PostgreSQL (when `aws_service == "Aurora PostgreSQL"`)

```hcl
# Aurora PostgreSQL — <heroku_app>
# Heroku source: heroku-postgresql:<plan> (multi-az-ha/multi-region availability)
resource "aws_rds_cluster" "<app_sanitized>_aurora" {
  cluster_identifier = "${var.project_name}-${var.environment}-aurora"
  engine             = "aurora-postgresql"
  engine_version     = "<aws_config.engine_version>"

  database_name   = var.db_name
  master_username = var.db_username
  master_password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]

  backup_retention_period = 7
  preferred_backup_window = "<preferences.json.global.maintenance_window formatted>"
  storage_encrypted       = true

  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project_name}-${var.environment}-aurora-final"

  tags = {
    Name      = "${var.project_name}-${var.environment}-aurora"
    HerokuApp = "<heroku_app>"
  }
}

resource "aws_rds_cluster_instance" "<app_sanitized>_aurora" {
  count              = 2
  identifier         = "${var.project_name}-${var.environment}-aurora-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.<app_sanitized>_aurora.id
  instance_class     = "<aws_config.instance_class>"
  engine             = aws_rds_cluster.<app_sanitized>_aurora.engine
  engine_version     = aws_rds_cluster.<app_sanitized>_aurora.engine_version

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-${count.index + 1}"
  }
}
```

### RDS Proxy (when `aws_config.rds_proxy == true`)

```hcl
# RDS Proxy — Connection pooling replacement for Heroku connection pooling
resource "aws_db_proxy" "<app_sanitized>_postgres" {
  name                   = "${var.project_name}-${var.environment}-proxy"
  debug_logging          = false
  engine_family          = "POSTGRESQL"
  idle_client_timeout    = 1800
  require_tls            = true
  role_arn               = aws_iam_role.rds_proxy.arn
  vpc_security_group_ids = [aws_security_group.database.id]
  vpc_subnet_ids         = <private_subnet_references>

  auth {
    auth_scheme = "SECRETS"
    iam_auth    = "DISABLED"
    secret_arn  = aws_secretsmanager_secret.db_credentials.arn
  }

  tags = {
    Name      = "${var.project_name}-${var.environment}-proxy"
    HerokuApp = "<heroku_app>"
  }
}

resource "aws_db_proxy_default_target_group" "<app_sanitized>_postgres" {
  db_proxy_name = aws_db_proxy.<app_sanitized>_postgres.name

  connection_pool_config {
    max_connections_percent = 100
  }
}

resource "aws_db_proxy_target" "<app_sanitized>_postgres" {
  db_proxy_name          = aws_db_proxy.<app_sanitized>_postgres.name
  target_group_name      = aws_db_proxy_default_target_group.<app_sanitized>_postgres.name
  db_instance_identifier = aws_db_instance.<app_sanitized>_postgres.identifier
}

# Secrets Manager for RDS Proxy authentication
resource "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.project_name}-${var.environment}/db-credentials"

  tags = {
    Name = "${var.project_name}-${var.environment}-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
  })
}

# IAM Role for RDS Proxy
resource "aws_iam_role" "rds_proxy" {
  name = "${var.project_name}-${var.environment}-rds-proxy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "rds.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-proxy-role"
  }
}

resource "aws_iam_role_policy" "rds_proxy_secrets" {
  name = "secrets-access"
  role = aws_iam_role.rds_proxy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ]
      Resource = [aws_secretsmanager_secret.db_credentials.arn]
    }]
  })
}
```

**Database rules:**

- Storage encrypted by default (`storage_encrypted = true`)
- Final snapshot enabled (`skip_final_snapshot = false`)
- `max_allocated_storage` set to 2× initial for auto-scaling headroom
- Aurora always has 2 instances (writer + reader) for HA
- RDS Proxy emitted ONLY when `aws_config.rds_proxy == true` (connection pooling was enabled on source)
- Credentials stored in Secrets Manager (not inline)

---

## Step 8: Generate `cache.tf`

For each service in `aws-design.json` where `aws_service` is "ElastiCache Redis":

```hcl
# ElastiCache Redis — <heroku_app>
# Heroku source: heroku-redis:<plan>

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-cache-subnet"
  subnet_ids = <private_subnet_references>

  tags = {
    Name = "${var.project_name}-${var.environment}-cache-subnet"
  }
}

resource "aws_elasticache_replication_group" "<app_sanitized>_redis" {
  replication_group_id = "${var.project_name}-${var.environment}-redis"
  description          = "Redis cluster for ${var.project_name} (migrated from Heroku Redis)"

  engine               = "redis"
  engine_version       = "<aws_config.engine_version>"
  node_type            = "<aws_config.node_type>"
  num_cache_clusters   = <2 if multi_az else 1>
  port                 = 6379

  # High Availability
  automatic_failover_enabled = <aws_config.automatic_failover>
  multi_az_enabled           = <aws_config.multi_az>

  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = <aws_config.transit_encryption>

  # Network
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.cache.id]

  # Maintenance
  maintenance_window       = "<preferences.json.global.maintenance_window formatted>"
  snapshot_retention_limit = 7
  snapshot_window          = "03:00-05:00"

  # Parameter group
  parameter_group_name = aws_elasticache_parameter_group.<app_sanitized>_redis.name

  tags = {
    Name      = "${var.project_name}-${var.environment}-redis"
    HerokuApp = "<heroku_app>"
  }
}

resource "aws_elasticache_parameter_group" "<app_sanitized>_redis" {
  name   = "${var.project_name}-${var.environment}-redis-params"
  family = "redis<major_version>"

  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-params"
  }
}
```

**ElastiCache rules:**

- `automatic_failover_enabled` and `multi_az_enabled`: Set to `true` if and only if source Heroku Redis has HA enabled (`aws_config.automatic_failover == true`)
- `transit_encryption_enabled`: Set to `true` if and only if source has encryption-in-transit (`aws_config.transit_encryption == true`)
- `at_rest_encryption_enabled`: Always `true` (security best practice)
- `num_cache_clusters`: 2 when Multi-AZ enabled, 1 when single-AZ
- `engine_version`: Matches source Redis version from `aws_config.engine_version`
- `node_type`: From `aws_config.node_type` (mapped from Redis Plan Table)

---

## Step 9: Generate `messaging.tf`

For each service in `aws-design.json` where `aws_service` is "Amazon MSK":

```hcl
# Amazon MSK — <heroku_app>
# Heroku source: heroku-kafka:<plan>

resource "aws_msk_configuration" "<app_sanitized>_kafka" {
  name              = "${var.project_name}-${var.environment}-msk-config"
  kafka_versions    = ["<aws_config.kafka_version || 3.5.1>"]
  server_properties = <<PROPERTIES
auto.create.topics.enable=false
default.replication.factor=<aws_config.replication_factor || 3>
num.partitions=<aws_config.default_partitions || 3>
min.insync.replicas=2
log.retention.hours=<preferences.json.data.kafka_retention_days * 24>
PROPERTIES

  tags = {
    Name = "${var.project_name}-${var.environment}-msk-config"
  }
}

resource "aws_msk_cluster" "<app_sanitized>_kafka" {
  cluster_name           = "${var.project_name}-${var.environment}-msk"
  kafka_version          = "<aws_config.kafka_version || 3.5.1>"
  number_of_broker_nodes = <aws_config.broker_count || 2>

  broker_node_group_info {
    instance_type   = "<aws_config.broker_instance_type>"
    client_subnets  = <private_subnet_references — one per AZ, matching broker count>
    security_groups = [aws_security_group.messaging.id]

    storage_info {
      ebs_storage_info {
        volume_size = <aws_config.storage_gb>
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.<app_sanitized>_kafka.arn
    revision = aws_msk_configuration.<app_sanitized>_kafka.latest_revision
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.msk.name
      }
    }
  }

  tags = {
    Name      = "${var.project_name}-${var.environment}-msk"
    HerokuApp = "<heroku_app>"
  }
}

resource "aws_cloudwatch_log_group" "msk" {
  name              = "/msk/${var.project_name}-${var.environment}"
  retention_in_days = <preferences.json.operational.log_retention_days || 30>

  tags = {
    Name = "${var.project_name}-${var.environment}-msk-logs"
  }
}
```

**MSK rules:**

- `number_of_broker_nodes`: Minimum 2, always spread across ≥ 2 AZs (per Requirement 7.4)
- `broker_instance_type`: From `aws_config.broker_instance_type` (mapped from Kafka Plan Table)
- `volume_size`: From `aws_config.storage_gb` (meets or exceeds source plan storage)
- Encryption in-transit and in-cluster always enabled for MSK
- `client_subnets` must match the number of broker nodes and span multiple AZs
- Kafka retention set from `preferences.json.data.kafka_retention_days`
- `replication_factor` and partition counts preserved from source plan topology

---

## Step 10: Handle Unmapped Resources and Warnings

**Always write `$MIGRATION_DIR/generation-warnings.json`** — it is a mandatory
artifact of this phase (part of generate's `_produces` floor), a manifest that
records whatever could NOT be generated. Write it even when nothing was skipped:
in that case the `warnings` array is EMPTY (`"warnings": []`). A consumer can then
rely on the file always existing rather than testing for its absence.

For any `service_id` in `aws-design.json` whose `aws_service` does not have a
Terraform resource mapping defined in Steps 4–9 above:

1. **Skip** the resource — do NOT generate Terraform for it
2. **Append** the skip as an entry in `generation-warnings.json`'s `warnings` array

If every service mapped successfully, still write the file with an empty
`warnings` array.

### `generation-warnings.json` Schema

```json
{
  "generated_at": "<ISO 8601 timestamp>",
  "migration_id": "<migration_id>",
  "warnings": [
    {
      "service_id": "<service_id from aws-design.json>",
      "aws_service": "<aws_service value>",
      "heroku_app": "<heroku_app>",
      "source_resource_id": "<source_resource_id>",
      "reason": "No Terraform resource mapping available for <aws_service>",
      "recommendation": "Configure this service manually in the AWS Console or add a custom Terraform module"
    }
  ],
  "total_warnings": <count>,
  "total_services_generated": <count of successfully generated services>,
  "total_services_skipped": <count of skipped services>
}
```

**Warning scenarios that produce entries:**

- CloudWatch Logs mapped from Papertrail (no standalone Terraform needed — integrated into `compute.tf` log configuration)
- CloudWatch + X-Ray composite mappings (Scout APM, New Relic)
- Amazon SES (SendGrid mapping)
- Amazon SNS (Twilio mapping)
- Amazon EventBridge Scheduler (Heroku Scheduler mapping)
- ElastiCache Memcached (Memcachier mapping)
- Amazon MQ (CloudAMQP mapping)
- Amazon OpenSearch (Bonsai Elasticsearch mapping)
- S3 + CloudFront composite (Cloudinary mapping)

**Exception:** If `aws_service == "CloudWatch Logs"` and it maps from a logging add-on (Papertrail, Rollbar, Sentry), the log group is already emitted in `compute.tf` Step 6. Do NOT log a warning for this case.

---

## Step 11: Generate `.gitignore` and `terraform.tfvars.example`

### `$MIGRATION_DIR/terraform/.gitignore`

```
# Terraform state and providers
.terraform/
*.tfstate
*.tfstate.backup
.terraform.lock.hcl

# Variable values (may contain secrets)
terraform.tfvars
*.auto.tfvars
!terraform.tfvars.example

# Crash logs
crash.log
crash.*.log

# Plan files
*.tfplan
```

### `$MIGRATION_DIR/terraform/terraform.tfvars.example`

```hcl
# Copy this file to terraform.tfvars and fill in values before running terraform plan.
# Do NOT commit terraform.tfvars to source control — it may contain sensitive values.

aws_region   = "<target_region>"
project_name = "<project_name>"
environment  = "<environment>"
migration_id = "<migration_id>"

# Database credentials (required if RDS/Aurora is in the design)
# db_username = "app_user"
# db_password = "CHANGE_ME"

# ACM certificate (required if ALB is in the design)
# acm_certificate_arn = "arn:aws:acm:<region>:<account_id>:certificate/<cert-id>"

# Container images (one per Fargate service)
# container_image_<app>_<process_type> = "<account_id>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>"

# Elastic Beanstalk CodePipeline deploy (only when eb_deploy_method = "codepipeline")
# github_connection_arn = "arn:aws:codestar-connections:<region>:<account_id>:connection/<id>"
# github_repo           = "owner/repository"
# github_branch         = "main"

# Existing VPC (only if Private Space peering is detected)
# existing_vpc_id     = "vpc-0123456789abcdef0"
# existing_subnet_ids = ["subnet-aaa", "subnet-bbb"]
```

---

## Step 12: Validate Generated Configuration

After all files are written:

1. **Syntax check**: Verify all `.tf` files are syntactically valid HCL
2. **Reference integrity**: Ensure all `resource` references resolve to declared resources within the same configuration
3. **Variable completeness**: Every `var.*` reference has a corresponding `variable` block in `variables.tf`
4. **Output references**: Every `output` references a declared resource attribute
5. **Tag consistency**: Every resource has the default tags (applied via provider `default_tags`)

**Note:** Full `terraform validate` requires `terraform init` (provider download). The generated configuration SHOULD pass `terraform validate` when run with network access. If validation cannot run (no Terraform binary, no network), log a note but do NOT block generation.

When all files are written, control returns to `heroku-generate.md` (then the phase assembler `heroku-generate-assemble.md`), which runs the phase completion handoff gate per its `_postconditions`.
