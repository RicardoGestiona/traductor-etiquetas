# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sistema de traducción automatizada de etiquetas de Docebo (plataforma LMS) a múltiples idiomas. Utiliza scripts Python para procesar y traducir contenido.

## Build & Development Commands

```bash
# Ejecutar scripts de traducción
python3 analizar_no_traducidas.py
python3 aplicar_correcciones.py

# Verificar traducciones
./check.sh
```

## Tech Stack

- Python 3
- JSON para checkpoints de traducción

## Architecture

```
├── analizar_no_traducidas.py      # Análisis de etiquetas sin traducir
├── aplicar_correcciones.py        # Aplicar correcciones a traducciones
├── check.sh                       # Script de verificación
├── checkpoint_euskera.json        # Checkpoint traducción euskera
├── checkpoint_gallego.json        # Checkpoint traducción gallego
├── checkpoint_simple.json         # Checkpoint básico
├── crear_muestra.py               # Crear muestra de etiquetas
├── Idiomas/                       # Archivos de idiomas traducidos
├── instalar.sh                    # Script de instalación
├── registro-prompts.md            # Histórico de prompts/instrucciones
├── traductor_euskera.py           # Traductor a euskera
├── traductor_gallego.py           # Traductor a gallego
├── traductor_simple.py            # Traductor simple (principal)
├── traductor_xliff.py             # Traductor XLIFF profesional
├── verificar_traducciones.py      # Verificación de traducciones
└── xliff-english.xliff            # Archivo fuente XLIFF
```

## Workflow

1. Analizar etiquetas no traducidas con `analizar_no_traducidas.py`
2. Revisar resultados y ajustar
3. Aplicar correcciones con `aplicar_correcciones.py`
4. Verificar con `check.sh`

## Checkpoints

Los archivos `checkpoint_*.json` guardan el estado de las traducciones para poder reanudar el proceso.

## Quality Assurance

**IMPORTANTE:** Antes de dar por finalizado cualquier cambio, verificar siempre:
- Que los cambios son seguros y no introducen vulnerabilidades
- Que no se ha modificado nada funcionalmente de forma no intencionada
- Utilizar los agentes de QA y Seguridad para validar los cambios
- Antes de subir cambios a GitHub, preguntar al usuario si van a la rama `main` o a la rama `pre`
- Registra en el archivo `registro-prompts.md` todas las instrucciones del usuario con numeración correlativa, fecha y hora para poder hacer seguimiento de las interacciones