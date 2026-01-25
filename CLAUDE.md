# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sistema de traduccion automatizada de etiquetas de Docebo (plataforma LMS) a multiples idiomas. Utiliza scripts Python para procesar y traducir contenido XLIFF.

## Build & Development Commands

```bash
# Procesamiento automatico (recomendado)
python -m traductor procesar                 # Procesa archivos en traduccion-pendiente/
python -m traductor procesar --watch         # Modo vigilancia continua

# Traduccion manual
python -m traductor traducir archivo.xliff --idioma catalan
python -m traductor traducir archivo.xliff --idioma catalan euskera gallego

# Gestion de traducciones pendientes (fallidas)
python -m traductor pendientes               # Lista traducciones que fallaron
python -m traductor pendientes --detalle     # Muestra detalle de cada pendiente
python -m traductor reintentar               # Reintenta todas las pendientes
python -m traductor reintentar --idioma ca   # Reintenta solo catalan
python -m traductor limpiar-pendientes       # Elimina pendientes de la BD

# Utilidades
python -m traductor estadisticas
python -m traductor listar idiomas

# Scripts legacy (deprecados - movidos a legacy/scripts/)
```

## Tech Stack

- Python 3
- SQLite para base de datos de traducciones
- deep-translator para traducciones (Google Translate)
- tqdm para barras de progreso

## Architecture

```
traductor/                          # Paquete principal (nuevo sistema)
├── __init__.py
├── __main__.py                     # Punto de entrada CLI
├── cli.py                          # Interfaz de linea de comandos
├── config/
│   ├── __init__.py
│   └── idiomas.py                  # Configuracion de idiomas soportados
├── core/
│   ├── __init__.py
│   ├── base_translator.py          # Clase base para traductores
│   └── xliff_parser.py             # Parser XLIFF con soporte CDATA
├── database/
│   ├── __init__.py
│   ├── db_manager.py               # Gestor de base de datos SQLite
│   ├── migrations.py               # Migracion de checkpoints JSON
│   └── models.py                   # Esquema de BD
├── services/
│   ├── __init__.py
│   ├── batch_processor.py          # Procesador por lotes automatico
│   ├── incremental_detector.py     # Deteccion de etiquetas nuevas
│   └── translation_service.py      # Servicio principal de traduccion
└── utils/
    ├── __init__.py
    ├── file_naming.py              # Nomenclatura estandarizada
    └── logger.py                   # Sistema de logging

traductor.db                        # Base de datos SQLite

# Carpetas de procesamiento automatico
traduccion-pendiente/               # Depositar archivos XLIFF aqui (siempre vacia)
└── _procesados/                    # Archivos ya procesados
traducidos/                         # Salida de traducciones automaticas
├── catalan/
├── euskera/
└── gallego/

# Carpetas legacy (archivos historicos)
Idiomas/                            # Traducciones manuales antiguas
└── Legacy/                         # Archivos XLIFF historicos
legacy/                             # Archivos legacy
├── checkpoints/                    # Checkpoints JSON migrados
└── scripts/                        # Scripts deprecados (traductores antiguos)
```

## Idiomas Soportados

- catalan (ca)
- euskera (eu)
- gallego (gl)
- valenciano (va)
- espanol (es)
- frances (fr)
- portugues (pt)
- italiano (it)
- aleman (de)

## Workflow Automatico (Recomendado)

1. Depositar archivo XLIFF en `traduccion-pendiente/`
2. Ejecutar procesamiento:
   ```bash
   python -m traductor procesar           # Una vez
   python -m traductor procesar --watch   # Continuo
   ```
3. El sistema traduce automaticamente a catalan, gallego y euskera
4. Archivos generados en `traducidos/{idioma}/YYYYMMDD-nombre-codigo.xliff`
5. Archivo original movido a `traduccion-pendiente/_procesados/`

## Workflow Manual

1. Ejecutar traduccion especifica:
   ```bash
   python -m traductor traducir archivo.xliff --idioma catalan euskera gallego
   ```
