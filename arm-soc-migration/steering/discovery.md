# Workflow 1: Discovery and Analysis

**Goal:** Identify platform-specific code and architecture differences between source and target Arm SoCs.

## Complete Example: BCM2711 → BCM2712 Migration

### Step 1: Scan Codebase for Platform Dependencies

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

### Step 2: Analyze Architecture Differences

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

### Step 3: Identify HAL Requirements

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
