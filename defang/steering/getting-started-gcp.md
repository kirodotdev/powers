# Get Started with Defang

## Overview

Guide on how to use Defang MCP server on how to set up and deploy to GCP.

**IMPORTANT**:

- This steering file assumes that the user has already completed the onboarding steps outlined in the #Onboarding section from the defang/POWER.md file.
- Do not call the defang MCP "estimate" tool in this steering file, as it is not part of this getting started flow.

## Trigger

When user runs the Defang power tool, or "I would like to deploy to gcp".

## Step 1: Check if there is a stack in the current project

Check if there are any stacks in the current project by using the defang MCP tool called "list-stacks".

- If there is no stack, prompt user to create a new stack using defang MCP tool "create_gcp_stack".

A stack will need the following information:

- Stack name
- Region (default: us-central1)
- GCPProjectID
- Mode ["affordable", "balanced", "high_availability"] (default: affordable)

## Step 2: Select the stack

Now prompt user to select the stack to deploy to by calling the defang MCP "list-stacks" tool.

Present the user with the list of stacks to choose from.

Then we set the selected stack as the active stack by calling the defang MCP "select_stack" tool.

## Step 3: Deploy the project

Now that the stack is selected, we can deploy the project using the defang MCP "deploy" tool.

## Step 4: Post-deployment

After the defang MCP "deploy" tool call ends, present the return data from tool. Lastly, Kiro should not progress with any further steps unless user explicitly requests so.
