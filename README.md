# Traductor de Etiquetas Docebo

Sistema de traduccion automatizada de etiquetas de Docebo (plataforma LMS) a multiples idiomas. Procesa archivos XLIFF con deteccion incremental y cache en SQLite.

## Requisitos

- Python 3.7+
- Conexion a internet (Google Translate via deep-translator)

## Instalacion

```bash
pip install -r requirements.txt
```

## Uso

### Procesamiento automatico (recomendado)

```bash
# Depositar archivo XLIFF en traduccion-pendiente/ y ejecutar:
python -m traductor procesar

# Modo vigilancia continua
python -m traductor procesar --watch
```

El sistema traduce automaticamente a catalan, gallego y euskera. Los archivos generados se guardan en `traducidos/{idioma}/`.

### Traduccion manual

```bash
python -m traductor traducir archivo.xliff --idioma catalan
python -m traductor traducir archivo.xliff --idioma catalan euskera gallego
```

### Gestion de pendientes

```bash
python -m traductor pendientes               # Lista traducciones fallidas
python -m traductor pendientes --detalle     # Detalle de cada pendiente
python -m traductor reintentar               # Reintenta todas
python -m traductor reintentar --idioma ca   # Reintenta solo catalan
python -m traductor limpiar-pendientes       # Elimina pendientes de la BD
```

### Utilidades

```bash
python -m traductor estadisticas
python -m traductor listar idiomas
```

## Idiomas soportados

| Idioma | Codigo |
|--------|--------|
| Catalan | ca |
| Euskera | eu |
| Gallego | gl |
| Valenciano | va |
| Espanol | es |
| Frances | fr |
| Portugues | pt |
| Italiano | it |
| Aleman | de |

## Arquitectura

```
traductor/                          # Paquete principal
├── __main__.py                     # Punto de entrada CLI
├── cli.py                          # Interfaz de linea de comandos
├── config/idiomas.py               # Configuracion de idiomas
├── core/
│   ├── base_translator.py          # Clase base para traductores
│   └── xliff_parser.py             # Parser XLIFF con soporte CDATA
├── database/
│   ├── db_manager.py               # Gestor SQLite
│   ├── migrations.py               # Migracion de checkpoints JSON
│   └── models.py                   # Esquema de BD
├── services/
│   ├── batch_processor.py          # Procesador por lotes
│   ├── incremental_detector.py     # Deteccion de etiquetas nuevas
│   └── translation_service.py      # Servicio principal de traduccion
└── utils/
    ├── file_naming.py              # Nomenclatura estandarizada
    ├── logger.py                   # Logging JSON estructurado
    └── report_generator.py         # Generador de informes

traduccion-pendiente/               # Depositar archivos XLIFF aqui
└── _procesados/                    # Archivos ya procesados
traducidos/                         # Salida de traducciones
├── catalan/
├── euskera/
└── gallego/
traductor.db                        # Cache SQLite
```

## Workflow

1. Depositar archivo XLIFF en `traduccion-pendiente/`
2. Ejecutar `python3 -m traductor procesar`
3. El sistema detecta etiquetas nuevas vs cacheadas (solo traduce lo nuevo)
4. Archivos generados en `traducidos/{idioma}/YYYYMMDD-nombre-codigo.xliff`
5. Original movido a `traduccion-pendiente/_procesados/`

## Tech Stack

- **Python 3** — Lenguaje principal
- **SQLite** — Cache de traducciones y registro de sesiones
- **deep-translator** — Traducciones via Google Translate
- **tqdm** — Barras de progreso

## Licencia

Uso interno.
