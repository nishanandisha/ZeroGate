# AWS deployment (optional)

Same Compose lab on one EC2 host. **Status: `terraform validate` passes; it has not been applied to a real account.**

```bash
terraform init
terraform apply -var admin_cidr="$(curl -s ifconfig.me)/32" -var ssh_public_key="$(cat ~/.ssh/id_ed25519.pub)" -var repo_url=<git url>
terraform output ssh_tunnel     # then open http://localhost:3300
terraform destroy               # when finished
```

* **Cost:** the default `t3.medium` is not free tier (about 4 GB RAM is needed for Keycloak plus the rest).
  A free-tier `t3.micro` can run only the VPN and proxy services.
* Only UDP 51820/500/4500 face the internet. SSH is limited to `admin_cidr`. Admin UIs are reached through the SSH tunnel.
* Cloud-init replaces every default password in `.env` with a random one.
* Known gap: Keycloak's public URL stays `http://localhost:8080`, which works through the SSH tunnel only.
