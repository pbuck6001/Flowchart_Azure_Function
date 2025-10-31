# Azure Flowchart Generator Function App Deployment Guide (Local Rendering)

This guide provides comprehensive instructions for deploying the **Azure Flowchart Generator Function App**. This updated solution ensures that all data remains within your Azure environment by implementing **local Mermaid rendering**.

The function now:
1.  Accepts a natural language description of a flowchart via an HTTP POST request.
2.  Converts the description to Mermaid syntax using **Azure OpenAI**.
3.  **Crucially, it renders the Mermaid syntax to a PNG image locally within the Azure Function App using the `mermaid-cli` (mmdc) tool, eliminating the need to send data to an external service like `mermaid.ink`.**

The infrastructure is defined using **Terraform** for seamless deployment from your preferred environment, such as **GitHub Codespaces** or a local machine with VS Code.

## 1. Prerequisites

Before starting, ensure you have the following in your environment:

1.  **Azure Account and Subscription:** You need an active Azure subscription.
2.  **Azure CLI:** Used for logging in and authenticating Terraform.
3.  **Terraform CLI:** Used to deploy the infrastructure.
4.  **Azure OpenAI Service:** You must have an existing Azure OpenAI resource with a deployed model.
    *   The function code is configured to use a deployment named `gpt-4.1-mini`. If your deployment has a different name (e.g., `gpt-35-turbo`), you must update the `openai_deployment_name` variable in `terraform/main.tf` and the `AZURE_OPENAI_DEPLOYMENT_NAME` setting in the Function App after deployment.

## 2. Infrastructure Deployment (Terraform)

The infrastructure deployment will create the following Azure resources:

*   Resource Group
*   Storage Account
*   Application Insights
*   Consumption Plan (for Azure Functions)
*   Python Azure Function App

### Step 2.1: Authenticate with Azure

Open your terminal in GitHub Codespaces and run the following command to log in to Azure. Follow the instructions to complete the device login flow.

\`\`\`bash
az login
\`\`\`

### Step 2.2: Initialize Terraform

Navigate to the Terraform directory and initialize the backend.

\`\`\`bash
cd azure-mermaid-function/terraform
terraform init
\`\`\`

### Step 2.3: Review and Plan Deployment

Review the resources that Terraform will create.

\`\`\`bash
terraform plan
\`\`\`

### Step 2.4: Apply Deployment

Apply the plan to create the Azure resources. Type `yes` when prompted.

\`\`\`bash
terraform apply
\`\`\`

The output will provide the name of your new Function App (e.g., `mermaid-flowchart-xxxxxxxx`) and a critical note about the next step.

### Step 2.5: Configure Azure OpenAI Settings (CRITICAL)

The Terraform script creates the Function App but cannot securely set your sensitive Azure OpenAI API key and endpoint. **You must set these manually** in the Azure Portal or via the Azure CLI.

1.  **Get your Azure OpenAI details:**
    *   **Endpoint:** The base URL for your Azure OpenAI resource (e.g., `https://<your-openai-resource>.openai.azure.com/`).
    *   **API Key:** One of the two keys for your Azure OpenAI resource.
2.  **Update Function App Settings:**
    *   Go to the Azure Portal, find your newly created Function App (name is in the Terraform output).
    *   Navigate to **Configuration** -> **Application settings**.
    *   Find and update the following two settings with your actual values:
        *   `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL.
        *   `OPENAI_API_KEY`: Your Azure OpenAI API key.

## 3. Code Deployment and Local Mermaid Setup

The local rendering requires **Node.js** and the **`mermaid-cli`** package to be installed on the Function App environment. We will use a custom deployment script for this.

### Step 3.1: Install Azure Functions Core Tools

If not already installed in your Codespace, install the Azure Functions Core Tools.

\`\`\`bash
# Install dependencies for the Azure Functions Core Tools
sudo apt-get update
sudo apt-get install -y apt-transport-https
# Add the Microsoft package repository
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" > /etc/apt/sources.list.d/azure-cli.list'
# Install the Core Tools
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
\`\`\`

### Step 3.2: Configure Deployment for Node.js Dependency (CRITICAL)

The standard Python deployment process does not automatically install Node.js dependencies. The `install_mermaid_cli.sh` script is provided to install the necessary `mermaid-cli` package.

**You must manually execute this script on the Function App's Kudu console after the initial code deployment.**

1.  **Publish the code** (Step 3.3).
2.  **Access the Kudu Console** (Advanced Tools) for your Function App in the Azure Portal.
3.  **Navigate to the `site/wwwroot` directory** and manually execute the script:

    \`\`\`bash
    # In the Kudu Console's Debug Console (Bash)
    cd /home/site/wwwroot
    chmod +x install_mermaid_cli.sh
    ./install_mermaid_cli.sh
    \`\`\`

### Step 3.3: Publish the Code

Navigate back to the project root directory and publish the code. Replace `<YOUR_FUNCTION_APP_NAME>` with the name from your Terraform output.

\`\`\`bash
cd .. # Back to azure-mermaid-function/
func azure functionapp publish <YOUR_FUNCTION_APP_NAME> --python
\`\`\`

**Remember to perform the manual Kudu step (Step 3.2) after this deployment for the local rendering to work.**

## 4. Usage

Once deployed and configured, the function can be called via a simple HTTP POST request.

### Endpoint URL

The endpoint URL will be:

\`\`\`
https://<YOUR_FUNCTION_APP_NAME>.azurewebsites.net/api/DiagramGenerator
\`\`\`

### Example Request (using cURL)

You can test the endpoint by sending a JSON payload with a `prompt`.

\`\`\`bash
# Replace <YOUR_FUNCTION_URL> with the actual URL
# Replace <YOUR_FUNCTION_KEY> with the Function Key (found in the Azure Portal under Function -> DiagramGenerator -> Function Keys)
curl -X POST "https://<YOUR_FUNCTION_URL>/api/DiagramGenerator?code=<YOUR_FUNCTION_KEY>" \
     -H "Content-Type: application/json" \
     --data '{"prompt": "A simple login process where the user enters credentials, if valid they proceed to the dashboard, otherwise they try again."}' \
     --output "flowchart.png"
\`\`\`

The response will be a PNG image file, which will be saved as `flowchart.png` in your current directory.

## 5. Clean Up

To destroy the Azure resources created by Terraform, run the following commands from the `azure-mermaid-function/terraform` directory:

\`\`\`bash
terraform destroy
\`\`\`
Type `yes` when prompted.
\`\`\`
