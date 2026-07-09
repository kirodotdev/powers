# Codebase Observability Gap Analysis Steering

## Purpose
This steering file provides guidance for analyzing codebases across major programming languages to identify observability gaps and provide actionable recommendations for instrumentation, logging, metrics, and tracing.

## Analysis Framework

### 1. Logging Analysis
Identify gaps in logging coverage:

**What to Check:**
- Error handling blocks without logging
- Critical operations without audit logs
- Missing structured logging (JSON format)
- Inconsistent log levels
- Missing correlation IDs/request IDs
- Sensitive data in logs (PII, credentials)
- Missing context (user, session, transaction)

**Recommendations:**
- Use structured logging libraries (e.g., structlog, logrus, winston)
- Add correlation IDs to all log entries
- Log at appropriate levels (ERROR, WARN, INFO, DEBUG)
- Include contextual metadata (service, version, environment)
- Sanitize sensitive data before logging

**Cost Optimization:**
- Set production log level to INFO or WARN (avoid DEBUG in production)
- Use log sampling for high-throughput operations (e.g., log 1 in 100 requests)
- Configure CloudWatch log retention policies (7-30 days for most use cases)
- Use metric filters instead of logging for high-frequency counters
- Avoid logging in hot paths (tight loops, per-item processing)
- Consider log aggregation before shipping (batch similar events)
- Use EMF (Embedded Metric Format) for Lambda to reduce log volume

### 2. Metrics Collection
Assess metrics instrumentation:

**What to Check:**
- Missing business metrics (orders, signups, conversions)
- No performance metrics (latency, throughput)
- Missing resource utilization metrics
- No error rate tracking
- Missing custom CloudWatch metrics
- No metric dimensions for filtering

**Recommendations:**
- Instrument key business operations
- Track request duration and count
- Monitor error rates by type
- Add custom CloudWatch metrics for business KPIs
- Use metric dimensions (service, endpoint, status)
- Implement metric aggregation for high-volume operations

**Cost Optimization:**
- Limit metric dimensions to avoid cardinality explosion (max 10 dimensions per metric)
- Use metric aggregation at source before publishing to CloudWatch
- Leverage EMF (Embedded Metric Format) for Lambda to reduce API calls
- Set appropriate metric resolution (standard 1-min vs high-res 1-sec)
- Use metric math in dashboards instead of creating derived metrics
- Implement local aggregation for high-frequency metrics (>1000/sec)
- Consider StatsD/DogStatsD for local aggregation before CloudWatch

### 3. Distributed Tracing
Evaluate tracing implementation:

**What to Check:**
- Missing OpenTelemetry SDK integration
- No trace context propagation (W3C Trace Context)
- Missing spans for external calls
- No span attributes for business context
- Missing span events for debugging
- No sampling strategy
- Legacy X-Ray SDK without OTEL migration path

**Recommendations:**
- Use OpenTelemetry (OTEL) for instrumentation (vendor-neutral, industry standard)
- Deploy AWS Distro for OpenTelemetry (ADOT) as the collector
- Enable AWS Application Signals for automatic APM (built on OTEL)
- Propagate trace context across service boundaries (W3C Trace Context)
- Create spans for database, HTTP, and AWS SDK calls
- Add span attributes for searchable context
- Include span events for debugging details
- Implement adaptive sampling for high-volume services
- For existing X-Ray implementations: Plan migration to OTEL with X-Ray exporter

**Application Signals Benefits:**
- Automatic service discovery and dependency mapping
- Pre-built dashboards for service health (latency, errors, availability)
- SLO tracking and error budget monitoring
- Correlation between traces, metrics, and logs
- No code changes required (auto-instrumentation via ADOT)
- Built on OpenTelemetry standards

**Cost Optimization:**
- Implement head-based sampling (sample at trace start, not per-span)
- Use adaptive sampling rules (higher rate for errors, lower for success)
- Configure sampling rates based on traffic volume (1% for high-volume, 100% for low-volume)
- Avoid tracing health check endpoints
- Use tail-based sampling for critical transactions only
- Leverage ADOT collector for local aggregation and filtering

### 4. Error Handling
Review error handling patterns:

