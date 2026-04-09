# Workflow: Redacción de Caso de Éxito SDP desde Documentos del Proyecto

Sigue este proceso cuando el usuario tenga documentos del proyecto y necesite redactar un caso de éxito.

## Paso 1 — Recopilar y leer documentos

Solicitar o leer los siguientes documentos en orden de prioridad:

| Documento | Qué extraer |
|---|---|
| Acta de cierre / entrega | Fechas reales, alcance entregado, firmantes del cliente |
| Memoria técnica / EspArqReq | Servicios AWS, arquitectura, Account IDs, subnets, configuraciones |
| Propuesta económica / SOW | Fecha de inicio, alcance original, servicios propuestos |
| Diagramas de arquitectura | Adjuntar directamente al formulario SDP |
| Correos o minutas | Contexto adicional, resultados mencionados por el cliente |

## Paso 2 — Extraer información clave

Con los documentos disponibles, identificar y anotar:

**Del cliente:**
- Nombre completo y tipo de organización (sector, país)
- Account ID(s) de AWS involucrados
- Contacto que puede validar el caso ante AWS (nombre + cargo)

**Del proyecto:**
- Servicios AWS utilizados (lista completa)
- Problema original que motivó el engagement
- Fechas: inicio, fin, go-live (si hay subproyectos, fechas de cada uno)
- Herramientas de terceros involucradas

**De los resultados:**
- Cualquier métrica documentada (latencia, costo, disponibilidad, tiempo)
- Beneficios cualitativos claros aunque no tengan número exacto
- Problemas resueltos que sean verificables por el cliente

## Paso 3 — Redactar campo "Desafío del cliente"

**Longitud**: 3-5 párrafos (300-500 palabras)

**Estructura**:
1. Contexto del cliente (quién es, industria, escala de operaciones)
2. Problema técnico específico (qué no funcionaba o faltaba)
3. Por qué era crítico o urgente resolverlo
4. Limitaciones del enfoque anterior (si aplica)

**Reglas**:
- Escribir desde la perspectiva del cliente
- NO mencionar al partner/implementador en esta sección
- Usar lenguaje que el cliente reconocería como suyo
- Evitar frases genéricas como "necesitaban mejorar su infraestructura"

**Ejemplo de apertura fuerte**:
> "[Cliente] opera [N] aplicaciones críticas distribuidas en [N] cuentas AWS bajo una organización de Control Tower. Sin una capa de red centralizada, cada nuevo proyecto requería configurar conectividad bilateral manualmente, incrementando el riesgo operacional y los tiempos de despliegue."

## Paso 4 — Redactar campo "Solución propuesta"

**Longitud**: 4-7 párrafos técnicos + tabla de servicios

**Estructura**:
1. Párrafo introductorio: visión general de la arquitectura
2. Un párrafo por componente mayor (nombrar servicios AWS exactos)
3. Tabla obligatoria: Servicio AWS | Rol en la solución
4. Mención de Well-Architected Framework si aplica

**Nivel de detalle esperado**:
- Nombres exactos: "Amazon Aurora PostgreSQL" no "base de datos"
- Configuraciones relevantes: número de AZs, CIDRs, cantidad de instancias
- Flujo de datos entre componentes

**Plantilla de tabla de servicios**:
```
| Servicio AWS | Rol en la solución |
|---|---|
| [Servicio] | [Qué hace específicamente en este proyecto] |
```

## Paso 5 — Completar campos de fechas

Si hay múltiples subproyectos, documentar fechas por subproyecto:

```
Fecha de inicio: [fecha del primer kickoff o propuesta aceptada]
Fecha de finalización: [fecha del último acta de cierre]
Fecha de producción: [fecha de go-live real, más reciente si hubo fases]
```

Si solo hay un acta de cierre, usar esa fecha como referencia de fin y producción.

## Paso 6 — Redactar campo "Resultados/Outcomes"

**Orden de impacto para AWS**:
1. Métricas de negocio (costo, velocidad, ingresos)
2. Métricas técnicas medibles (latencia ms, uptime %, throughput)
3. Mejoras operacionales (reducción de tickets, eliminación de procesos manuales)
4. Mejoras de seguridad (cumplimiento normativo, reducción de superficie de ataque)

**Formato recomendado** (lista numerada, cada ítem con negrita + descripción):
```
1. **[Nombre del resultado]**: [Descripción verificable del beneficio logrado].
2. **[Nombre del resultado]**: [Descripción verificable del beneficio logrado].
```

**Si no hay métricas exactas**, usar:
- Número de cuentas/ambientes/aplicaciones conectadas o protegidas
- Eliminación de un riesgo o problema específico
- Descripción del estado "antes vs después"

## Paso 7 — Sección de diagramas

Siempre incluir esta sección indicando:
- Qué documentos contienen los diagramas existentes
- Qué diagramas se deben adjuntar al formulario
- Si no existe diagrama, indicarlo claramente para que el equipo lo cree

## Paso 8 — Generar documento Word

Una vez redactados todos los campos, generar un `.docx` profesional usando `docx-js` con:
- Encabezado con nombre del cliente y SDP objetivo
- Cada campo como sección con título en heading
- Tabla de servicios AWS con formato de colores
- Sección de fechas clara y organizada
- Footer con datos de contacto del cliente y del equipo ITERA
