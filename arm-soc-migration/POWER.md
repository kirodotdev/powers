---
name: "arm-soc-migration"
displayName: "Perform Migration between Arm SoC"
description: "Guides migration of code from one Arm SoC to another, with architecture-aware analysis and safe migration practices."
keywords: ["arm", "soc", "migration", "embedded", "cortex", "neon", "sve", "hal", "platform", "cross-compile"]
author: "ARM"
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
git clone https://github.com/arm/arm-mcp.git
cd arm-mcp

# Build for your platform
docker build -f mcp-local/Dockerfile -t arm-mcp:custom mcp-local

# Update mcp.json to use your custom image
# Change "armlimited/arm-mcp:latest" to "arm-mcp:custom"
```

#### Verifying Installation

After installation, verify the MCP server is working:

**Step 1: Check Docker Image**

Verify the Docker image is available:
```bash
# Check if image is pulled
docker images | grep arm-mcp

# Expected output:
# armlimited/arm-mcp   latest   <image-id>   <size>
```

**Step 2: Test Docker Container**

Test the container runs correctly:
```bash
# Test container startup
docker run --rm armlimited/arm-mcp:latest --version

# If successful, you should see version information
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

This should return Arm documentation if the server is working correctly.

**Troubleshooting Docker Issues:**

If the MCP server fails to connect:

1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Check Docker permissions:**
   ```bash
   # Linux: Add user to docker group
   sudo usermod -aG docker $USER
   # Then log out and back in
   ```

3. **Manually test the container:**
   ```bash
   docker run --rm -i armlimited/arm-mcp:latest
   # Should start without errors
   ```

4. **Check logs in Kiro:**
   - Open MCP Servers panel
   - Click on "arm-mcp-server"
   - View logs for error messages

5. **Enable debug logging:**
   - Edit `mcp.json`
   - Change `"FASTMCP_LOG_LEVEL": "ERROR"` to `"FASTMCP_LOG_LEVEL": "DEBUG"`
   - Restart MCP server

**Step 3: Verify Cross-Compilation Tools (Optional)**

For local compilation testing:
```bash
# Check if cross-compilation tools are available
aarch64-linux-gnu-gcc --version
arm-linux-gnueabihf-gcc --version

# Verify build tools
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

# Verify installation
aarch64-linux-gnu-gcc --version
```

### Initial Setup

**Step 1: Verify MCP Server Connection**

After installing this power, verify the Arm MCP Server is working:

1. **Check MCP Server Status:**
   - Open Kiro's MCP Server panel (View → MCP Servers)
   - Look for "arm-mcp-server" with green status
   - If red/disconnected, click "Reconnect" or restart Kiro

2. **Test MCP Server (Optional):**
   ```
   "Search Arm knowledge base for BCM2711 architecture information"
   ```
   This should return Arm documentation if the server is working.

**Step 2: Specify Migration Context**

Tell Kiro your source and target SoCs:
```
"I need to migrate from BCM2711 (Raspberry Pi 4) to BCM2712 (Raspberry Pi 5)"
```

**Step 3: Project Structure**

Ensure your project follows recommended structure:
```
project/
├── src/           # Application code
├── include/       # Headers
├── platform/      # Platform-specific code
├── hal/           # Hardware abstraction layer
└── CMakeLists.txt # Build configuration
```

**Step 4: Complete Onboarding Example**

Let's walk through a complete onboarding example for migrating from Raspberry Pi 4 to Raspberry Pi 5:

**Example Migration Context:**
```
"I need to migrate my embedded sensor monitoring application from BCM2711 (Raspberry Pi 4) to BCM2712 (Raspberry Pi 5). The application uses GPIO for LEDs, SPI for temperature sensors, and has real-time requirements."
```

**First Analysis Command:**
```
"Analyze my project structure for ARM SoC migration readiness and identify BCM2711-specific code"
```

**Expected Response:**
Kiro will analyze your codebase and identify:
- Platform-specific GPIO pin definitions
- SPI bus configurations
- Memory-mapped I/O access
- Architecture-specific optimizations
- HAL layer completeness

**Sample Project Structure Analysis:**
```
✅ Good: HAL abstraction layer exists
⚠️  Warning: GPIO pins hard-coded in main.c
❌ Issue: Direct BCM2711 register access in spi_driver.c
✅ Good: CMake build system supports cross-compilation
⚠️  Warning: No platform-specific configuration files
```

## Common Workflows