**What to Check:**
- Silent failures (empty catch blocks)
- Generic error messages
- Missing error context
- No error categorization
- Missing retry logic
- No circuit breaker patterns

**Recommendations:**
- Log all errors with full context
- Use specific error types/classes
- Include stack traces for debugging
- Categorize errors (transient, permanent, user)
- Implement exponential backoff for retries
- Add circuit breakers for external dependencies

### 5. Health Checks & Readiness
Assess service health endpoints:

**What to Check:**
- Missing health check endpoints
- No readiness probes
- Incomplete dependency checks
- No graceful shutdown handling
- Missing startup probes

**Recommendations:**
- Implement `/health` endpoint
- Add `/ready` endpoint with dependency checks
- Include version and build info
- Implement graceful shutdown
- Add startup probes for slow-starting services

## Language-Specific Patterns

### Python
```python
# GOOD: Structured logging with context
import structlog
logger = structlog.get_logger()

def process_order(order_id, user_id):
    log = logger.bind(order_id=order_id, user_id=user_id)
    try:
        log.info("processing_order_started")
        # ... business logic
        log.info("processing_order_completed", duration_ms=duration)
    except Exception as e:
        log.error("processing_order_failed", error=str(e), exc_info=True)
        raise

# BAD: Unstructured logging, no context
def process_order(order_id, user_id):
    try:
        print("Processing order")
        # ... business logic
    except:
        pass  # Silent failure
```

### Java
```java
// GOOD: Structured logging with MDC
import org.slf4j.Logger;
import org.slf4j.MDC;

public void processOrder(String orderId, String userId) {
    MDC.put("orderId", orderId);
    MDC.put("userId", userId);
    try {
        logger.info("Processing order started");
        // ... business logic
        logger.info("Processing order completed");
    } catch (Exception e) {
        logger.error("Processing order failed", e);
        throw e;
    } finally {
        MDC.clear();
    }
}

// BAD: No context, generic logging
public void processOrder(String orderId, String userId) {
    try {
        System.out.println("Processing");
        // ... business logic
    } catch (Exception e) {
        // Silent failure
    }
}
```

### JavaScript/TypeScript
```javascript
// GOOD: Structured logging with Winston
const winston = require('winston');
const logger = winston.createLogger({
  format: winston.format.json(),
  defaultMeta: { service: 'order-service' }
});

async function processOrder(orderId, userId) {
  const log = logger.child({ orderId, userId });
  try {
    log.info('Processing order started');
    // ... business logic
    log.info('Processing order completed', { duration: duration });
  } catch (error) {
    log.error('Processing order failed', { error: error.message, stack: error.stack });
    throw error;
  }
}

// BAD: Console logging, no structure
async function processOrder(orderId, userId) {
  try {
    console.log('Processing order');
    // ... business logic
  } catch (error) {
    // Silent failure
  }
}
```

### Go
```go
// GOOD: Structured logging with zerolog
import "github.com/rs/zerolog/log"

func processOrder(orderID, userID string) error {
    logger := log.With().
        Str("order_id", orderID).
        Str("user_id", userID).
        Logger()
    
    logger.Info().Msg("Processing order started")
    
    if err := doWork(); err != nil {
        logger.Error().Err(err).Msg("Processing order failed")
        return err
    }
    
    logger.Info().Msg("Processing order completed")
    return nil
}

// BAD: fmt.Println, no structure
func processOrder(orderID, userID string) error {
    fmt.Println("Processing order")
    if err := doWork(); err != nil {
        return err  // No logging
    }
    return nil
}
```

## Analysis Workflow

When analyzing a codebase:

1. **Scan Entry Points**
   - API endpoints/routes
   - Lambda handlers
   - Message queue consumers
   - Scheduled jobs

2. **Identify Critical Paths**
   - Authentication/authorization
   - Payment processing
   - Data mutations
   - External service calls

3. **Check Instrumentation**
   - Logging at entry/exit points
   - Error handling coverage
   - Metrics emission
   - Trace context propagation

4. **Generate Report**
   - List gaps by severity (Critical, High, Medium, Low)
   - Provide code examples for fixes
   - Estimate implementation effort
   - Prioritize recommendations

## Common Observability Gaps

