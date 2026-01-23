# Traductor de Archivos XLIFF

Aplicación para traducir archivos XLIFF del inglés al catalán de forma automática usando APIs de traducción profesionales.

## 🚀 Características

- ✅ Traducción automática inglés → catalán
- ✅ Soporte para Google Translate API y DeepL API
- ✅ Sistema de checkpoints (guarda el progreso automáticamente)
- ✅ Reintentos automáticos en caso de errores
- ✅ Barra de progreso visual
- ✅ Preserva la estructura y formato del archivo XLIFF original
- ✅ Manejo de CDATA sections
- ✅ Reinicio desde donde se quedó si se interrumpe

## 📋 Requisitos

- Python 3.7 o superior
- Una cuenta de Google Cloud (para Google Translate) o una API key de DeepL

## 🔧 Instalación

### 1. Instalar dependencias básicas

```bash
pip install -r requirements.txt
```

### 2. Configurar la API de traducción

#### Opción A: Google Cloud Translate (Recomendado para empezar)

Google ofrece $300 de crédito gratuito y 500,000 caracteres gratis al mes.

1. Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com)
2. Activa la API de Cloud Translation
3. Crea una cuenta de servicio y descarga el archivo JSON de credenciales
4. Guarda la ruta al archivo JSON (la necesitarás al ejecutar)

**Instalación solo de Google Translate:**
```bash
pip install google-cloud-translate tqdm
```

#### Opción B: DeepL (Mejor calidad, de pago)

DeepL ofrece traducciones de mayor calidad pero requiere una API key de pago.

1. Regístrate en [DeepL API](https://www.deepl.com/pro-api)
2. Obtén tu API key
3. Guarda la API key (la necesitarás al ejecutar)

**Instalación solo de DeepL:**
```bash
pip install deepl tqdm
```

## 📖 Uso

### Uso básico con Google Translate

```bash
python traductor_xliff.py xliff-english.xliff
```

Esto creará un archivo `xliff-english_ca.xliff` con las traducciones.

### Con nombre de archivo personalizado

```bash
python traductor_xliff.py xliff-english.xliff -o xliff-catalan.xliff
```

### Usando DeepL

```bash
python traductor_xliff.py xliff-english.xliff --api deepl --api-key TU_API_KEY_AQUI
```

### Con Google Translate especificando credenciales

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/ruta/a/tu/credenciales.json"
python traductor_xliff.py xliff-english.xliff
```

O directamente:

```bash
python traductor_xliff.py xliff-english.xliff --api google --api-key /ruta/a/credenciales.json
```

### Opciones avanzadas

```bash
python traductor_xliff.py archivo.xliff \
  -o salida.xliff \
  --api google \
  --checkpoint mi_progreso.json
```

## 🎯 Parámetros

- `archivo_entrada`: Archivo XLIFF a traducir (obligatorio)
- `-o, --output`: Archivo de salida (opcional, por defecto: `entrada_ca.xliff`)
- `--api`: API a usar: `google` o `deepl` (por defecto: `google`)
- `--api-key`: Ruta al archivo de credenciales (Google) o API key (DeepL)
- `--checkpoint`: Archivo para guardar el progreso (por defecto: `checkpoint.json`)

## 🔄 Sistema de Checkpoints

El script guarda automáticamente el progreso en un archivo `checkpoint.json`. Si el proceso se interrumpe (por error de conexión, límite de API, etc.), puedes ejecutar el mismo comando nuevamente y continuará desde donde se quedó.

### Ventajas del checkpoint:
- No pierdes el progreso si hay un error
- Puedes pausar y reanudar la traducción
- Evita volver a traducir unidades ya procesadas
- Ahorra dinero en llamadas a la API

## ⚙️ Cómo funciona

1. **Carga el archivo XLIFF** y analiza su estructura XML
2. **Encuentra todas las unidades de traducción** (`<trans-unit>`)
3. **Para cada unidad**:
   - Extrae el texto del elemento `<source>`
   - Verifica si ya fue traducido (checkpoint)
   - Si no, llama a la API de traducción
   - Guarda la traducción en el checkpoint
   - Actualiza el elemento `<target>` con la traducción
4. **Guarda el archivo** con todas las traducciones

## 📊 Estimación de costos

### Google Translate
- **Gratis**: $300 de crédito inicial + 500,000 caracteres/mes
- **Después**: $20 por cada millón de caracteres
- Para un archivo de 116,355 líneas (~5-10MB de texto): aproximadamente $0.10 - $0.20

### DeepL
- **Plan gratuito**: No disponible para API
- **Plan Pro**: $25/mes por 250,000 caracteres
- Para un archivo de 116,355 líneas: aproximadamente 1-2 meses del plan básico

## 🐛 Solución de problemas

### Error: "No module named 'google.cloud'"
```bash
pip install google-cloud-translate
```

### Error: "No module named 'deepl'"
```bash
pip install deepl
```

### Error de autenticación con Google
Asegúrate de que la variable de entorno esté configurada:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/ruta/completa/a/credenciales.json"
```

### El proceso es muy lento
- Es normal. Las APIs tienen límites de velocidad
- El script hace pausas automáticas para no saturar la API
- Para ~116,000 líneas, puede tomar varias horas
- Gracias al checkpoint, puedes pausar y reanudar cuando quieras

### Traducciones de baja calidad
- Considera usar DeepL en lugar de Google Translate
- DeepL generalmente ofrece mejor calidad para textos técnicos

## 📝 Notas adicionales

- El script preserva la estructura completa del XLIFF, incluyendo atributos y metadata
- Las secciones CDATA se mantienen correctamente
- Si una traducción falla, se mantiene el texto original en inglés
- El script muestra estadísticas al finalizar

## 🤝 Contribuciones

Si encuentras algún problema o tienes sugerencias de mejora, no dudes en modificar el código según tus necesidades.

## 📄 Licencia

Este código es de uso libre. Úsalo como quieras.

---

**¡Buena suerte con tu traducción! 🎉**

