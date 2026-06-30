# AVM Post Deployment Guide

> **📋 Note**: This guide is specifically for post-deployment steps after using the AVM template. For complete deployment from scratch, see the main [Deployment Guide](./DeploymentGuide.md).

---

This document provides guidance on post-deployment steps after deploying the Modernize your code solution accelerator from the [AVM (Azure Verified Modules) repository](https://github.com/Azure/bicep-registry-modules/tree/main/avm/ptn/sa/modernize-your-code).

## Pre-requisites

Ensure you have a **Deployed Infrastructure** - A successful Modernize your code solution accelerator deployment from the [AVM repository](https://github.com/Azure/bicep-registry-modules/tree/main/avm/ptn/sa/modernize-your-code)

## Next Steps

1. **Access the Application**
   
   Navigate to your Azure portal, open the resource group created by the deployment, locate the frontend Container App, and copy the Application URL to access the solution.

2. **Add App Authentication**
   
    If you chose to enable authentication for the deployment, follow the steps in [App Authentication](./AddAuthentication.md)

## Running the application

To help you get started, sample Informix queries have been included in the `data/informix/functions` and `data/informix/simple` directories. You can choose to upload these files to test the application.
