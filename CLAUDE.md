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

xliffs-english-archivo/              # Archivo historico de originales en ingles

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

## Estructura del fichero XLIFF

### Cabecera (lineas 1-4)

```xml
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE xliff PUBLIC "-//XLIFF//DTD XLIFF//EN" "http://www.oasis-open.org/committees/xliff/documents/xliff.dtd">
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="urn:oasis:names:tc:xliff:document:1.2 xliff-core-1.2-strict.xsd">
<file datatype="html" source-language="en" target-language="en" date="2026-01-24" original="xliff-english.xliff">
```

En el archivo de entrada, `target-language="en"` porque aun no se ha traducido. El sistema debe actualizar este valor al codigo ISO del idioma destino al generar el archivo traducido (ver reglas de procesamiento).

### Body (a partir de linea 5)

Cada etiqueta sigue esta estructura repetitiva:

```xml
<trans-unit id="Catalog type" extradata="CoursecatalogApp">
      <source><![CDATA[Display modality]]></source>
      <target><![CDATA[Display modality]]></target>
</trans-unit>
```

- **trans-unit id**: Identificador unico de la etiqueta. Se usa para asociar la traduccion con su unidad, pero NO es la clave de cache. El cache usa `hash(texto_origen)` como clave.
- **source**: Texto en el idioma origen (`source-language`). Nunca se modifica.
- **target**: Texto a traducir. En el archivo de entrada contiene el mismo texto que `<source>` (ingles). El sistema lo reemplaza por la traduccion al idioma destino.

## Reglas de procesamiento del fichero

1. El archivo de entrada siempre tiene `source-language="en"` (ingles)
2. Al generar el archivo traducido, el sistema debe actualizar `target-language` al codigo ISO del idioma destino (`ca`, `gl`, `eu`, etc.). **Nota:** En Docebo, catalan/gallego/euskera estan mapeados a slots de idiomas no usados (am/bs/ar respectivamente), pero el archivo generado debe usar codigos ISO reales.
3. Solo se traducen las etiquetas `<target>`
4. **NO** traducir, editar ni modificar las etiquetas `<source>`
5. Una etiqueta vacia se mantiene vacia (no se traduce)
6. Siglas, acronimos, anglicismos y terminos tecnicos se mantienen en su idioma original sin traducir
7. Al procesar un fichero, se genera automaticamente una copia del original en ingles (sin modificar) en `xliffs-english-archivo/` con nombre `YYYYMMDD-xliff-english.xliff`. Esto permite trazar cada momento en que se ejecuto una traduccion.

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
