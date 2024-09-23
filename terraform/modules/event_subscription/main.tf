resource "azurerm_eventgrid_event_subscription" "blob_created" {
  name                = var.event_subscription_name
  scope               = var.storage_account_id
  included_event_types = ["Microsoft.Storage.BlobCreated"]

  destination {
    endpoint_type = "webhook"
    endpoint_url  = var.webhook_endpoint_url
  }

  retry_policy {
    max_delivery_attempts = 3
    event_time_to_live    = 1440
  }
}
