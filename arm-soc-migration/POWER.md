---
name: "arm-soc-migration"
displayName: "Perform Migration between Arm SoC"
description: "Guides migration of code from one Arm SoC to another, with architecture-aware analysis and safe migration practices."
keywords: ["arm", "soc", "migration", "embedded", "cortex", "neon", "sve", "hal", "platform", "cross-compile"]
author: "Arm"
---

# Kiro Arm SoC Migration Power

A Kiro power that guides developers through migrating code from one Arm-based System-on-Chip (SoC) to another, ensuring architecture-aware analysis and safe migration practices.

## Overview

This power helps you migrate embedded, automotive, or general-purpose applications between different Arm SoCs while preserving functional behavior, safety properties, and code quality.

**Common migration scenarios:**
- AWS Graviton → Raspberry Pi
- AWS Graviton2 → AWS Graviton3
- NXP i.MX8 → NVIDIA Jetson Orin
- Qualcomm Snapdragon → STM32MP1

The power provides architecture-aware analysis, identifies platform-specific code, and guides safe refactoring while maintaining compatibility and performance.

## Available Steering Files

This power has the following steering files for detailed workflow guidance:

- **discovery** — Discovery and Analysis: scan codebases for platform-specific code, compare architectures, identify HAL requirements
- **planning** — Migration Planning: generate migration plans, risk assessments, and performance impact analysis
- **implementation** — Implementation Guidance: refactor platform-specific code, build HAL abstractions, update build systems
- **validation** — Validation and Testing: cross-compilation verification, performance benchmarking, functional test suites
- **constraints** — Migration constraints and safety rules that apply to all Arm SoC migrations

All conceptual knowledge is in this POWER.md file. The steering files provide detailed workflow examples with complete code samples.

## Onboarding

### Prerequisites

**Required Information:**
Before beginning any migration work, you must specify:
1. **Source Arm SoC** — Current platform (e.g., BCM2711, AWS Graviton2, NXP i.MX8)
2. **Target Arm SoC** — Destination platform (e.g., BCM2712, STM32MP1)

**System Requirements:**
- Cross-compilation toolchains for both source and target architectures
- Access to source code with build system (CMake, Make, or similar)
- Development environment with Arm analysis tools

### Installation

The Arm MCP Server runs as a Docker container, providing a consistent and isolated environment.

#### Docker Installation

**Step 1: Install Docker**

Ensure Docker is installed and running:
```bash
# Verify Docker installation
docker --version

# Test Docker is running
docker ps
```

If Docker is not installed:
- macOS: Download Docker Desktop from https://www.docker.com/products/docker-desktop
- Linux: `sudo apt-get install docker.io` or use your package manager
- Windows: Download Docker Desktop from https://www.docker.com/products/docker-desktop

**Step 2: Configure Kiro MCP Settings**

The Arm MCP Server is configured in Kiro's MCP configuration file. This power includes a pre-configured `mcp.json` that uses Docker.

```json
{
  "mcpServers": {
    "arm-mcp-server": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "--pull=always", "armlimited/arm-mcp:latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "ARM_MCP_CACHE_DIR": "~/.cache/arm-mcp",
        "ARM_MCP_TIMEOUT": "30"
      },
      "disabled": false,
      "autoApprove": ["knowledge_base_search", "sysreport_instructions"],
      "disabledTools": ["migrate_ease_scan"]
    }
  }
}
```

**Configuration Options Explained:**
- `command`: Uses Docker to run the containerized MCP server
- `args`: 
  - `run`: Start a new container
  - `--rm`: Automatically remove container when it exits
  - `-i`: Keep STDIN open for interactive communication
  - `--pull=always`: Always pull the latest image before running
  - `armlimited/arm-mcp:latest`: Official Arm MCP Docker image
- `env.FASTMCP_LOG_LEVEL`: Reduces logging verbosity (set to "DEBUG" for troubleshooting)
- `env.ARM_MCP_CACHE_DIR`: Directory for caching Arm documentation and embeddings
- `env.ARM_MCP_TIMEOUT`: Server timeout in seconds
- `autoApprove`: Tools that don't require user confirmation (safe read-only operations)
- `disabledTools`: Tools disabled for safety (migrate_ease_scan requires careful manual review)