### Workflow 1: Discovery and Analysis

**Goal:** Identify platform-specific code and architecture differences

**Complete Example: BCM2711 → BCM2712 Migration**

**Step 1: Scan Codebase for Platform Dependencies**
```
"Scan my codebase for BCM2711-specific code that needs migration to BCM2712. Focus on GPIO, SPI, and memory-mapped I/O."
```

**Example Analysis Results:**
```
Platform-Specific Code Found:

📁 src/gpio_driver.c:
  - Line 15: #define GPIO_BASE 0x7E200000  // BCM2711 specific
  - Line 23: Direct register access via *(gpio_base + offset)
  - Line 45: BCM2711 pull-up/down register sequence

📁 include/config.h:
  - Line 8: #define SPI0_BASE 0x7E204000   // BCM2711 specific
  - Line 12: GPIO pin assignments (BCM numbering)

📁 platform/bcm2711/spi.c:
  - Line 30: Clock divider calculations for BCM2711
  - Line 67: Interrupt handling for BCM2711 SPI controller

Recommendations:
✅ Move GPIO_BASE to platform-specific header
✅ Abstract register access through HAL functions
✅ Create BCM2712 platform directory
```

**Step 2: Analyze Architecture Differences**
```
"Compare BCM2711 and BCM2712 architecture capabilities, focusing on CPU cores, SIMD, and peripheral differences"
```

**Example Architecture Comparison:**
```
Architecture Analysis: BCM2711 vs BCM2712

CPU Cores:
  BCM2711: 4x Cortex-A72 @ 1.5GHz (ARMv8-A)
  BCM2712: 4x Cortex-A76 @ 2.4GHz (ARMv8.2-A)
  Impact: ~40% performance improvement, new instructions available

SIMD Capabilities:
  BCM2711: NEON (128-bit vectors)
  BCM2712: NEON + additional ARMv8.2 SIMD instructions
  Impact: Potential for better vectorization

Memory:
  BCM2711: LPDDR4-3200, 35GB/s bandwidth
  BCM2712: LPDDR4X-4267, 67GB/s bandwidth
  Impact: Significantly improved memory performance

Peripherals:
  BCM2711: Legacy GPIO controller
  BCM2712: New RP1 I/O controller (PCIe-connected)
  Impact: Major change - GPIO/SPI/I2C access methods different
```

**Step 3: Identify HAL Requirements**
```
"What HAL changes are needed for BCM2712 migration? Focus on the new RP1 I/O controller."
```

**Example HAL Analysis:**
```
HAL Layer Requirements:

Current HAL Status:
❌ No abstraction for GPIO register access
❌ SPI driver directly accesses BCM2711 registers
✅ UART already abstracted through HAL

Required Changes:

1. GPIO HAL Enhancement:
   - Abstract RP1 I/O controller access
   - Maintain BCM2711 compatibility
   - Add pin multiplexing support

2. SPI HAL Creation:
   - Create common SPI interface
   - BCM2711 implementation (existing)
   - BCM2712/RP1 implementation (new)

3. Build System Updates:
   - Platform selection mechanism
   - Conditional compilation support
   - Cross-compilation targets
```

### Workflow 2: Migration Planning

**Goal:** Create detailed migration strategy and timeline

**Complete Example: Sensor Monitoring Application Migration**

**Step 1: Generate Migration Plan**
```
"Create a detailed migration plan from BCM2711 to BCM2712 for my sensor monitoring application. Include timeline, phases, and risk mitigation."
```

**Example Migration Plan:**
```
BCM2711 → BCM2712 Migration Plan
Application: Sensor Monitoring System

Phase 1: Foundation (Week 1-2)
├── Set up BCM2712 development environment
├── Create platform abstraction layer structure
├── Implement basic GPIO HAL for both platforms
└── Milestone: Dual-platform build system working

Phase 2: Core Migration (Week 3-4)
├── Migrate SPI driver to HAL abstraction
├── Update sensor communication layer
├── Implement RP1 I/O controller support
└── Milestone: Basic sensor reading works on both platforms

Phase 3: Optimization (Week 5-6)
├── Leverage Cortex-A76 performance improvements
├── Optimize memory access patterns
├── Update real-time scheduling for new CPU
└── Milestone: Performance targets met on BCM2712

Phase 4: Validation (Week 7-8)
├── Comprehensive testing on both platforms
├── Performance benchmarking
├── Long-term stability testing
└── Milestone: Production-ready dual-platform support

Risk Mitigation:
- Maintain BCM2711 compatibility throughout
- Feature flags for platform-specific optimizations
- Rollback plan if critical issues discovered
```

