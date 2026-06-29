# outputs.tf — values the pipeline reads back and sends to ServiceNow
output "vm_name" {
  description = "The provisioned VM name"
  value       = azurerm_linux_virtual_machine.vm.name
}
output "public_ip" {
  description = "Public IP address used by Ansible to connect over SSH"
  value       = var.create_public_ip ? azurerm_public_ip.pip[0].ip_address : ""
}
output "private_ip" {
  description = "Private IP of the VM"
  value       = azurerm_network_interface.nic.private_ip_address
}
output "resource_group" {
  description = "Resource group (used by the teardown step)"
  value       = azurerm_resource_group.rg.name
}
output "vm_size" {
  value = azurerm_linux_virtual_machine.vm.size
}
output "location" {
  value = azurerm_resource_group.rg.location
}