**Step 3: First Run**

The Docker image will be automatically pulled when you first use this power. The `--pull=always` flag ensures you always have the latest version.

**First-time usage will:**
1. Pull the `armlimited/arm-mcp:latest` Docker image from Docker Hub
2. Start the container with MCP server
3. Initialize Arm knowledge base and embeddings
4. Connect to Kiro automatically

**Note:** The first launch may take 1-2 minutes as Docker downloads the image (~500MB). Subsequent launches are much faster as the image is cached locally.

**Optional: Pre-pull the Docker Image**

To avoid waiting during first use, you can pre-pull the image:
```bash
docker pull armlimited/arm-mcp:latest
```

#### Build Custom Docker Image (Advanced)

If you need to customize the Docker image:
```bash
# Clone the repository
git clone https://github.com/mcp/arm/arm-mcp
cd arm-mcp

# Build for your platform
docker build -f mcp-local/Dockerfile -t arm-mcp:custom mcp-local

# Update mcp.json to use your custom image
# Change "armlimited/arm-mcp:latest" to "arm-mcp:custom"
```

#### Verifying Installation

After installation, verify the MCP server is working:

**Step 1: Check Docker Image**
```bash
docker images | grep arm-mcp
```

**Step 2: Test Docker Container**
```bash
docker run --rm armlimited/arm-mcp:latest --version
```

**Step 3: Check MCP Server Status in Kiro**

1. Open Kiro → View → MCP Servers (or use Command Palette: "MCP: Show Servers")
2. Look for "arm-mcp-server" in the list
3. Status should show green/connected
4. If red/disconnected, click "Reconnect" or "Restart"

**Step 4: Test MCP Server Tools**

Ask Kiro to test the server:
```
"Search the Arm knowledge base for BCM2711 architecture information"
```

**Step 5: Verify Cross-Compilation Tools (Optional)**
```bash
aarch64-linux-gnu-gcc --version
arm-linux-gnueabihf-gcc --version
cmake --version
make --version
```

**If cross-compilation tools are missing:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf

# macOS
brew install aarch64-elf-gcc
brew install arm-none-eabi-gcc
```

### Initial Setup

**Step 1: Specify Migration Context**

Tell Kiro your source and target SoCs:
```
"I need to migrate from BCM2711 (Raspberry Pi 4) to BCM2712 (Raspberry Pi 5)"
```

**Step 2: Project Structure**

Ensure your project follows recommended structure:
```
project/
├── src/           # Application code
├── include/       # Headers
├── platform/      # Platform-specific code
├── hal/           # Hardware abstraction layer
└── CMakeLists.txt # Build configuration
```

## Common Workflows

### Workflow 1: Discovery and Analysis

Identify platform-specific code and architecture differences between source and target SoCs. This workflow scans your codebase for hard-coded addresses, direct register access, and platform-dependent logic, then compares architecture capabilities and identifies HAL requirements.

For detailed steps and complete examples, load the steering file:
```
readSteering: powerName="arm-soc-migration", steeringFile="discovery.md"
```

### Workflow 2: Migration Planning

Create a detailed migration strategy with phased timelines, risk assessments, and performance impact analysis. Covers risk categorization (high/medium/low), mitigation strategies, and expected performance deltas between source and target architectures.

For detailed steps and complete examples, load the steering file:
```
readSteering: powerName="arm-soc-migration", steeringFile="planning.md"
```

### Workflow 3: Implementation Guidance

Execute the migration with proper platform abstraction. Covers refactoring platform-specific code into HAL layers, updating build systems for dual-platform support, and implementing peripheral abstractions (GPIO, SPI, I2C) for both source and target SoCs.

For detailed steps and complete examples, load the steering file:
```
readSteering: powerName="arm-soc-migration", steeringFile="implementation.md"
```

### Workflow 4: Validation and Testing

Verify migration correctness and performance. Covers cross-compilation verification scripts, performance benchmarking frameworks, and functional test suites that validate identical behavior across both platforms.

For detailed steps and complete examples, load the steering file:
```
readSteering: powerName="arm-soc-migration", steeringFile="validation.md"
```

## MCP Server Tools

The Arm MCP Server provides these analysis capabilities:

### Architecture Analysis
- **knowledge_base_search**: Find Arm documentation and compatibility information
- **check_image**: Verify Docker image architecture support
- **skopeo**: Inspect container image architectures
- **mca**: Assembly code performance analysis

### Migration Analysis
- **sysreport_instructions**: Get system architecture information

**Note:** The `migrate_ease_scan` tool is disabled for this power to ensure manual, careful migration practices.

## Migration Constraints

This power enforces strict safety constraints defined in `constraints.md`:

### Critical Rules
- **Preserve Behavior**: No silent API or timing changes
- **Platform Abstraction**: SoC-specific code must be isolated in HAL layers
- **Safety Properties**: Maintain input validation and error handling
- **Documentation**: All changes must be justified and recorded

### Architecture Considerations
- Arm version differences (Armv7, Armv8, Armv9)
- Core type variations (Cortex-A72 vs Cortex-A76)
- SIMD capabilities (NEON, SVE, SVE2)
- Memory model and cache differences

## Troubleshooting

### MCP Server Connection Issues

**Problem:** Arm MCP Server won't start or connect

**Solutions:**
1. Verify Docker is running: `docker ps`
2. Check Docker permissions (Linux): `sudo usermod -aG docker $USER`
3. Test container directly: `docker run --rm -i armlimited/arm-mcp:latest`
4. Check Kiro MCP Server panel status
5. Force pull latest image: `docker pull armlimited/arm-mcp:latest`
6. Check logs in Kiro: Open MCP Servers panel → click "arm-mcp-server" → view logs
7. Enable debug logging: Change `"FASTMCP_LOG_LEVEL": "ERROR"` to `"DEBUG"` in `mcp.json`
8. Restart Kiro

### Cross-Compilation Errors

**Error:** "aarch64-linux-gnu-gcc: command not found"
```bash
# Ubuntu/Debian
sudo apt-get install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