**Step 2: Risk Assessment**
```
"What are the specific risks and compatibility issues for migrating my sensor monitoring application from BCM2711 to BCM2712?"
```

**Example Risk Assessment:**
```
Migration Risk Analysis:

HIGH RISK:
🔴 RP1 I/O Controller Changes
   Risk: GPIO/SPI access completely different on BCM2712
   Impact: Core functionality broken
   Mitigation: Comprehensive HAL abstraction, extensive testing

🔴 Real-time Timing Changes
   Risk: Cortex-A76 timing differs from Cortex-A72
   Impact: Sensor sampling rates affected
   Mitigation: Timing validation, adjustable parameters

MEDIUM RISK:
🟡 Memory Layout Differences
   Risk: Different memory mapping on BCM2712
   Impact: Direct memory access fails
   Mitigation: Use proper memory mapping APIs

🟡 Interrupt Handling Changes
   Risk: RP1 interrupt routing different
   Impact: Sensor interrupt handling broken
   Mitigation: Abstract interrupt handling in HAL

LOW RISK:
🟢 Application Logic
   Risk: Core sensor processing unchanged
   Impact: Minimal
   Mitigation: Standard testing procedures

🟢 Build System
   Risk: CMake already supports cross-compilation
   Impact: Minor configuration changes
   Mitigation: Platform-specific build targets
```

**Step 3: Performance Impact Analysis**
```
"Analyze performance implications of migrating from Cortex-A72 to Cortex-A76. Focus on sensor processing and real-time requirements."
```

**Example Performance Analysis:**
```
Performance Impact Analysis: Cortex-A72 → Cortex-A76

CPU Performance:
  Single-thread: +35-40% improvement
  Multi-thread: +30-35% improvement
  Impact: Sensor processing can handle higher sample rates

Memory Performance:
  Bandwidth: +91% improvement (35GB/s → 67GB/s)
  Latency: ~15% improvement
  Impact: Faster data logging, reduced buffer requirements

Real-time Characteristics:
  Cache: Larger L2 cache (1MB → 2MB)
  Predictability: Similar interrupt latency
  Impact: More consistent real-time performance

Sensor Processing Improvements:
  Current: 1000 samples/sec maximum
  BCM2712: 1400+ samples/sec possible
  Headroom: 40% performance margin for future features

Power Consumption:
  Idle: Similar power draw
  Active: 10-15% higher due to higher performance
  Impact: May need thermal management updates

Optimization Opportunities:
  - SIMD improvements for sensor data processing
  - Better memory access patterns
  - Reduced CPU utilization for same workload
```

### Workflow 3: Implementation Guidance

**Goal:** Execute migration with proper platform abstraction

**Complete Example: GPIO and SPI HAL Implementation**

**Step 1: Refactor Platform-Specific Code**
```
"Help me refactor my GPIO access code for BCM2712 compatibility. Here's my current BCM2711-specific GPIO driver that needs abstraction."
```

**Example Code Refactoring:**

**Before (BCM2711-specific):**
```c
// gpio_driver.c - BCM2711 specific
#define GPIO_BASE 0x7E200000
#define GPFSEL0   (GPIO_BASE + 0x00)
#define GPSET0    (GPIO_BASE + 0x1C)
#define GPCLR0    (GPIO_BASE + 0x28)

void gpio_set_output(int pin) {
    volatile uint32_t *gpfsel = (uint32_t*)GPFSEL0;
    int reg = pin / 10;
    int shift = (pin % 10) * 3;
    gpfsel[reg] &= ~(7 << shift);
    gpfsel[reg] |= (1 << shift);
}
```

**After (HAL abstracted):**
```c
// hal/gpio.h - Platform abstraction
typedef struct {
    int (*init)(void);
    int (*set_mode)(uint8_t pin, gpio_mode_t mode);
    int (*write)(uint8_t pin, uint8_t value);
    int (*read)(uint8_t pin);
    void (*cleanup)(void);
} gpio_hal_t;

// platform/bcm2711/gpio_bcm2711.c
static int bcm2711_gpio_set_mode(uint8_t pin, gpio_mode_t mode) {
    volatile uint32_t *gpfsel = (uint32_t*)BCM2711_GPIO_BASE;
    // BCM2711-specific implementation
}

// platform/bcm2712/gpio_bcm2712.c  
static int bcm2712_gpio_set_mode(uint8_t pin, gpio_mode_t mode) {
    // RP1 I/O controller implementation
    return rp1_gpio_configure(pin, mode);
}

// Platform selection
extern const gpio_hal_t gpio_hal;
```

