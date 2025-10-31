#!/bin/bash

# This script is designed to be run during the Azure Function App deployment
# to install the necessary Node.js dependencies for Mermaid CLI.

echo "Starting installation of Node.js and Mermaid CLI..."

# 1. Install Node.js and npm (if not already present in the Azure Function Linux image)
# Azure Functions Linux Consumption plan images often have Node.js pre-installed,
# but this ensures it's available or updated.
# We will rely on the fact that the Python worker runs on a Linux image
# that allows for shell execution during deployment (e.g., via a custom build step or Kudu).

# Check if Node.js is installed
if ! command -v node &> /dev/null
then
    echo "Node.js not found. Skipping explicit installation, relying on Azure Functions environment."
    # In a real-world scenario, you might add a step here to install Node.js if necessary,
    # but for Azure Functions, it's generally better to rely on the base image.
fi

# 2. Install mermaid-cli globally
# The global installation ensures the 'mmdc' command is available in the PATH.
echo "Installing mermaid-cli globally..."
npm install -g @mermaid-js/mermaid-cli

if [ $? -eq 0 ]; then
    echo "Mermaid CLI installed successfully."
    echo "mmdc version:"
    mmdc --version
else
    echo "Error installing Mermaid CLI."
    exit 1
fi

# 3. Install Chromium dependencies for mmdc (if necessary)
# mmdc uses Puppeteer, which requires certain system libraries.
# This step is often necessary for headless Chromium to run.
# However, for Azure Functions, we will rely on the pre-installed libraries
# in the base image to keep the deployment simple.

# Clean up npm cache
npm cache clean --force

echo "Mermaid CLI installation script finished."
