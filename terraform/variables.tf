variable "prefix" {
  description = "Resource name prefix (lowercase, alphanumeric)"
  type        = string
  default     = "retaildsops"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "sql_location" {
  description = "Azure region for the SQL server (some subscriptions restrict SQL provisioning in certain regions)"
  type        = string
  default     = "centralindia"
}

variable "sql_admin_username" {
  description = "Azure SQL administrator login"
  type        = string
  default     = "sqladmin"
}

variable "sql_admin_password" {
  description = "Azure SQL administrator password"
  type        = string
  sensitive   = true
}