**Step 2: Update Build Configuration**
```
"Update my CMakeLists.txt for dual BCM2711/BCM2712 support with proper platform selection and cross-compilation."
```

**Example CMake Configuration:**
```cmake
# CMakeLists.txt - Enhanced for dual platform support
cmake_minimum_required(VERSION 3.16)
project(sensor_monitor)

# Platform selection
set(TARGET_SOC "BCM2711" CACHE STRING "Target SoC (BCM2711 or BCM2712)")
set_property(CACHE TARGET_SOC PROPERTY STRINGS "BCM2711" "BCM2712")

# Cross-compilation setup
if(TARGET_SOC STREQUAL "BCM2711")
    set(CMAKE_SYSTEM_NAME Linux)
    set(CMAKE_SYSTEM_PROCESSOR aarch64)
    set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
    set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)
    add_definitions(-DTARGET_BCM2711)
elseif(TARGET_SOC STREQUAL "BCM2712")
    set(CMAKE_SYSTEM_NAME Linux)
    set(CMAKE_SYSTEM_PROCESSOR aarch64)
    set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
    set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)
    add_definitions(-DTARGET_BCM2712)
endif()

# Common source files
set(COMMON_SOURCES
    src/main.c
    src/sensor.c
    src/application.c
)

# HAL interface
set(HAL_SOURCES
    hal/gpio.c
    hal/spi.c
)

# Platform-specific sources
if(TARGET_SOC STREQUAL "BCM2711")
    set(PLATFORM_SOURCES
        platform/bcm2711/gpio_bcm2711.c
        platform/bcm2711/spi_bcm2711.c
        platform/bcm2711/platform_init.c
    )
    set(PLATFORM_INCLUDE platform/bcm2711/include)
elseif(TARGET_SOC STREQUAL "BCM2712")
    set(PLATFORM_SOURCES
        platform/bcm2712/gpio_bcm2712.c
        platform/bcm2712/spi_bcm2712.c
        platform/bcm2712/rp1_driver.c
        platform/bcm2712/platform_init.c
    )
    set(PLATFORM_INCLUDE platform/bcm2712/include)
endif()

# Create executable
add_executable(sensor_monitor
    ${COMMON_SOURCES}
    ${HAL_SOURCES}
    ${PLATFORM_SOURCES}
)

target_include_directories(sensor_monitor PRIVATE
    include
    hal/include
    ${PLATFORM_INCLUDE}
)

# Build commands for both platforms
add_custom_target(build-bcm2711
    COMMAND ${CMAKE_COMMAND} -DTARGET_SOC=BCM2711 -B build-bcm2711 -S .
    COMMAND ${CMAKE_COMMAND} --build build-bcm2711
    COMMENT "Building for BCM2711"
)

add_custom_target(build-bcm2712
    COMMAND ${CMAKE_COMMAND} -DTARGET_SOC=BCM2712 -B build-bcm2712 -S .
    COMMAND ${CMAKE_COMMAND} --build build-bcm2712
    COMMENT "Building for BCM2712"
)
```

**Step 3: Implement HAL Abstraction**
```
"Create a complete HAL layer for SPI peripheral differences between BCM2711 and BCM2712. Include the RP1 I/O controller support."
```

