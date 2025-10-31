# --- Provider Configuration ---
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# Configure the Microsoft Azure Provider
# Assumes Azure CLI is already logged in (az login)
provider "azurerm" {
  features {}
}

# --- Variables ---
variable "resource_group_name" {
  description = "The name of the resource group to create"
  type        = string
  default     = "rg-mermaid-flowchart-app"
}

variable "location" {
  description = "The Azure region to deploy resources to"
  type        = string
  default     = "eastus"
}

variable "app_service_plan_sku" {
  description = "The SKU for the App Service Plan (e.g., Y1 for Consumption plan)"
  type        = string
  default     = "Y1" # Consumption plan for Azure Functions
}

variable "function_app_name_prefix" {
  description = "Prefix for the Function App name (must be globally unique)"
  type        = string
  default     = "mermaid-flowchart"
}

variable "openai_deployment_name" {
  description = "The name of the Azure OpenAI deployment model"
  type        = string
  default     = "gpt-4.1-mini"
}

# --- Locals ---
locals {
  # Generate a unique suffix to ensure global uniqueness for storage and function app names
  random_suffix = substr(sha1(timestamp()), 0, 8)
  storage_account_name = "st${replace(var.function_app_name_prefix, "-", "")}${local.random_suffix}"
  function_app_name    = "${var.function_app_name_prefix}-${local.random_suffix}"
}


# --- Resource Group ---
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# --- Storage Account (Required by Function App) ---
resource "azurerm_storage_account" "sa" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# --- Application Insights (For monitoring) ---
resource "azurerm_application_insights" "app_insights" {
  name                = "${local.function_app_name}-ai"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
}

# --- App Service Plan (Consumption Plan for Functions) ---
resource "azurerm_service_plan" "asp" {
  name                = "${local.function_app_name}-plan"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = var.app_service_plan_sku # Y1 is the Consumption Plan
}

# --- Function App ---
resource "azurerm_linux_function_app" "func_app" {
  name                       = local.function_app_name
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  service_plan_id            = azurerm_service_plan.asp.id
  storage_account_name       = azurerm_storage_account.sa.name
  storage_account_access_key = azurerm_storage_account.sa.primary_access_key

  # Python 3.11 runtime
  functions_extension_version = "~4"
  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    # Required for Function App
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "WEBSITE_RUN_FROM_PACKAGE" = "1" # Deploy from zip package

    # Application Insights
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.app_insights.instrumentation_key

    # Custom Settings for the Function Code
    "AZURE_OPENAI_DEPLOYMENT_NAME" = var.openai_deployment_name
    
    # Placeholder for Azure OpenAI Configuration - User MUST update these in Azure Portal or another deployment step
    "AZURE_OPENAI_ENDPOINT" = "https://<your-openai-resource>.openai.azure.com/"
    "OPENAI_API_KEY" = "YOUR_AZURE_OPENAI_KEY_HERE"
  }
}

# --- Outputs ---
output "function_app_name" {
  value       = azurerm_linux_function_app.func_app.name
  description = "The name of the deployed Azure Function App."
}

output "function_app_url" {
  value       = azurerm_linux_function_app.func_app.default_hostname
  description = "The default hostname of the deployed Azure Function App."
}

output "resource_group_name" {
  value       = azurerm_resource_group.rg.name
  description = "The name of the resource group."
}

output "note_for_user" {
  value       = "IMPORTANT: You must manually configure the 'AZURE_OPENAI_ENDPOINT' and 'OPENAI_API_KEY' application settings in the Azure Portal after deployment, as the key is sensitive and should not be hardcoded in Terraform."
  description = "A note regarding required post-deployment configuration."
}
