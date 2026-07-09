# Migration Constraints

These constraints apply to all Arm SoC-to-SoC migrations regardless of source or target platform.

## Initial Requirements

- Before any migration work begins, the developer MUST specify:
  - The source Arm SoC (current platform)
  - The target Arm SoC (destination platform)
- If this information is not provided, prompt the developer to supply it before proceeding.

## Functional Behavior

- The migration must not change externally visible functional behavior unless
  explicitly requested. Any change to public APIs, communication protocols, or
  configuration interfaces must be documented and justified.

## Safety Properties

- Safety properties must not be degraded:
  - Do not remove or weaken input validation and range checks.
  - Do not remove diagnostic logging in safety-relevant paths without a documented reason.
  - Do not introduce non-deterministic behavior in previously deterministic control paths.

## Platform Abstraction

- No hard-coding of target SoC specifics into generic modules:
  - Board-specific constants (GPIO pins, bus IDs, device paths, memory maps) must live in platform/HAL layers.
  - Code that is logically platform-independent must remain platform-independent.
  - Create or extend platform abstraction layers for SoC-specific functionality.

## Timing and Performance

- Do not silently relax timing constraints (e.g., control-loop cycle times, interrupt latencies).
- Any known change in timing behavior must be explicitly documented.
- Profile and compare performance characteristics between source and target SoCs.

## Build and Deployment

- Do not remove the ability to build and run on the source platform unless explicitly requested.
- If source platform support is deprecated, document this clearly.
- Maintain build system compatibility for both platforms during transition.

## Safety and Compliance

- Do not introduce undefined behavior, data races, or reliance on unspecified
  compiler or CPU behavior.
- Where applicable standards (MISRA, ISO 26262, AUTOSAR, etc.) are in play, new code must
  not obviously violate them; where compliance is uncertain, state the risk.
- Consider differences in memory models, cache behavior, and atomics between SoCs.

## Hardware I/O

- Direct hardware access must be isolated in the target platform's HAL layer.
- Timing-critical I/O manipulations must be carefully documented.
- Peripheral differences (SPI, I2C, UART, GPIO) must be abstracted appropriately.

## Architecture Considerations

- Identify and document differences in:
  - Arm architecture version (Armv7, Armv8, Armv9)
  - Core type (Cortex-A, Cortex-M, Cortex-R, Neoverse)
  - SIMD capabilities (NEON, SVE, SVE2)
  - Memory hierarchy and cache sizes
  - Endianness and alignment requirements

## Documentation

- Every non-trivial platform-specific change must be reflected in design or migration docs.
- Migration rationales must be understandable by another engineer reviewing the changes.
- Document any feature gaps or limitations of the target SoC compared to the source.
