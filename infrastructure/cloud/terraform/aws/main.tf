# ZeroGate on AWS: one EC2 host running the same Docker Compose lab.
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.region
  default_tags { tags = { Project = "zerogate", ManagedBy = "terraform" } }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_vpc" "lab" {
  cidr_block           = "10.50.0.0/16"
  enable_dns_hostnames = true
}

resource "aws_internet_gateway" "lab" {
  vpc_id = aws_vpc.lab.id
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.lab.id
  cidr_block              = "10.50.1.0/24"
  map_public_ip_on_launch = true
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.lab.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab.id
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Only the VPN ports face the internet. Admin UIs are reached over SSH port-forwarding or the VPN itself.
resource "aws_security_group" "gateway" {
  name_prefix = "zerogate-gw-"
  description = "ZeroGate VPN gateway"
  vpc_id      = aws_vpc.lab.id

  ingress {
    description = "WireGuard"
    from_port   = 51820
    to_port     = 51820
    protocol    = "udp"
    cidr_blocks = var.vpn_client_cidrs
  }
  ingress {
    description = "IKEv2"
    from_port   = 500
    to_port     = 500
    protocol    = "udp"
    cidr_blocks = var.vpn_client_cidrs
  }
  ingress {
    description = "IPsec NAT-T"
    from_port   = 4500
    to_port     = 4500
    protocol    = "udp"
    cidr_blocks = var.vpn_client_cidrs
  }
  ingress {
    description = "SSH from the admin address only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }
  egress {
    description = "Outbound (image pulls, proxied web traffic)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "admin" {
  key_name_prefix = "zerogate-"
  public_key      = var.ssh_public_key
}

resource "aws_instance" "lab" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.gateway.id]
  key_name               = aws_key_pair.admin.key_name
  user_data              = templatefile("${path.module}/user_data.sh.tftpl", { repo_url = var.repo_url })

  metadata_options {
    http_tokens = "required" # IMDSv2 only
  }
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }
  tags = { Name = "zerogate-lab" }
}

resource "aws_eip" "lab" {
  instance = aws_instance.lab.id
  domain   = "vpc"
}
