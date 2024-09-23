module "storage_account" {
  source              = "../../modules/storage_account"
  resource_group_name = var.resource_group_name
  storage_account_name = var.storage_account_name
  location            = var.location
}

module "event_subscription" {
  source                 = "../../modules/event_subscription"
  resource_group_name     = var.resource_group_name
  storage_account_id      = module.storage_account.id
  event_subscription_name = var.event_subscription_name
  webhook_endpoint_url    = var.webhook_endpoint_url
}