**Example SPI HAL Implementation:**
```c
// hal/include/spi_hal.h - SPI HAL Interface
typedef struct {
    int (*init)(uint8_t bus, uint32_t speed_hz);
    int (*transfer)(const uint8_t *tx_buf, uint8_t *rx_buf, size_t len);
    int (*write)(const uint8_t *buf, size_t len);
    int (*read)(uint8_t *buf, size_t len);
    void (*cleanup)(void);
} spi_hal_t;

extern const spi_hal_t *spi_hal;

// platform/bcm2711/spi_bcm2711.c - BCM2711 Implementation
#define BCM2711_SPI0_BASE 0x7E204000

static int bcm2711_spi_init(uint8_t bus, uint32_t speed_hz) {
    volatile uint32_t *spi_base = (uint32_t*)BCM2711_SPI0_BASE;
    
    // Configure BCM2711 SPI controller
    uint32_t divider = 250000000 / speed_hz;  // Core clock / desired speed
    spi_base[SPI_CLK] = divider;
    spi_base[SPI_CS] = SPI_CS_CLEAR;
    
    return 0;
}

static int bcm2711_spi_transfer(const uint8_t *tx_buf, uint8_t *rx_buf, size_t len) {
    volatile uint32_t *spi_base = (uint32_t*)BCM2711_SPI0_BASE;
    
    for (size_t i = 0; i < len; i++) {
        // Wait for TX ready
        while (!(spi_base[SPI_CS] & SPI_CS_TXD));
        spi_base[SPI_FIFO] = tx_buf ? tx_buf[i] : 0;
        
        // Wait for RX ready
        while (!(spi_base[SPI_CS] & SPI_CS_RXD));
        if (rx_buf) rx_buf[i] = spi_base[SPI_FIFO];
    }
    
    return 0;
}

const spi_hal_t bcm2711_spi_hal = {
    .init = bcm2711_spi_init,
    .transfer = bcm2711_spi_transfer,
    .write = bcm2711_spi_write,
    .read = bcm2711_spi_read,
    .cleanup = bcm2711_spi_cleanup
};

// platform/bcm2712/spi_bcm2712.c - BCM2712/RP1 Implementation
#include "rp1_driver.h"

static int bcm2712_spi_init(uint8_t bus, uint32_t speed_hz) {
    // Initialize RP1 I/O controller
    if (rp1_init() != 0) return -1;
    
    // Configure SPI through RP1
    rp1_spi_config_t config = {
        .bus = bus,
        .speed_hz = speed_hz,
        .mode = SPI_MODE_0,
        .bits_per_word = 8
    };
    
    return rp1_spi_configure(&config);
}

static int bcm2712_spi_transfer(const uint8_t *tx_buf, uint8_t *rx_buf, size_t len) {
    // Use RP1 SPI transfer function
    return rp1_spi_transfer(tx_buf, rx_buf, len);
}

const spi_hal_t bcm2712_spi_hal = {
    .init = bcm2712_spi_init,
    .transfer = bcm2712_spi_transfer,
    .write = bcm2712_spi_write,
    .read = bcm2712_spi_read,
    .cleanup = bcm2712_spi_cleanup
};

// Platform selection in hal/spi.c
#ifdef TARGET_BCM2711
const spi_hal_t *spi_hal = &bcm2711_spi_hal;
#elif defined(TARGET_BCM2712)
const spi_hal_t *spi_hal = &bcm2712_spi_hal;
#else
#error "No target platform defined"
#endif
```

### Workflow 4: Validation and Testing

**Goal:** Verify migration correctness and performance

**Complete Example: Comprehensive Validation Process**

**Step 1: Cross-Compilation Verification**
```
"Help me set up comprehensive cross-compilation testing for both BCM2711 and BCM2712 platforms."
```

**Example Build and Test Script:**
```bash
#!/bin/bash
# validate_migration.sh - Comprehensive build validation

set -e  # Exit on any error

echo "=== ARM SoC Migration Validation ==="

# Clean previous builds
rm -rf build-bcm2711 build-bcm2712

# Build for BCM2711
echo "Building for BCM2711..."
cmake -DTARGET_SOC=BCM2711 -B build-bcm2711 -S .
cmake --build build-bcm2711 --parallel 4

# Build for BCM2712  
echo "Building for BCM2712..."
cmake -DTARGET_SOC=BCM2712 -B build-bcm2712 -S .
cmake --build build-bcm2712 --parallel 4

# Verify binaries
echo "Verifying binary architectures..."
file build-bcm2711/sensor_monitor
file build-bcm2712/sensor_monitor

# Check for platform-specific symbols
echo "Checking platform-specific symbols..."
nm build-bcm2711/sensor_monitor | grep -E "(bcm2711|rp1)" || echo "✅ No platform leakage in BCM2711 build"
nm build-bcm2712/sensor_monitor | grep -E "(bcm2711|rp1)" || echo "✅ Clean BCM2712 build"

# Size comparison
echo "Binary size comparison:"
ls -lh build-bcm2711/sensor_monitor build-bcm2712/sensor_monitor

echo "✅ Cross-compilation validation complete"
```

**Step 2: Performance Comparison**
```
"Create a comprehensive performance benchmark comparing BCM2711 and BCM2712 builds. Focus on sensor processing throughput and real-time characteristics."
```

