# variables.tf — inputs for Track B target VM
variable "vm_name" {
  description = "VM name derived from the Change Request ticket"
  type        = string
}
variable "vm_size" {
  description = "Azure VM size. Using B2as_v2 to bypass subscription limits."
  type        = string
  default     = "Standard_B2as_v2"
  validation {
    condition     = contains(["Standard_B1s", "Standard_B2s", "Standard_B1s_v2", "Standard_B2s_v2", "Standard_B2as_v2"], var.vm_size)
    error_message = "For cost safety this training only allows B-series sizes."
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
  description = "SSH public key injected into the VM for Ansible access"
  type        = string
}
variable "create_public_ip" {
  description = "Must be true for Track B so the GitHub runner can connect over SSH"
  type        = bool
  default     = true
}
variable "allowed_ssh_source" {
  description = "Allowed IP range to SSH. Set to * for GitHub runner access."
  type        = string
  default     = "*"
}
