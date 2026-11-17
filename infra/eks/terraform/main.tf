# Ephemeral EKS for e2e: apply -> deploy -> test -> destroy in one CI run (eks-e2e.yml).
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" { region = var.region }

variable "region" { default = "us-west-2" }
variable "name" { default = "promptvet-e2e" }

data "aws_availability_zones" "az" { state = "available" }

module "vpc" {
  source             = "terraform-aws-modules/vpc/aws"
  version            = "~> 5.13"
  name               = var.name
  cidr               = "10.42.0.0/16"
  azs                = slice(data.aws_availability_zones.az.names, 0, 2)
  private_subnets    = ["10.42.1.0/24", "10.42.2.0/24"]
  public_subnets     = ["10.42.101.0/24", "10.42.102.0/24"]
  enable_nat_gateway = true
  single_nat_gateway = true
  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }
}

module "eks" {
  source                                   = "terraform-aws-modules/eks/aws"
  version                                  = "~> 20.24"
  cluster_name                             = var.name
  cluster_version                          = "1.31"
  vpc_id                                   = module.vpc.vpc_id
  subnet_ids                               = module.vpc.private_subnets
  cluster_endpoint_public_access           = true
  enable_cluster_creator_admin_permissions = true
  cluster_addons = { coredns = {}, kube-proxy = {}, vpc-cni = {}, eks-pod-identity-agent = {} }
  eks_managed_node_groups = {
    default = { instance_types = ["t3.medium"], min_size = 2, max_size = 3, desired_size = 2 }
  }
}

output "cluster_name" { value = module.eks.cluster_name }