**Example Performance Benchmark:**
```c
// benchmark.c - Performance validation
#include <time.h>
#include <stdio.h>
#include "sensor.h"
#include "hal/gpio.h"

typedef struct {
    double sensor_read_time_us;
    double processing_time_us;
    double total_cycle_time_us;
    int samples_per_second;
    double cpu_utilization;
} benchmark_results_t;

benchmark_results_t run_performance_benchmark(int duration_seconds) {
    benchmark_results_t results = {0};
    struct timespec start, end, cycle_start, cycle_end;
    int sample_count = 0;
    
    printf("Running %d second performance benchmark...\n", duration_seconds);
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    while (1) {
        clock_gettime(CLOCK_MONOTONIC, &cycle_start);
        
        // Sensor reading benchmark
        struct timespec read_start, read_end;
        clock_gettime(CLOCK_MONOTONIC, &read_start);
        float temperature = sensor_read_temperature();
        clock_gettime(CLOCK_MONOTONIC, &read_end);
        
        // Processing benchmark
        struct timespec proc_start, proc_end;
        clock_gettime(CLOCK_MONOTONIC, &proc_start);
        process_sensor_data(temperature);
        clock_gettime(CLOCK_MONOTONIC, &proc_end);
        
        clock_gettime(CLOCK_MONOTONIC, &cycle_end);
        
        // Accumulate timing data
        double read_time = (read_end.tv_sec - read_start.tv_sec) * 1e6 + 
                          (read_end.tv_nsec - read_start.tv_nsec) / 1e3;
        double proc_time = (proc_end.tv_sec - proc_start.tv_sec) * 1e6 + 
                          (proc_end.tv_nsec - proc_start.tv_nsec) / 1e3;
        double cycle_time = (cycle_end.tv_sec - cycle_start.tv_sec) * 1e6 + 
                           (cycle_end.tv_nsec - cycle_start.tv_nsec) / 1e3;
        
        results.sensor_read_time_us += read_time;
        results.processing_time_us += proc_time;
        results.total_cycle_time_us += cycle_time;
        sample_count++;
        
        // Check if benchmark duration elapsed
        clock_gettime(CLOCK_MONOTONIC, &end);
        if ((end.tv_sec - start.tv_sec) >= duration_seconds) break;
        
        usleep(1000);  // 1ms delay for 1kHz sampling
    }
    
    // Calculate averages
    results.sensor_read_time_us /= sample_count;
    results.processing_time_us /= sample_count;
    results.total_cycle_time_us /= sample_count;
    results.samples_per_second = sample_count / duration_seconds;
    results.cpu_utilization = (results.processing_time_us / 1000.0) * 100.0;
    
    return results;
}

// Example benchmark results comparison
void compare_platform_performance(void) {
    printf("=== Platform Performance Comparison ===\n");
    
    benchmark_results_t results = run_performance_benchmark(10);
    
    printf("Platform: %s\n", PLATFORM_NAME);
    printf("Sensor Read Time: %.2f μs\n", results.sensor_read_time_us);
    printf("Processing Time: %.2f μs\n", results.processing_time_us);
    printf("Total Cycle Time: %.2f μs\n", results.total_cycle_time_us);
    printf("Samples/Second: %d\n", results.samples_per_second);
    printf("CPU Utilization: %.1f%%\n", results.cpu_utilization);
    
    // Expected performance improvements on BCM2712
    #ifdef TARGET_BCM2712
    printf("\nBCM2712 Performance Expectations:\n");
    printf("✅ 30-40%% faster processing expected\n");
    printf("✅ Higher sample rates possible\n");
    printf("✅ Lower CPU utilization for same workload\n");
    #endif
}
```

**Step 3: Functional Testing**
```
"Create comprehensive functional tests to validate that migrated code maintains identical behavior on both BCM2711 and BCM2712 platforms."
```

