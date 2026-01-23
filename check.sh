#!/bin/bash
# Verificación rápida del proceso

echo "🔍 VERIFICACIÓN RÁPIDA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar proceso
if ps aux | grep "traductor_simple.py xliff-english.xliff" | grep -v grep > /dev/null; then
    echo "✅ Proceso: ACTIVO"
    PID=$(ps aux | grep "traductor_simple.py xliff-english.xliff" | grep -v grep | awk '{print $2}')
    echo "   PID: $PID"
    
    # Tiempo que lleva corriendo
    TIEMPO=$(ps -p $PID -o etime= | xargs)
    echo "   Tiempo ejecutándose: $TIEMPO"
else
    echo "❌ Proceso: DETENIDO"
    exit 1
fi

# Verificar checkpoint
if [ -f "checkpoint_simple.json" ]; then
    TRADUCIDAS=$(grep -o '"' checkpoint_simple.json | wc -l)
    TRADUCIDAS=$((TRADUCIDAS / 4))
    TOTAL=28907
    PORCENTAJE=$(echo "scale=2; ($TRADUCIDAS / $TOTAL) * 100" | bc)
    
    echo "✅ Checkpoint: PRESENTE"
    echo "   Progreso: $TRADUCIDAS / $TOTAL ($PORCENTAJE%)"
    
    # Última modificación del checkpoint
    ULTIMA_MOD=$(stat -f "%Sm" -t "%H:%M:%S" checkpoint_simple.json)
    echo "   Última actualización: $ULTIMA_MOD"
else
    echo "⏳ Checkpoint: INICIANDO"
fi

echo ""
echo "💡 Para ver progreso detallado: bash ver_progreso.sh"
echo "💡 Para verificar que avanza: bash verificar_proceso.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

