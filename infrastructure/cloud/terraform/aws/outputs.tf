output "public_ip" {
  value = aws_eip.lab.public_ip
}

output "ssh_tunnel" {
  description = "Forward the admin UIs to your machine"
  value       = "ssh -L 3300:localhost:3300 -L 8080:localhost:8080 -L 8443:localhost:8443 -L 8800:localhost:8800 ubuntu@${aws_eip.lab.public_ip}"
}

output "wireguard_endpoint" {
  value = "${aws_eip.lab.public_ip}:51820"
}
