# 🌍 Traductor XLIFF - English to Catalan

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

Aplicación profesional para traducir archivos XLIFF del inglés al catalán de forma automática usando APIs de traducción.

## 🚀 Características

- ✅ **Traducción automática** inglés → catalán
- ✅ **Sistema de checkpoints** - Guarda el progreso automáticamente
- ✅ **Reintentos automáticos** en caso de errores
- ✅ **Barra de progreso visual** con `tqdm`
- ✅ **Múltiples APIs soportadas** - Google Translate, DeepL, deep-translator
- ✅ **Pausa y reanuda** en cualquier momento
- ✅ **Preserva la estructura** XLIFF original
- ✅ **Manejo de CDATA** sections
- ✅ **Scripts de monitoreo** incluidos

## 📋 Requisitos

- Python 3.7 o superior
- Conexión a internet
- (Opcional) API key de Google Cloud o DeepL para traducción profesional

## 🔧 Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/traductor-xliff.git
cd traductor-xliff
```

### 2. Instalar dependencias

**Opción A: Traductor Simple (Gratis, sin API key)**
```bash
pip install deep-translator tqdm
```

**Opción B: Instalación completa**
```bash
pip install -r requirements.txt
```

**Opción C: Instalador interactivo**
```bash
bash instalar.sh
```

## 📖 Uso

### Opción 1: Traductor Simple (Recomendado)

```bash
python3 traductor_simple.py archivo.xliff
```

Esto creará `archivo_ca.xliff` con las traducciones al catalán.

### Opción 2: Traductor Profesional

**Con Google Translate:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="ruta/a/credenciales.json"
python3 traductor_xliff.py archivo.xliff
```

**Con DeepL:**
```bash
python3 traductor_xliff.py archivo.xliff --api deepl --api-key TU_API_KEY
```

### Opciones Avanzadas

```bash
# Especificar archivo de salida
python3 traductor_simple.py entrada.xliff -o salida.xliff

# Usar un checkpoint personalizado
python3 traductor_simple.py entrada.xliff --checkpoint mi_progreso.json
```

## 🔍 Monitoreo del Progreso

### Verificación rápida
```bash
bash VERIFICAR_AHORA.sh
```

### Verificación completa (espera 30s para confirmar avance)
```bash
bash verificar_proceso.sh
```

### Ver progreso detallado
```bash
bash ver_progreso.sh
```

## 📊 Ejemplo de Uso

```bash
# 1. Instalar
pip install deep-translator tqdm

# 2. Probar que funciona
python3 prueba_traduccion.py

# 3. (Opcional) Crear una muestra para probar
python3 crear_muestra.py archivo_grande.xliff -n 100

# 4. Traducir
python3 traductor_simple.py archivo.xliff

# 5. Monitorear progreso
bash VERIFICAR_AHORA.sh
```

## 🎯 Estructura del Proyecto

```
traductor-xliff/
├── traductor_simple.py          # Traductor gratuito (recomendado)
├── traductor_xliff.py            # Traductor profesional con APIs
├── crear_muestra.py              # Crea archivos de muestra
├── prueba_traduccion.py          # Script de prueba
├── instalar.sh                   # Instalador interactivo
├── VERIFICAR_AHORA.sh            # Verificación rápida
├── ver_progreso.sh               # Progreso detallado
├── verificar_proceso.sh          # Verificación de avance
├── check.sh                      # Check instantáneo
├── requirements.txt              # Dependencias Python
├── README.md                     # Documentación en español
└── docs/                         # Documentación adicional
    ├── INICIO_RAPIDO.md
    ├── GUIA_VISUAL.txt
    ├── COMO_VERIFICAR.md
    └── PROCESO_COMPLETADO.md
```

## 🔄 Sistema de Checkpoints

El traductor guarda automáticamente el progreso cada pocas traducciones en un archivo `checkpoint_simple.json`. Si el proceso se interrumpe:

1. Simplemente ejecuta el mismo comando de nuevo
2. Continuará desde donde se quedó
3. No traducirá dos veces la misma línea

## ⚙️ Configuración

### APIs Soportadas

#### Deep Translator (Gratis)
- No requiere API key
- Usa Google Translate de forma gratuita
- Buena calidad para la mayoría de textos

#### Google Cloud Translate
- $300 de crédito gratuito + 500,000 caracteres/mes gratis
- Excelente calidad
- Requiere cuenta de Google Cloud

#### DeepL
- Mejor calidad de traducción
- Requiere API key de pago ($25/mes plan básico)
- Ideal para textos técnicos

## 📈 Rendimiento

Para un archivo de ~30,000 unidades de traducción:

| API | Velocidad | Tiempo Estimado | Costo |
|-----|-----------|-----------------|-------|
| Deep Translator | ~1-2 unidades/seg | 4-8 horas | Gratis |
| Google Translate | ~2-4 unidades/seg | 2-4 horas | ~$0.10-0.20 |
| DeepL | ~3-5 unidades/seg | 1-3 horas | ~$25-50/mes |

## 🛠️ Solución de Problemas

### El proceso se detuvo
```bash
# Reiniciar (continuará desde el checkpoint)
python3 traductor_simple.py archivo.xliff
```

### Traducciones de baja calidad
```bash
# Usar DeepL en lugar del traductor simple
python3 traductor_xliff.py archivo.xliff --api deepl --api-key TU_KEY
```

### Verificar que está funcionando
```bash
bash VERIFICAR_AHORA.sh
```

## 📝 Ejemplos de Traducciones

| Inglés | Catalán |
|--------|---------|
| Display modality | Modalitat de visualització |
| Hide the catalog | Amaga el catàleg |
| Show the catalog in a dedicated page | Mostra el catàleg en una pàgina dedicada |
| Use categories tree | Utilitzeu l'arbre de categories |
| General catalog sorting direction | Direcció general de classificació del catàleg |

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👏 Agradecimientos

- [deep-translator](https://github.com/nidhaloff/deep-translator) - Librería de traducción gratuita
- [Google Cloud Translation](https://cloud.google.com/translate) - API de Google Translate
- [DeepL](https://www.deepl.com/) - API de DeepL
- [tqdm](https://github.com/tqdm/tqdm) - Barra de progreso

## 📞 Soporte

Para preguntas, problemas o sugerencias:

- Abre un [Issue](https://github.com/TU_USUARIO/traductor-xliff/issues)
- Consulta la [Documentación completa](README.md)

---

**Creado con ❤️ para facilitar la traducción de archivos XLIFF**

