# variables.tf — inputs the pipeline passes in (sourced from the ServiceNow request)
variable "vm_name" {
  description = "VM name; derive it from the RITM (e.g. vm-<ritm-number>) for idempotency"
  type        = string
}
variable "vm_size" {
  description = "Azure VM size. Keep it small/cheap."
  type        = string
  default     = "Standard_B1s"
  validation {
    condition     = contains(["Standard_B1s", "Standard_B2s"], var.vm_size)
    error_message = "For cost safety this training only allows Standard_B1s or Standard_B2s."
  }
}
variable "region" {
  description = "Azure region"
  type        = string
  default     = "centralindia"
}
variable "admin_username" {
  description = "Admin user for the VM"
  type        = string
  default     = "azureuser"
}
variable "ssh_public_key" {
  description = "SSH public key for VM access. Generate with: ssh-keygen -t rsa -b 4096 -f ~/.ssh/training_key"
  type        = string
}
variable "create_public_ip" {
  description = "Set true to attach a public IP + NSG (needed for Track B Ansible-over-SSH from CI). Keep false for Track A."
  type        = bool
  default     = false
}
variable "allowed_ssh_source" {
  description = "CIDR/IP allowed to SSH when create_public_ip=true. '*' = anywhere (only ok for a short-lived training VM you tear down fast). Tighten to 'your.ip/32' if you can."
  type        = string
  default     = "*"
}
