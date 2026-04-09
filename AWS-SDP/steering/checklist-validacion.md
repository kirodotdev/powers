# Checklist de Validación — Antes de Enviar a AWS

Ejecuta esta validación completa antes de enviar cualquier customer reference al portal de APN.

---

## ✅ Validación de Contenido

### Campos obligatorios
- [ ] **Nombre del caso** está completo y menciona los servicios AWS del SDP objetivo
- [ ] **Desafío del cliente** tiene al menos 3 párrafos y describe un problema real y específico
- [ ] **Solución propuesta** describe la arquitectura componente por componente
- [ ] **Tabla de servicios AWS** está incluida con el rol específico de cada servicio
- [ ] **Terceros/ISVs** están listados (o se indica explícitamente que no aplica)
- [ ] **Las tres fechas** están completas: inicio, fin, producción
- [ ] **Resultados** incluyen al menos 3 outcomes documentados
- [ ] **Diagramas** están identificados y listos para adjuntar

### Calidad del contenido
- [ ] El desafío NO menciona al partner/implementador
- [ ] La solución nombra servicios AWS con sus nombres exactos y completos
- [ ] Las fechas son consistentes: inicio ≤ fin ≤ producción
- [ ] Los resultados son verificables por el cliente (no inventados)
- [ ] Se incluye al menos un Account ID de AWS del cliente
- [ ] El lenguaje es profesional y puede entenderse sin contexto interno

---

## ✅ Validación Técnica

### Servicios AWS
- [ ] Los servicios listados corresponden al SDP al que se está aplicando
- [ ] Los servicios están en producción (no solo planeados o en desarrollo)
- [ ] Los Account IDs mencionados son los correctos para el cliente

### Para SDP Networking en particular:
- [ ] Se menciona al menos uno de: Transit Gateway, Direct Connect, VPN Site-to-Site
- [ ] Se menciona Amazon VPC con configuración de subnets
- [ ] Si hay WAF: se especifica el número de reglas y Web ACLs
- [ ] Si hay CloudFront: se menciona la configuración de origen (S3 o ALB)
- [ ] Si hay Route 53: se describe el rol de DNS en la solución

---

## ✅ Validación de Fechas

| Verificación | ¿OK? |
|---|---|
| Fecha de inicio ≤ fecha de fin | [ ] |
| Fecha de fin ≤ fecha de producción (o igual) | [ ] |
| El proyecto ya está en producción (no planeado) | [ ] |
| Las fechas coinciden con documentos de soporte (actas, propuestas) | [ ] |
| Si hay subproyectos, todas las fechas son consistentes | [ ] |

---

## ✅ Validación del Diagrama

- [ ] Existe al menos un diagrama de arquitectura listo para adjuntar
- [ ] El diagrama muestra todos los servicios AWS mencionados en el caso
- [ ] El diagrama está en formato PNG, JPG o PDF
- [ ] El diagrama es legible (no demasiado pequeño o comprimido)
- [ ] Si hay múltiples cuentas AWS, el diagrama las distingue claramente

**Si el diagrama no existe**: DETENER — no enviar hasta tenerlo. Es requisito obligatorio.

---

## ✅ Validación del Cliente

- [ ] Hay un contacto identificado en el cliente que puede validar el caso ante AWS
- [ ] El contacto tiene cargo relevante (Gerente TI, Arquitecto, CTO, etc.)
- [ ] El cliente está de acuerdo en ser referenciado públicamente (o privadamente)
- [ ] Los datos del cliente (nombre, Account ID, industria) son correctos

---

## ✅ Validación Final de Envío

- [ ] El documento Word está completo y bien formateado
- [ ] El diagrama de arquitectura está adjunto como archivo separado
- [ ] Se tienen los datos de contacto del cliente listos para el formulario APN
- [ ] El SDP al que aplica el caso tiene los servicios mínimos requeridos
- [ ] Se ha revisado ortografía y redacción profesional

---

## 🚨 Señales de alerta (no enviar si alguna aplica)

- ❌ Fechas de producción en el futuro
- ❌ Sin diagrama de arquitectura
- ❌ Resultados que el cliente no podría confirmar
- ❌ Account IDs incorrectos o ficticios
- ❌ Servicios AWS que no están en producción
- ❌ Sin contacto del cliente identificado para validación de AWS
- ❌ El caso mezcla servicios de múltiples SDPs sin foco claro

---

## Documentos de soporte recomendados para conservar

Guardar junto al caso de éxito en caso de que AWS solicite evidencia:

1. Acta de cierre firmada por el cliente
2. Propuesta económica o SOW aceptado
3. Memoria técnica / Especificación de Arquitectura
4. Capturas de consola AWS mostrando los servicios desplegados
5. Diagrama de arquitectura en formato editable (draw.io, Lucidchart)