**Example Functional Test Suite:**
```c
// functional_tests.c - Platform behavior validation
#include <assert.h>
#include <stdio.h>
#include <math.h>
#include "sensor.h"
#include "hal/gpio.h"
#include "hal/spi.h"

typedef struct {
    const char *test_name;
    int (*test_func)(void);
    int passed;
} test_case_t;

// GPIO functionality test
int test_gpio_functionality(void) {
    printf("Testing GPIO functionality...\n");
    
    // Test GPIO initialization
    if (gpio_init() != 0) return 0;
    
    // Test pin configuration
    if (gpio_set_mode(LED_STATUS_PIN, GPIO_MODE_OUTPUT) != 0) return 0;
    if (gpio_set_mode(BUTTON_PIN, GPIO_MODE_INPUT) != 0) return 0;
    
    // Test GPIO write/read
    gpio_write(LED_STATUS_PIN, GPIO_HIGH);
    usleep(1000);
    gpio_write(LED_STATUS_PIN, GPIO_LOW);
    
    // Test should pass on both platforms
    gpio_cleanup();
    return 1;
}

// SPI communication test
int test_spi_communication(void) {
    printf("Testing SPI communication...\n");
    
    if (spi_init(SPI_BUS_0, 1000000) != 0) return 0;
    
    // Test SPI loopback (if available)
    uint8_t tx_data[] = {0xAA, 0x55, 0xFF, 0x00};
    uint8_t rx_data[4] = {0};
    
    if (spi_transfer(tx_data, rx_data, 4) != 0) {
        spi_cleanup();
        return 0;
    }
    
    // Verify data integrity (platform-independent)
    printf("SPI Test - TX: %02X %02X %02X %02X\n", 
           tx_data[0], tx_data[1], tx_data[2], tx_data[3]);
    printf("SPI Test - RX: %02X %02X %02X %02X\n", 
           rx_data[0], rx_data[1], rx_data[2], rx_data[3]);
    
    spi_cleanup();
    return 1;
}

// Sensor reading consistency test
int test_sensor_consistency(void) {
    printf("Testing sensor reading consistency...\n");
    
    if (sensor_init() != 0) return 0;
    
    // Take multiple readings
    float readings[10];
    for (int i = 0; i < 10; i++) {
        readings[i] = sensor_read_temperature();
        usleep(100000);  // 100ms between readings
    }
    
    // Check for reasonable consistency (platform-independent behavior)
    float min_temp = readings[0], max_temp = readings[0];
    for (int i = 1; i < 10; i++) {
        if (readings[i] < min_temp) min_temp = readings[i];
        if (readings[i] > max_temp) max_temp = readings[i];
    }
    
    float temp_range = max_temp - min_temp;
    printf("Temperature range: %.2f°C (%.2f - %.2f)\n", temp_range, min_temp, max_temp);
    
    // Should be stable within 2°C on both platforms
    sensor_cleanup();
    return (temp_range < 2.0) ? 1 : 0;
}

// Timing consistency test
int test_timing_consistency(void) {
    printf("Testing timing consistency...\n");
    
    struct timespec start, end;
    double times[100];
    
    // Measure sensor read timing consistency
    for (int i = 0; i < 100; i++) {
        clock_gettime(CLOCK_MONOTONIC, &start);
        sensor_read_temperature();
        clock_gettime(CLOCK_MONOTONIC, &end);
        
        times[i] = (end.tv_sec - start.tv_sec) * 1e6 + 
                   (end.tv_nsec - start.tv_nsec) / 1e3;
    }
    
    // Calculate timing statistics
    double sum = 0, mean, variance = 0;
    for (int i = 0; i < 100; i++) sum += times[i];
    mean = sum / 100.0;
    
    for (int i = 0; i < 100; i++) {
        variance += (times[i] - mean) * (times[i] - mean);
    }
    variance /= 100.0;
    double std_dev = sqrt(variance);
    
    printf("Timing - Mean: %.2f μs, Std Dev: %.2f μs\n", mean, std_dev);
    
    // Timing should be consistent (low standard deviation)
    return (std_dev < (mean * 0.1)) ? 1 : 0;  // <10% variation
}

// Main test runner
int run_functional_tests(void) {
    test_case_t tests[] = {
        {"GPIO Functionality", test_gpio_functionality, 0},
        {"SPI Communication", test_spi_communication, 0},
        {"Sensor Consistency", test_sensor_consistency, 0},
        {"Timing Consistency", test_timing_consistency, 0}
    };
    
    int num_tests = sizeof(tests) / sizeof(tests[0]);
    int passed = 0;
    
    printf("=== Functional Test Suite ===\n");
    printf("Platform: %s\n\n", PLATFORM_NAME);
    
    for (int i = 0; i < num_tests; i++) {
        printf("Running: %s\n", tests[i].test_name);
        tests[i].passed = tests[i].test_func();
        printf("Result: %s\n\n", tests[i].passed ? "PASS" : "FAIL");
        if (tests[i].passed) passed++;
    }
    
    printf("=== Test Results ===\n");
    printf("Passed: %d/%d tests\n", passed, num_tests);
    
    if (passed == num_tests) {
        printf("✅ All functional tests passed - migration successful!\n");
        return 0;
    } else {
        printf("❌ Some tests failed - review migration implementation\n");
        return 1;
    }
}
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
**Symptoms:**
- Error: "Connection refused" or "Server not responding"
- Red status in Kiro MCP Server panel
- Tools not available when using the power

**Solutions:**

**Step 1: Verify Docker is Running**
```bash
# Check Docker status
docker ps

