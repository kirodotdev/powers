---
name: "shipstatic"
displayName: "Shipstatic"
description: "Deploy static sites and manage custom domains on Shipstatic. Upload files, link domains, configure DNS, and manage deployments from your editor."
keywords: ["shipstatic", "deploy", "static site", "hosting", "domains", "dns", "upload", "publish"]
author: "Shipstatic"
---

# Shipstatic

## Overview

Deploy static websites to Shipstatic directly from your editor. Upload a directory, get a live URL in seconds. Link custom domains with automatic TLS. No build steps, no framework lock-in — just upload your files and ship.

This power connects to the Shipstatic MCP server for managing deployments and domains.

**Key capabilities:**

- **Deploy instantly**: Upload any directory and get a live URL
- **Custom domains**: Link your own domain with automatic HTTPS
- **Internal domains**: Free `*.shipstatic.dev` subdomains, instant, no DNS required
- **Labels**: Organize deployments and domains with labels
- **Instant rollback**: Switch a domain to any previous deployment

## Available MCP Servers

### shipstatic

**Connection:** Local stdio server via `npx @shipstatic/mcp`
**Authentication:** Requires `SHIP_API_KEY` environment variable

### Deployment Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `deployments_upload` | Upload deployment from directory | `path` (required), `subdomain` (optional), `labels` (optional) |
| `deployments_list` | List all deployments | — |
| `deployments_get` | Show deployment information | `deployment` |
| `deployments_set` | Set deployment labels | `deployment`, `labels` |
| `deployments_remove` | Delete deployment permanently | `deployment` |

### Domain Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `domains_set` | Create domain, link to deployment, or update labels | `domain` (required), `deployment` (optional), `labels` (optional) |
| `domains_list` | List all domains | — |
| `domains_get` | Show domain information | `domain` |
| `domains_records` | Get required DNS records for a domain | `domain` |
| `domains_validate` | Check if domain name is valid and available | `domain` |
| `domains_verify` | Trigger DNS verification for external domain | `domain` |
| `domains_remove` | Delete domain permanently | `domain` |

### Account Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `whoami` | Show current account information | — |

## Common Workflows

### Workflow 1: Deploy a Site

Upload a build output directory to get a live URL:

```
deployments_upload({ path: "/absolute/path/to/dist" })
```

Optionally suggest a subdomain and add labels:

```
deployments_upload({
  path: "/absolute/path/to/dist",
  subdomain: "my-site",
  labels: ["production", "v1.0"]
})
```

The response includes the deployment ID and live URL.

### Workflow 2: Set Up an Internal Domain

Internal domains (`*.shipstatic.dev`) are free and instant — no DNS configuration needed:

```
// Reserve a subdomain
domains_set({ domain: "my-site" })

// Link it to a deployment
domains_set({ domain: "my-site", deployment: "happy-cat-abc1234" })
```

### Workflow 3: Set Up a Custom Domain

Custom domains require DNS configuration. Follow these steps in order:

```
// Step 1: Check if the domain name is valid and available
domains_validate({ domain: "www.example.com" })

// Step 2: Create the domain and link to a deployment
domains_set({ domain: "www.example.com", deployment: "happy-cat-abc1234" })

// Step 3: Get the required DNS records
domains_records({ domain: "www.example.com" })

// Step 4: Tell the user to configure DNS records at their provider

// Step 5: After DNS is configured, trigger verification
domains_verify({ domain: "www.example.com" })
```

### Workflow 4: Switch a Domain to a Different Deployment

Instant rollback or promotion — just link the domain to another deployment:

```
domains_set({ domain: "www.example.com", deployment: "other-deploy-xyz9876" })
```

## Best Practices

### Domains

- **Always use subdomains** — apex domains (`example.com`) are not supported. Use `www.example.com` or `blog.example.com`.
- **Validate first** — always call `domains_validate` before `domains_set` for custom domains to catch issues early.
- **Internal domains are instant** — for quick previews, use internal subdomains (`my-site.shipstatic.dev`) instead of custom domains.

### Deployments

- **Use absolute paths** — the `path` parameter for `deployments_upload` must be an absolute path to the directory.
- **Use labels** — label deployments with `production`, version numbers, or branch names for easy identification.
- **Upload the build output** — deploy the built output directory (e.g. `dist/`, `build/`, `_site/`), not the source directory.

## Troubleshooting

### Error: "Invalid or missing API key"

**Cause:** `SHIP_API_KEY` environment variable not set or invalid.
**Solution:**

1. Get your API key at https://my.shipstatic.com/settings
2. Key starts with `ship-`
3. Verify the key is set in your MCP configuration

### Error: "Domain not available"

**Cause:** Domain name is already taken or invalid format.
**Solution:**

1. Call `domains_validate` to check availability
2. Ensure you're using a subdomain, not an apex domain
3. Try a different subdomain name

### Error: "DNS verification failed"

**Cause:** DNS records not yet configured or not propagated.
**Solution:**

1. Call `domains_records` to confirm the required records
2. Verify records are configured at the DNS provider
3. Wait for DNS propagation (can take minutes to hours)
4. Retry `domains_verify`

### Error: "Deployment not found"

**Cause:** Invalid deployment ID or deployment was deleted.
**Solution:**

1. Call `deployments_list` to see all deployments
2. Verify the deployment ID format (e.g. `happy-cat-abc1234`)

## Configuration

**Authentication required:** Shipstatic API key

**Setup steps:**

1. Create an account at https://my.shipstatic.com
2. Go to Settings to find your API key (starts with `ship-`)
3. Configure the key in your MCP client:

```json
{
  "mcpServers": {
    "shipstatic": {
      "command": "npx",
      "args": ["-y", "@shipstatic/mcp"],
      "env": {
        "SHIP_API_KEY": "ship-..."
      }
    }
  }
}
```

**Requirements:** Node.js >= 20
