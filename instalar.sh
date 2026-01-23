#!/bin/bash

# Script de instalación rápida para el Traductor XLIFF

echo "🚀 Instalador del Traductor XLIFF"
echo "=================================="
echo ""

# Verificar Python
echo "📋 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    echo "Por favor instala Python 3.7 o superior"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION encontrado"
echo ""

# Verificar pip
echo "📋 Verificando pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip no está instalado"
    exit 1
fi
echo "✅ pip encontrado"
echo ""

# Preguntar qué opción instalar
echo "¿Qué traductor deseas instalar?"
echo ""
echo "1) Traductor Simple (GRATIS, sin API key, recomendado para empezar)"
echo "2) Google Translate API (requiere configuración)"
echo "3) DeepL API (mejor calidad, requiere API key de pago)"
echo "4) Instalar todo (todas las opciones)"
echo ""
read -p "Selecciona una opción (1-4): " opcion

case $opcion in
    1)
        echo ""
        echo "📦 Instalando traductor simple..."
        pip3 install deep-translator tqdm
        echo ""
        echo "✅ ¡Instalación completada!"
        echo ""
        echo "Para empezar a traducir ejecuta:"
        echo "  python3 traductor_simple.py xliff-english.xliff"
        ;;
    2)
        echo ""
        echo "📦 Instalando Google Translate API..."
        pip3 install google-cloud-translate tqdm
        echo ""
        echo "✅ ¡Instalación completada!"
        echo ""
        echo "⚠️  IMPORTANTE: Necesitas configurar las credenciales de Google Cloud"
        echo "Lee el archivo README.md para más detalles"
        echo ""
        echo "Después ejecuta:"
        echo "  python3 traductor_xliff.py xliff-english.xliff"
        ;;
    3)
        echo ""
        echo "📦 Instalando DeepL API..."
        pip3 install deepl tqdm
        echo ""
        echo "✅ ¡Instalación completada!"
        echo ""
        echo "⚠️  IMPORTANTE: Necesitas una API key de DeepL"
        echo "Regístrate en: https://www.deepl.com/pro-api"
        echo ""
        echo "Después ejecuta:"
        echo "  python3 traductor_xliff.py xliff-english.xliff --api deepl --api-key TU_API_KEY"
        ;;
    4)
        echo ""
        echo "📦 Instalando todas las opciones..."
        pip3 install -r requirements.txt
        echo ""
        echo "✅ ¡Instalación completada!"
        echo ""
        echo "Lee README.md o INICIO_RAPIDO.md para ver cómo usar cada opción"
        ;;
    *)
        echo ""
        echo "❌ Opción no válida"
        exit 1
        ;;
esac

echo ""
echo "📖 Documentación disponible:"
echo "   - INICIO_RAPIDO.md (guía rápida)"
echo "   - README.md (documentación completa)"
echo ""
echo "¡Buena suerte con tu traducción! 🎉"