# macOS
brew install aarch64-elf-gcc
```

### Platform Detection Issues

**Error:** "Unable to determine source SoC characteristics"
1. Explicitly specify source and target SoCs
2. Provide platform documentation or datasheets
3. Use architecture analysis tools to identify current platform

### HAL Layer Conflicts

**Error:** "Conflicting HAL implementations detected"
1. Review platform abstraction layer design
2. Ensure single HAL interface with multiple implementations
3. Use conditional compilation for platform-specific code

## Best Practices

- **Start with Discovery**: Always analyze existing code before making changes
- **Incremental Migration**: Migrate one subsystem at a time
- **Maintain Compatibility**: Keep source platform working during migration
- **Document Decisions**: Record all platform-specific choices and rationales
- **Test Thoroughly**: Validate both functional and performance requirements
- **Use HAL Layers**: Abstract all hardware-specific operations
- **Version Control**: Use feature branches for migration work

## Working Without MCP Server (Fallback Mode)

If you're unable to get the Arm MCP Server working, you can still use this power with reduced functionality:

1. **Manual SoC Specification:** Provide architecture details directly
2. **Manual Code Review:** Ask for platform-specific dependency analysis
3. **Architecture Documentation:** Provide links to SoC datasheets for manual analysis

**Available without MCP:**
- Migration Planning, Implementation Guidance, Best Practices

**Requires MCP:**
- Automated Analysis, Performance Profiling, Architecture Comparison

## Configuration

### Automatic Configuration (Recommended)

No additional configuration required — works after MCP server is installed in Kiro.

### Manual Configuration (Advanced Users)

**Environment Variables:**
- `FASTMCP_LOG_LEVEL`: Set to "ERROR" to reduce MCP server logging (optional)
- `ARM_MCP_CACHE_DIR`: Custom cache directory (default: ~/.cache/arm-mcp)
- `ARM_MCP_TIMEOUT`: Server timeout in seconds (default: 30)

**MCP Server Customization:**
Advanced users can modify `mcp.json` to enable additional tools, adjust auto-approval settings, or modify environment variables.

---
**MCP Server:** arm-mcp-server
**Package:** `arm-mcp-server`
**License**: Apache-2.0
**Support contact**: mcpserver@arm.com
