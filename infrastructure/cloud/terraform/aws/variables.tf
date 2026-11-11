variable "region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  description = "The full stack (Keycloak included) needs about 4 GB RAM. t3.medium is NOT free tier; t3.micro (free tier) only fits the VPN + proxy subset."
  type        = string
  default     = "t3.medium"
}

variable "admin_cidr" {
  description = "Your public IP in CIDR form (x.x.x.x/32) for SSH"
  type        = string
  validation {
    condition     = var.admin_cidr != "0.0.0.0/0"
    error_message = "Do not open SSH to the world; pass your own /32."
  }
}

variable "vpn_client_cidrs" {
  description = "Where VPN clients may connect from"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "ssh_public_key" {
  type = string
}

variable "repo_url" {
  description = "Git URL of this repository (cloned onto the host)"
  type        = string
}
