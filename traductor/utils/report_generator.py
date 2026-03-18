#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de informes de traduccion.

Genera informes en formato Markdown con detalles de errores y estadisticas.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from traductor.database.db_manager import DatabaseManager


@dataclass
class ErrorTraduccion:
    """Representa un error de traduccion."""
    idioma: str
    texto_origen: str
    motivo: str
    archivo: str
    fecha: str
    reintentos: int


class ReportGenerator:
    """Generador de informes de traduccion."""

    def __init__(self, db_path: str = "traductor.db", output_dir: str = "informes"):
        """
        Inicializa el generador de informes.

        Args:
            db_path: Ruta a la base de datos SQLite
            output_dir: Directorio para guardar informes
        """
        self.db = DatabaseManager(db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generar_informe_errores(self, archivo_salida: Optional[str] = None) -> str:
        """
        Genera informe de errores pendientes.

        Args:
            archivo_salida: Nombre del archivo (opcional, se genera automaticamente)

        Returns:
            Ruta al archivo generado
        """
        if archivo_salida is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_salida = f"informe_errores_{timestamp}.md"

        ruta_salida = self.output_dir / archivo_salida
        errores = self._obtener_errores_pendientes()
        contenido = self._generar_markdown_errores(errores)

        ruta_salida.write_text(contenido, encoding="utf-8")
        return str(ruta_salida)

    def _obtener_errores_pendientes(self) -> List[ErrorTraduccion]:
        """Obtiene errores pendientes de la base de datos."""
        rows = self.db.obtener_errores_pendientes_detallado()
        return [
            ErrorTraduccion(
                idioma=row["idioma_destino"],
                texto_origen=row["texto_origen"] or "(vacio)",
                motivo=row["motivo_fallo"],
                archivo=row["archivo_origen"],
                fecha=row["fecha_fallo"],
                reintentos=row["reintentos"]
            )
            for row in rows
        ]

    def _generar_markdown_errores(self, errores: List[ErrorTraduccion]) -> str:
        """Genera contenido Markdown del informe de errores."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        secciones = [
            self._generar_cabecera(timestamp, len(errores)),
            self._generar_resumen_por_tipo(errores),
            self._generar_resumen_por_idioma(errores),
            self._generar_detalle_errores(errores),
            self._generar_guia_solucion()
        ]

        return "\n".join(secciones)

    def _generar_cabecera(self, timestamp: str, total: int) -> str:
        """Genera cabecera del informe."""
        return f"""# Informe de Errores de Traduccion

**Generado:** {timestamp}
**Total de errores pendientes:** {total}

---
"""

    def _generar_resumen_por_tipo(self, errores: List[ErrorTraduccion]) -> str:
        """Genera resumen agrupado por tipo de error."""
        tipos = {}
        for e in errores:
            tipos[e.motivo] = tipos.get(e.motivo, 0) + 1

        if not tipos:
            return "## Resumen por Tipo de Error\n\nNo hay errores pendientes.\n"

        lineas = ["## Resumen por Tipo de Error\n"]
        lineas.append("| Tipo de Error | Cantidad |")
        lineas.append("|---------------|----------|")

        for motivo, cantidad in sorted(tipos.items(), key=lambda x: -x[1]):
            lineas.append(f"| {motivo} | {cantidad} |")

        lineas.append("")
        return "\n".join(lineas)

    def _generar_resumen_por_idioma(self, errores: List[ErrorTraduccion]) -> str:
        """Genera resumen agrupado por idioma."""
        idiomas = {}
        for e in errores:
            idiomas[e.idioma] = idiomas.get(e.idioma, 0) + 1

        if not idiomas:
            return ""

        lineas = ["## Resumen por Idioma\n"]
        lineas.append("| Idioma | Errores |")
        lineas.append("|--------|---------|")

        nombres = {"ca": "Catalan", "eu": "Euskera", "gl": "Gallego"}
        for codigo, cantidad in sorted(idiomas.items()):
            nombre = nombres.get(codigo, codigo)
            lineas.append(f"| {nombre} ({codigo}) | {cantidad} |")

        lineas.append("")
        return "\n".join(lineas)

    def _generar_detalle_errores(self, errores: List[ErrorTraduccion]) -> str:
        """Genera detalle de cada error."""
        if not errores:
            return "## Detalle de Errores\n\nNo hay errores para mostrar.\n"

        lineas = ["## Detalle de Errores\n"]

        for i, e in enumerate(errores[:50], 1):  # Limitar a 50 para legibilidad
            texto_truncado = self._truncar_texto(e.texto_origen, 100)
            lineas.append(f"### Error {i}")
            lineas.append(f"- **Idioma:** {e.idioma}")
            lineas.append(f"- **Motivo:** {e.motivo}")
            lineas.append(f"- **Archivo:** `{e.archivo}`")
            lineas.append(f"- **Fecha:** {e.fecha}")
            lineas.append(f"- **Reintentos:** {e.reintentos}")
            lineas.append(f"- **Texto origen:** `{texto_truncado}`")
            lineas.append("")

        if len(errores) > 50:
            lineas.append(f"*... y {len(errores) - 50} errores mas no mostrados.*\n")

        return "\n".join(lineas)

    def _truncar_texto(self, texto: str, max_len: int) -> str:
        """Trunca texto para mostrar en informe."""
        if len(texto) <= max_len:
            return texto
        return texto[:max_len] + "..."

    def _generar_guia_solucion(self) -> str:
        """Genera guia de solucion de errores."""
        return """## Guia de Solucion

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
"""

    def generar_informe_sesion(
        self,
        resultados: list,
        archivo_salida: Optional[str] = None
    ) -> str:
        """
        Genera informe de una sesion de traduccion.

        Args:
            resultados: Lista de ResultadoTraduccion o ResultadoProcesamiento
            archivo_salida: Nombre del archivo (opcional)

        Returns:
            Ruta al archivo generado
        """
        if archivo_salida is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_salida = f"informe_sesion_{timestamp}.md"

        ruta_salida = self.output_dir / archivo_salida
        contenido = self._generar_markdown_sesion(resultados)

        ruta_salida.write_text(contenido, encoding="utf-8")
        return str(ruta_salida)

    def _generar_markdown_sesion(self, resultados: list) -> str:
        """Genera Markdown para informe de sesion."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        exitosos = sum(1 for r in resultados if getattr(r, 'exitoso', True))
        con_errores = len(resultados) - exitosos

        lineas = [
            f"# Informe de Sesion de Traduccion\n",
            f"**Fecha:** {timestamp}\n",
            f"## Resumen\n",
            f"- **Total procesados:** {len(resultados)}",
            f"- **Exitosos:** {exitosos}",
            f"- **Con errores:** {con_errores}\n",
            "## Detalle por Archivo\n"
        ]

        for r in resultados:
            estado = "OK" if getattr(r, 'exitoso', True) else "ERROR"
            lineas.append(f"### {estado}: {getattr(r, 'archivo_origen', 'N/A')}\n")

            if hasattr(r, 'idiomas_procesados'):
                lineas.append(f"- Idiomas: {', '.join(r.idiomas_procesados)}")

            if hasattr(r, 'total_etiquetas'):
                lineas.append(f"- Total etiquetas: {r.total_etiquetas}")
                lineas.append(f"- Nuevas: {r.nuevas}")
                lineas.append(f"- Reutilizadas: {r.reutilizadas}")

            if hasattr(r, 'errores') and r.errores:
                if isinstance(r.errores, int) and r.errores > 0:
                    lineas.append(f"- **Errores:** {r.errores}")
                elif isinstance(r.errores, list):
                    for err in r.errores:
                        lineas.append(f"- **Error:** {err}")

            lineas.append("")

        return "\n".join(lineas)
