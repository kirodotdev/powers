# Workflow 3: Implementation Guidance

**Goal:** Execute migration with proper platform abstraction, HAL design, and build system updates.

## Complete Example: GPIO and SPI HAL Implementation

### Step 1: Refactor Platform-Specific Code

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

### Step 2: Update Build Configuration

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

### Step 3: Implement HAL Abstraction

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