2. El sistema detecta automaticamente etiquetas nuevas vs cacheadas
3. Solo traduce lo nuevo, reutiliza el cache existente

## Nomenclatura de Archivos

Formato: `YYYYMMDD-nombre_original-codigo_idioma.xliff`

Ejemplo: `20260123-xliff-english-ca.xliff`

Ubicacion: `Idiomas/carpeta_idioma/archivo.xliff`

## Base de Datos

El sistema usa SQLite (`traductor.db`) con:
- **cache_traducciones**: Cache global de traducciones por idioma
- **traducciones**: Registro de sesiones de traduccion
- **traducciones_pendientes**: Etiquetas que fallaron para reintentar despues

### Esquema de cache_traducciones
```sql
(idioma_destino, hash_origen, texto_origen, texto_traducido, fecha_creacion, veces_usado)
```

### Esquema de traducciones_pendientes
```sql
(idioma_destino, hash_origen, texto_origen, motivo_fallo, archivo_origen, fecha_fallo, reintentos)
```

## Patrones de Codigo Criticos

**IMPORTANTE - Evitar estos errores:**

1. **Guardar valores originales antes de mutar objetos:**
   ```python
   # INCORRECTO - El valor original se pierde
   traduccion = traducir(unit.target)
   parser.actualizar(unit, traduccion)  # Modifica unit.target
   cache.append((unit.target, traduccion))  # unit.target ya es la traduccion!

   # CORRECTO - Guardar antes de modificar
   texto_original = unit.target  # Guardar ANTES de actualizar
   traduccion = traducir(texto_original)
   parser.actualizar(unit, traduccion)
   cache.append((texto_original, traduccion))  # Usa el valor guardado
   ```

2. **Cache de traducciones:** El campo `texto_origen` debe contener siempre el texto en idioma original (ingles), nunca el texto traducido. Verificar con:
   ```sql
   SELECT texto_origen, texto_traducido FROM cache_traducciones
   WHERE idioma_destino='ca' ORDER BY fecha_creacion DESC LIMIT 5;
   ```

3. **Validar traducciones antes de guardar:** Siempre verificar que la traduccion no sea None antes de guardar en cache:
   ```python
   # INCORRECTO - Puede guardar None en cache
   traduccion = traductor.traducir(texto)
   cache.append((texto, traduccion))

   # CORRECTO - Validar antes de guardar
   traduccion = traductor.traducir(texto)
   if traduccion is not None and traduccion.strip():
       cache.append((texto, traduccion))
   else:
       pendientes.append((texto, "Traduccion devolvio None"))
   ```

## Manejo de Errores en Traducciones

El sistema maneja errores de traduccion de forma robusta:

1. **Guardado incremental**: El cache se guarda cada 100 traducciones, no solo al final
2. **Validacion de None**: Las traducciones que devuelven None se registran como pendientes
3. **Tabla de pendientes**: Las etiquetas fallidas se guardan en `traducciones_pendientes` para reintentar
4. **Archivo siempre generado**: El XLIFF se genera aunque haya errores (etiquetas fallidas mantienen texto original)

### Verificar pendientes
```sql
SELECT idioma_destino, COUNT(*) FROM traducciones_pendientes GROUP BY idioma_destino;
```

## Quality Assurance

**IMPORTANTE:** Antes de dar por finalizado cualquier cambio, verificar siempre:
- Que los cambios son seguros y no introducen vulnerabilidades
- Que no se ha modificado nada funcionalmente de forma no intencionada
- Utilizar los agentes de QA y Seguridad para validar los cambios
- Utilizar el agente de QA para validar el comportamiento de la funcionalidad y validar que todas las anteriores funcionalidades permanecen igual
- Antes de subir cambios a GitHub, preguntar al usuario si van a la rama `main` o a la rama `pre`
- Registra en el archivo `registro-prompts.md` todas las instrucciones del usuario con numeracion correlativa, fecha y hora para poder hacer seguimiento de las interacciones