### Critical Gaps
1. **No error logging** - Errors caught but not logged
2. **Missing trace context** - No X-Ray or trace propagation
3. **Silent failures** - Empty catch blocks
4. **No health checks** - Missing /health endpoints
5. **Sensitive data exposure** - PII in logs

### High Priority Gaps
1. **Unstructured logging** - Using print/console.log
2. **Missing correlation IDs** - Can't trace requests
3. **No metrics** - No CloudWatch custom metrics
4. **Generic error messages** - Hard to debug
5. **Missing request/response logging** - No audit trail

### Medium Priority Gaps
1. **Inconsistent log levels** - Everything at INFO
2. **Missing business metrics** - Only technical metrics
3. **No sampling strategy** - Tracing all requests
4. **Missing metadata** - Insufficient debugging context
5. **No log aggregation** - Logs not centralized

### Low Priority Gaps
1. **Verbose logging** - Too much DEBUG output
2. **Missing log rotation** - Disk space issues
3. **No log retention policy** - Compliance risk
4. **Inconsistent naming** - Hard to search logs
5. **Missing documentation** - No runbooks

## Actionable Recommendations Template

For each gap identified, provide:

```markdown
### Gap: [Description]
**Severity:** Critical/High/Medium/Low
**Location:** [File:Line or Pattern]
**Impact:** [What problems this causes]
**Recommendation:** [Specific fix]
**Code Example:**
[Before/After code snippet]
**Effort:** [Hours/Days estimate]
**Priority:** [1-5]
```

## Integration with AWS Observability

After identifying gaps, recommend:

1. **CloudWatch Logs**
   - Configure log groups per service
   - Set retention policies (7-30 days for cost optimization)
   - Enable log insights
   - Use metric filters for high-frequency counters

2. **CloudWatch Metrics**
   - Define custom metrics with limited dimensions
   - Set up dashboards
   - Configure alarms
   - Use EMF for Lambda functions

3. **OpenTelemetry + ADOT + Application Signals**
   - Integrate OpenTelemetry SDK (vendor-neutral)
   - Deploy ADOT Collector for trace aggregation
   - Enable AWS Application Signals for automatic APM
   - Configure sampling rules
   - Export to X-Ray, CloudWatch, or other backends
   - Set up service maps in X-Ray console
   - Use Application Signals dashboards for service health

4. **Application Signals (APM Layer)**
   - Enable for automatic service discovery
   - Define SLOs and track error budgets
   - Monitor service health (latency P50/P90/P99, error rates)
   - Correlate traces with metrics and logs
   - Use pre-built dashboards for common patterns

## Best Practices Checklist

- [ ] Structured logging with JSON format
- [ ] Correlation IDs in all logs
- [ ] Error logging with stack traces
- [ ] Metrics for key operations
- [ ] Distributed tracing with X-Ray
- [ ] Health check endpoints
- [ ] Graceful error handling
- [ ] No sensitive data in logs
- [ ] Log levels used appropriately
- [ ] Request/response logging
- [ ] Business metrics tracked
- [ ] Performance metrics collected
- [ ] Error rates monitored
- [ ] Trace context propagated
- [ ] Sampling strategy defined

## Example Analysis Output

```markdown
# Observability Analysis Report

## Summary
- **Files Analyzed:** 45
- **Critical Gaps:** 3
- **High Priority Gaps:** 8
- **Medium Priority Gaps:** 12
- **Low Priority Gaps:** 5

## Critical Gaps

### 1. Missing Error Logging in Payment Handler
**Severity:** Critical
**Location:** src/handlers/payment.py:45-60
**Impact:** Payment failures are not logged, making debugging impossible
**Recommendation:** Add structured error logging with full context
**Code Example:**
```python
# Before
try:
    process_payment(order)
except:
    pass

# After
try:
    process_payment(order)
except Exception as e:
    logger.error("payment_processing_failed", 
                 order_id=order.id,
                 error=str(e),
                 exc_info=True)
    raise
```
**Effort:** 2 hours
**Priority:** 1

[Continue for all gaps...]
```

---

**Remember**: Focus on actionable, specific recommendations with code examples. Prioritize by business impact and implementation effort.