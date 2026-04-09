# Banco de Resultados y Métricas por Tipo de SDP

Usa este banco cuando el usuario no tenga métricas exactas disponibles.
Siempre priorizar datos reales del proyecto sobre estas plantillas.

---

## SDP Networking

**Conectividad centralizada (Transit Gateway)**
- "Se consolidó la conectividad entre [N] cuentas AWS mediante Transit Gateway, eliminando la gestión de [N*(N-1)/2] peerings bilaterales y simplificando el modelo de enrutamiento a un único hub central."
- "La arquitectura hub-and-spoke permite al equipo de TI de [cliente] gestionar toda la conectividad de red desde una cuenta centralizada de Networking."

**VPN Site-to-Site**
- "Se establecieron [N] túneles VPN Site-to-Site cifrados con AES-256, eliminando la transmisión de datos sensibles sobre internet público entre [A] y [B]."
- "Los [N] ambientes de integración con [proveedor externo] (producción, contingencia y pruebas) quedaron operativos con cifrado extremo a extremo."

**WAF / Seguridad perimetral**
- "El WAF centralizado con [N] reglas activas protege [N] aplicaciones contra las amenazas más comunes de la web (OWASP Top 10)."
- "La habilitación de VPC Flow Logs con ingesta en CloudWatch provee visibilidad completa del tráfico de red, habilitando detección de anomalías y auditoría forense."

**CloudFront + S3**
- "La distribución CloudFront redujo la latencia de entrega de contenido estático para los usuarios de [aplicación] al servir contenido desde edge locations de AWS."
- "El despliegue en ambientes QA y Producción con pruebas funcionales aprobadas garantiza un pipeline de entrega continua validado."

**Alta disponibilidad**
- "La infraestructura de red opera en 3 zonas de disponibilidad (us-east-1a, 1b, 1c) garantizando continuidad ante fallas de zona."
- "Disponibilidad 7x24x365 documentada y soportada por equipo de soporte técnico dedicado."

---

## SDP Containers (EKS)

- "El clúster EKS multi-AZ garantiza alta disponibilidad con failover automático, sin interrupciones de servicio ante fallas de zona."
- "La migración de [aplicación] a contenedores en EKS redujo el tiempo de despliegue de [X horas] a [Y minutos]."
- "Horizontal Pod Autoscaler (HPA) permite absorber picos de tráfico automáticamente sin intervención del equipo de operaciones."
- "Se redujo el tiempo de provisioning de nuevos ambientes de [X días] a [Y horas] mediante infraestructura como código."
- "La separación de workloads en namespaces de Kubernetes mejoró el aislamiento de seguridad entre ambientes."

---

## SDP Containers (ECS / Fargate)

- "Fargate eliminó la necesidad de gestionar instancias EC2, reduciendo las horas dedicadas a patching y mantenimiento de SO."
- "La arquitectura ECS con Fargate escala automáticamente según la demanda, optimizando costos al pagar solo por los recursos utilizados."
- "El pipeline CI/CD integrado con ECR redujo el tiempo de entrega de nuevas versiones a producción."

---

## SDP Serverless

- "Lambda con API Gateway soporta hasta [N] transacciones por segundo sin aprovisionamiento previo de infraestructura."
- "El modelo serverless eliminó la gestión de servidores, reduciendo las horas de operación dedicadas a mantenimiento en un [X]%."
- "La arquitectura event-driven con Lambda redujo el costo de cómputo respecto al modelo previo basado en instancias EC2 siempre activas."
- "El tiempo de time-to-market para nuevas funcionalidades se redujo al eliminar ciclos de provisioning de infraestructura."

---

## SDP Database (RDS / Aurora)

- "Aurora PostgreSQL con replicación multi-AZ garantiza un RTO menor a [N] minutos y RPO menor a [N] minutos ante fallas."
- "La migración a Aurora Serverless v2 eliminó el sobreaprovisionamiento de base de datos, reduciendo costos de [X]% mensual."
- "Se logró disponibilidad del [99.9/99.99]% para la base de datos de producción."
- "Las automated backups y point-in-time recovery de RDS garantizan protección de datos sin intervención manual."

---

## SDP Security

- "AWS Security Hub centraliza hallazgos de seguridad de [N] cuentas en un único panel de control, reduciendo el tiempo de respuesta ante incidentes."
- "GuardDuty detectó y alertó sobre comportamientos anómalos en las primeras semanas de operación."
- "El cliente logró cumplimiento con [ISO 27001/SOC 2/PCI DSS] habilitado por los controles implementados."
- "AWS Config con reglas personalizadas garantiza cumplimiento continuo de políticas de seguridad corporativas."

---

## SDP Migration

- "La migración de [N] servidores a AWS se completó en [N semanas] con cero tiempo de inactividad para los usuarios finales."
- "Se redujo el costo total de infraestructura en un [X]% respecto al modelo on-premise previo."
- "La arquitectura cloud-native permite escalar recursos en minutos, sin los ciclos de procurement de hardware físico."

---

## Métricas genéricas útiles (cuando no hay datos exactos)

Cuando no hay métricas numéricas, documentar al menos:

- Número de cuentas AWS integradas en la solución
- Número de ambientes cubiertos (dev, QA, staging, producción)
- Número de aplicaciones protegidas o conectadas
- Número de regiones o AZs utilizadas
- Número de túneles/conexiones establecidas
- Número de reglas de seguridad configuradas
- Estado antes vs después (descriptivo pero verificable)

---

## Cómo obtener métricas del cliente

Si no hay métricas documentadas, preguntar al contacto del cliente:

1. ¿Cuánto tiempo tomaba antes el proceso que ahora es automatizado?
2. ¿Cuántos incidentes de conectividad/seguridad tenían antes vs ahora?
3. ¿Cuánto gastaban en infraestructura antes? ¿Cuánto gastan ahora con AWS?
4. ¿Cuántas personas se necesitaban para gestionar X antes vs ahora?
5. ¿Cuál es el tiempo de recuperación ante fallos ahora vs antes?
6. ¿Cuántas aplicaciones o usuarios se benefician de la solución?
