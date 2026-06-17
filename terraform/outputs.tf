output "resource_group" {
  value = azurerm_resource_group.rg.name
}

output "sql_server_fqdn" {
  value = "${azurerm_mssql_server.sql.name}.database.windows.net"
}

output "sql_database" {
  value = azurerm_mssql_database.db.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.kv.vault_uri
}

output "databricks_workspace_url" {
  value = "https://${azurerm_databricks_workspace.dbx.workspace_url}"
}

output "adls_account" {
  value = azurerm_storage_account.adls.name
}
