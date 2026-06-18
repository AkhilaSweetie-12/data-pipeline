# =====================================================================
# Retail DataSecOps - Azure infrastructure (DEV)
# Provisions: Resource Group, ADLS Gen2, Azure SQL, Key Vault, Databricks
# =====================================================================
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "rg" {
  name     = "${var.prefix}-rg"
  location = var.location
}

# ---------------- ADLS Gen2 (medallion storage) ----------------
resource "azurerm_storage_account" "adls" {
  name                     = "${var.prefix}adls"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true # Hierarchical namespace = Data Lake Gen2
}

resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

# ---------------- Azure SQL (OLTP source) ----------------
resource "azurerm_mssql_server" "sql" {
  name                         = "${var.prefix}-${var.sql_location}-sql"
  resource_group_name          = azurerm_resource_group.rg.name
  location                     = var.sql_location
  version                      = "12.0"
  administrator_login          = var.sql_admin_username
  administrator_login_password = var.sql_admin_password
}

resource "azurerm_mssql_database" "db" {
  name      = "retail"
  server_id = azurerm_mssql_server.sql.id
  sku_name  = "Basic"
}

resource "azurerm_mssql_firewall_rule" "allow_azure" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.sql.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# ---------------- Key Vault (secrets) ----------------
resource "azurerm_key_vault" "kv" {
  name                       = "${var.prefix}-kv"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = false
  soft_delete_retention_days = 7
}

resource "azurerm_key_vault_access_policy" "deployer" {
  key_vault_id = azurerm_key_vault.kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
}

resource "azurerm_key_vault_secret" "sql_host" {
  name         = "sql-server-host"
  value        = "${azurerm_mssql_server.sql.name}.database.windows.net"
  key_vault_id = azurerm_key_vault.kv.id
  depends_on   = [azurerm_key_vault_access_policy.deployer]
}

resource "azurerm_key_vault_secret" "sql_db" {
  name         = "sql-database"
  value        = azurerm_mssql_database.db.name
  key_vault_id = azurerm_key_vault.kv.id
  depends_on   = [azurerm_key_vault_access_policy.deployer]
}

resource "azurerm_key_vault_secret" "sql_user" {
  name         = "sql-username"
  value        = var.sql_admin_username
  key_vault_id = azurerm_key_vault.kv.id
  depends_on   = [azurerm_key_vault_access_policy.deployer]
}

resource "azurerm_key_vault_secret" "sql_pwd" {
  name         = "sql-password"
  value        = var.sql_admin_password
  key_vault_id = azurerm_key_vault.kv.id
  depends_on   = [azurerm_key_vault_access_policy.deployer]
}

# ---------------- Databricks workspace ----------------
resource "azurerm_databricks_workspace" "dbx" {
  name                = "${var.prefix}-dbx"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "premium" # required for Unity Catalog & RBAC
}

# ---------------- Azure Monitor: Action Group ----------------
resource "azurerm_monitor_action_group" "alerts" {
  name                = "${var.prefix}-incident-ag"
  resource_group_name = azurerm_resource_group.rg.name
  short_name          = "incidents"

  email_receiver {
    name          = "platform-owner"
    email_address = var.alert_email
  }
}

# ---------------- Azure Monitor: SQL DTU alert ----------------
resource "azurerm_monitor_metric_alert" "sql_dtu" {
  name                = "${var.prefix}-sql-dtu-high"
  resource_group_name = azurerm_resource_group.rg.name
  scopes              = [azurerm_mssql_database.db.id]
  description         = "Alert when SQL database DTU consumption exceeds 80%"
  severity            = 2
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.Sql/servers/databases"
    metric_name      = "dtu_consumption_percent"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.alerts.id
  }
}

# ---------------- Azure Monitor: SQL connection failures alert ----
resource "azurerm_monitor_metric_alert" "sql_connections" {
  name                = "${var.prefix}-sql-failed-connections"
  resource_group_name = azurerm_resource_group.rg.name
  scopes              = [azurerm_mssql_database.db.id]
  description         = "Alert on SQL connection failures (pipeline JDBC errors)"
  severity            = 1
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.Sql/servers/databases"
    metric_name      = "connection_failed"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 5
  }

  action {
    action_group_id = azurerm_monitor_action_group.alerts.id
  }
}

# ---------------- Azure Monitor: Storage availability alert ------
resource "azurerm_monitor_metric_alert" "adls_availability" {
  name                = "${var.prefix}-adls-availability"
  resource_group_name = azurerm_resource_group.rg.name
  scopes              = [azurerm_storage_account.adls.id]
  description         = "Alert when ADLS Gen2 availability drops below 99%"
  severity            = 1
  frequency           = "PT5M"
  window_size         = "PT15M"

  criteria {
    metric_namespace = "Microsoft.Storage/storageAccounts"
    metric_name      = "Availability"
    aggregation      = "Average"
    operator         = "LessThan"
    threshold        = 99
  }

  action {
    action_group_id = azurerm_monitor_action_group.alerts.id
  }
}