# Test Docker functionality
docker run --rm hello-world
```

**Step 2: Manual MCP Server Test**
```bash
# Test the Arm MCP container directly
docker run --rm armlimited/arm-mcp:latest --version

# This should show version information if working correctly
```

**Step 3: Check Kiro MCP Configuration**
1. Open Kiro → View → MCP Servers
2. Find "arm-mcp-server" in the list
3. Check status (should be green/connected)
4. If red, click "Reconnect" button
5. If still failing, click "Restart" button

**Step 4: Pull Latest Image**
```bash
# Force pull the latest Docker image
docker pull armlimited/arm-mcp:latest

# Remove old containers
docker container prune -f
```

**Step 5: Restart Kiro**
- Close Kiro completely
- Restart Kiro
- Check MCP Server panel again

**Step 6: Check Logs**
- In Kiro MCP Server panel, click on "arm-mcp-server"
- Review error logs for specific issues
- Common issues: Docker permissions, network connectivity, image pull failures

### Cross-Compilation Errors

**Error:** "aarch64-linux-gnu-gcc: command not found"
**Cause:** Missing cross-compilation toolchain
**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

# macOS
brew install aarch64-elf-gcc

# Verify installation
aarch64-linux-gnu-gcc --version
```

### Platform Detection Issues

**Error:** "Unable to determine source SoC characteristics"
**Cause:** Insufficient platform information provided
**Solution:**
1. Explicitly specify source and target SoCs
2. Provide platform documentation or datasheets
3. Use architecture analysis tools to identify current platform

### HAL Layer Conflicts

**Error:** "Conflicting HAL implementations detected"
**Cause:** Multiple platform-specific implementations without proper abstraction
**Solution:**
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

### Manual Architecture Analysis

**Instead of automated analysis, you can:**

1. **Manual SoC Specification:**
   ```
   "I'm migrating from BCM2711 (Cortex-A72, ARMv8-A, quad-core) to BCM2712 (Cortex-A76, ARMv8.2-A, quad-core)"
   ```

2. **Manual Code Review:**
   ```
   "Review my GPIO and SPI code for platform-specific dependencies that need abstraction"
   ```

3. **Architecture Documentation:**
   Provide links to your SoC datasheets and technical reference manuals for manual analysis.

### Limited Workflows Available

- ✅ **Migration Planning** - Strategy and approach guidance
- ✅ **Implementation Guidance** - Code refactoring and HAL design
- ✅ **Best Practices** - Safe migration principles
- ❌ **Automated Analysis** - Requires MCP server
- ❌ **Performance Profiling** - Requires MCP server
- ❌ **Architecture Comparison** - Requires MCP server

### Getting Help

If MCP server issues persist:
1. **Check Kiro Documentation:** https://kiro.dev/docs/mcp/
2. **Community Support:** Kiro Discord or GitHub issues
3. **Manual Migration:** Use this power's guidance with manual analysis

## Configuration

### Automatic Configuration (Recommended)

**No additional configuration required** - works after MCP server is installed in Kiro.

### Manual Configuration (Advanced Users)

**Environment Variables:**
- `FASTMCP_LOG_LEVEL`: Set to "ERROR" to reduce MCP server logging (optional)
- `ARM_MCP_CACHE_DIR`: Custom cache directory (default: ~/.cache/arm-mcp)
- `ARM_MCP_TIMEOUT`: Server timeout in seconds (default: 30)

**Cross-Compilation Setup:**
Ensure appropriate toolchains are installed for your source and target architectures.

**MCP Server Customization:**
Advanced users can modify `mcp.json` to:
- Enable additional tools (remove from `disabledTools`)
- Adjust auto-approval settings
- Modify environment variables

---
**MCP Server:** arm-mcp-server
**Package:** `arm-mcp-server`
**License**: Apache-2.0
**Support contact**: mcpserver@arm.com