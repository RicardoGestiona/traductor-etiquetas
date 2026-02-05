# Informe de Errores de Traduccion

**Generado:** 2026-02-05 08:51:26
**Total de errores pendientes:** 0

---

## Resumen por Tipo de Error

No hay errores pendientes.


## Detalle de Errores

No hay errores para mostrar.

## Guia de Solucion

### Tipos de Error y Soluciones

| Error | Causa | Solucion |
|-------|-------|----------|
| `API devolvio respuesta vacia` | La API de traduccion no pudo procesar el texto | Reintentar con `python -m traductor reintentar` |
| `Texto origen vacio` | Etiqueta XLIFF sin contenido | Ignorar (no requiere accion) |
| `Timeout` | Tiempo de espera agotado | Reintentar mas tarde |
| `Rate limit exceeded` | Limite de peticiones excedido | Esperar 1 hora y reintentar |
| `Connection error` | Error de red | Verificar conexion y reintentar |

### Comandos Utiles

```bash
# Ver traducciones pendientes
python -m traductor pendientes --detalle

# Reintentar todas las pendientes
python -m traductor reintentar

# Reintentar solo un idioma
python -m traductor reintentar --idioma ca

# Limpiar pendientes (si son falsos positivos)
python -m traductor limpiar-pendientes
```

### Cuando Escalar

Escalar a revision manual si:
1. El mismo error persiste tras 3 reintentos
2. Hay mas de 100 errores del mismo tipo
3. Errores de tipo desconocido o no listado

---
*Informe generado automaticamente por el sistema de traduccion.*
