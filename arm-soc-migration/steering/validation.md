# Workflow 4: Validation and Testing

**Goal:** Verify migration correctness and performance across both source and target platforms.

## Complete Example: Comprehensive Validation Process

### Step 1: Cross-Compilation Verification

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

### Step 2: Performance Comparison

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

### Step 3: Functional Testing

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
