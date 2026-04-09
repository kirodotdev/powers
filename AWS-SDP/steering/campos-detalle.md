# Guía Detallada de Campos SDP — Con Ejemplos y Errores Comunes

## Campo: Name of the Publicly Available Case Study

**Formato**: `[Cliente] – [Descripción de la solución] con [Servicios principales AWS]`

**Ejemplos buenos**:
- "Comfandi – Transformación de Infraestructura de Red en AWS con Transit Gateway, VPN Site-to-Site, Network Firewall, CloudFront y Route 53"
- "Bancolombia – Plataforma de microservicios en Amazon EKS con alta disponibilidad multi-AZ"
- "EPM – Analítica en tiempo real con arquitectura Serverless en AWS Lambda y Kinesis"

**Errores comunes**:
- ❌ "Proyecto de infraestructura para cliente financiero" — demasiado vago
- ❌ "Implementación AWS para Comfandi" — no menciona qué servicios ni qué solución
- ✅ Debe identificar el SDP al que aplica con solo leer el nombre

---

## Campo: Desafío del cliente

**Longitud ideal**: 300-500 palabras

**Lo que AWS quiere ver**:
- Problema real de negocio, no solo técnico
- Impacto de NO resolver el problema
- Contexto suficiente para entender la magnitud del engagement
- Lenguaje del cliente (como si el cliente lo escribiera)

**Errores comunes**:
- ❌ Mencionar al partner/implementador: "Comfandi contactó a ITERA para..."
- ❌ Ser genérico: "necesitaban mejorar su infraestructura cloud"
- ❌ Mezclar desafío con solución en el mismo párrafo
- ✅ "Las aplicaciones Fovis y Fosfec carecían de protección perimetral web centralizada, exponiéndolas a amenazas OWASP sin visibilidad del tráfico de red."

**Plantillas de apertura por industria**:

*Caja de compensación / sector social:*
> "[Cliente] es una de las [adjetivo] cajas de compensación familiar de Colombia, con operaciones en [región] que atienden a más de [N] beneficiarios. Su infraestructura tecnológica soporta aplicaciones críticas de [subsidios/salud/educación] que requieren disponibilidad continua."

*Sector financiero:*
> "[Cliente] opera en [N] países con una plataforma de [servicios] que procesa [N] transacciones diarias. La creciente demanda de conectividad segura entre entornos cloud y sistemas legados representaba un riesgo operacional significativo."

---

## Campo: Solución propuesta

**Nivel de detalle esperado por AWS**:

| Elemento | Malo | Bueno |
|---|---|---|
| Nombre de servicio | "base de datos" | "Amazon Aurora PostgreSQL-Compatible" |
| Configuración | "multi-zona" | "3 zonas de disponibilidad: us-east-1a, 1b, 1c" |
| Red | "VPC privada" | "VPC CIDR 10.249.36.0/22 con subnets privadas bajo Control Tower" |
| Seguridad | "con WAF" | "AWS WAF con 1 Web ACL, 9 reglas personalizadas y 1 Managed Rule Group" |

**Plantilla de párrafo de introducción**:
> "[Partner] diseñó e implementó una arquitectura de [tipo: red/contenedores/serverless] sobre AWS que [qué resuelve]. La solución integra los siguientes componentes..."

**Plantilla de tabla de servicios** (siempre incluir):
```
| Servicio AWS | Rol en la solución |
|---|---|
| AWS Transit Gateway | Hub central de enrutamiento entre N VPCs de las cuentas de [cliente] |
| AWS Site-to-Site VPN | N túneles cifrados para conectar [A] con [B] |
```

---

## Campo: Aplicaciones o soluciones de terceros

**Cuándo aplica**:
- Herramientas de CI/CD externas (Jenkins, GitLab, GitHub Actions)
- Monitoring de terceros (Datadog, New Relic, Grafana)
- Identity providers (Keycloak, Okta, Active Directory)
- Sistemas on-premise conectados
- Proveedores externos conectados vía VPN/Direct Connect
- IaC: Terraform, Pulumi, Ansible (si son parte de la solución entregada)

**Si no hay terceros**:
> "No se utilizaron soluciones de terceros. La solución fue implementada 100% sobre servicios nativos de AWS."

---

## Campo: Cómo se utiliza AWS como parte de la solución

**Formato recomendado**: tabla + párrafo de flujo de integración

**Tip**: Ser específico por servicio. Ejemplos:

| Vago ❌ | Específico ✅ |
|---|---|
| "Amazon VPC para networking" | "Amazon VPC con CIDR 10.249.36.0/22, subnets privadas en 3 AZs bajo Control Tower" |
| "CloudWatch para monitoreo" | "CloudWatch para ingesta de VPC Flow Logs (20 GB/mes) y auditoría de tráfico de red" |
| "S3 para almacenamiento" | "Amazon S3 como origen de activos estáticos para distribución vía CloudFront" |

---

## Campos de Fechas

### Reglas importantes:
- `Inicio ≤ Fin ≤ Producción` — AWS verifica consistencia
- Si hay múltiples subproyectos, documentar el rango completo
- Usar la fecha del acta de cierre como referencia de fin cuando exista
- El proyecto DEBE estar en producción — si aún no lo está, no aplica para SDP

### Cuando hay múltiples fases:
```
Fecha de inicio: [fecha del primer subproyecto]
Fecha de finalización: [fecha del último cierre]  
Fecha de producción: [fecha de go-live del componente principal]
```

---

## Campo: Resultados/Outcomes

### Jerarquía de valor para AWS:
1. 🥇 Métricas de negocio (USD ahorrados, % reducción de costos, time-to-market)
2. 🥈 Métricas técnicas medibles (latencia, uptime %, throughput RPS)
3. 🥉 Mejoras operacionales (tickets reducidos, procesos eliminados)
4. Mejoras de seguridad (cumplimiento logrado, riesgos mitigados)

### Plantillas por tipo de resultado:

**Conectividad/Networking**:
> "Se consolidó la conectividad entre [N] cuentas AWS mediante Transit Gateway, reemplazando la gestión bilateral de peerings por un modelo hub-and-spoke con un único punto de control."

**Seguridad**:
> "El WAF centralizado con [N] reglas activas protege [N] aplicaciones contra amenazas OWASP Top 10, con visibilidad completa del tráfico mediante VPC Flow Logs."

**Alta disponibilidad**:
> "La arquitectura multi-AZ garantiza disponibilidad continua 7x24x365 con failover automático ante fallas de zona de disponibilidad."

**Distribución de contenido**:
> "CloudFront redujo la latencia de entrega de contenido estático para usuarios de [aplicación] en [región], con pruebas funcionales aprobadas en ambientes QA y producción."

---

## Campo: Diagramas de arquitectura

**Formatos aceptados**: PNG, JPG, PDF

**Checklist del diagrama**:
- [ ] Todos los servicios AWS del caso aparecen en el diagrama
- [ ] Se muestra el flujo de datos/conectividad entre componentes
- [ ] Se identifican las cuentas AWS separadas (si aplica)
- [ ] Se muestran las zonas de disponibilidad (si hay HA)
- [ ] Se muestran conexiones a sistemas externos/on-premise

**Herramientas recomendadas**:
- draw.io / diagrams.net (gratis, íconos oficiales AWS disponibles)
- AWS Architecture Icons oficiales: https://aws.amazon.com/architecture/icons/
- Cloudcraft (especializado en AWS)
- Lucidchart

**Si el diagrama no existe**: indicarlo explícitamente en el documento y crear una tarea para que el equipo técnico lo genere antes de enviar a AWS.
