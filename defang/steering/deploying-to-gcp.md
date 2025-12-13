# Deploying to GCP with Defang

## Overview

This guide describes how to deploy applications to GCP with Defang.

**IMPORTANT**:

- Avoid automatically estimating deployment costs, wait for the user to request it.

## Trigger

When the user's project has a compose.yaml file and would like to deploy to aws.

## Step 1: Select the stack to which the application will be deployed

A stack is a single deployed instance of your project in a specific AWS account and region. You can deploy multiple stacks into the same account and region, for example: `staging` and `production`.

Check if there are any stacks in the current project.

- If a stack is already defined, ask the user if they would like to select one of the existing stacks, or if they would like to create a new one.
- If there are no stacks, prompt user to create a new AWS stack.

The following information will be needed to create a stack:

- Stack name: must be alphanumeric and must not start with a number
- Region: for example: `us-central1`
- GCP Project ID: The GCP Project in which the application will be deployed. This must be created beforehand in the GCP Console.
- Deployment Mode: The deployment mode is the primary parameter for managing the cost and resiliency of your application's deployment. The following deployment modes are available: `affordable`, `balanced`, and `high_availability`. The default is `affordable`. Learn more at https://docs.defang.io/docs/concepts/deployment-modes

If a new stack is created, make sure to select it before it can be used.

## Step 2: Deploy the project

Now that a stack is selected, the project can be deployed.

## Step 3: Monitor the deployment

Once the deployment has begun, progress can be monitored by tailing the logs or periodically checking service status.
