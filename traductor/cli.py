#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI unificado para el sistema de traduccion XLIFF.

Comandos disponibles:
- procesar: Procesa archivos en traduccion-pendiente/ a catalan, gallego y euskera
- traducir: Traduce un archivo XLIFF a uno o mas idiomas
- pendientes: Lista traducciones pendientes (fallidas)
- reintentar: Reintenta traducciones pendientes
- migrar-checkpoints: Migra checkpoints JSON legacy a SQLite
- estadisticas: Muestra estadisticas del sistema
- listar: Lista traducciones e idiomas disponibles
"""

import argparse
import os
import sys
from typing import List, Optional

from traductor import __version__
from traductor.config.idiomas import listar_idiomas, obtener_config_idioma, IDIOMAS_SOPORTADOS
from traductor.database.db_manager import DatabaseManager
from traductor.database.migrations import CheckpointMigrator
from traductor.services.translation_service import TranslationService
from traductor.services.batch_processor import BatchProcessor
from traductor.utils.logger import get_logger


def cmd_traducir(args: argparse.Namespace) -> int:
    """Comando para traducir archivos XLIFF."""
    logger = get_logger()

    # Validar archivo de entrada
    if not os.path.exists(args.archivo):
        logger.error(f"El archivo '{args.archivo}' no existe")
        return 1

    # Validar idiomas
    idiomas_validos = []
    for idioma in args.idioma:
        config = obtener_config_idioma(idioma)
        if config is None:
            logger.error(f"Idioma no soportado: {idioma}")
            logger.info(f"Idiomas disponibles: {', '.join(listar_idiomas())}")
            return 1
        idiomas_validos.append(idioma)

    try:
        service = TranslationService(
            db_path=args.db,
            base_dir_salida=args.output_dir
        )

        if len(idiomas_validos) == 1:
            resultado = service.traducir(
                args.archivo,
                idiomas_validos[0],
                archivo_salida=args.output,
                forzar_retraduccion=args.forzar
            )
            return 0 if resultado.exitoso else 1
        else:
            resultados = service.traducir_multiples_idiomas(
                args.archivo,
                idiomas_validos,
                forzar_retraduccion=args.forzar
            )
            exitosos = sum(1 for r in resultados if r.exitoso)
            logger.info(f"\nResumen: {exitosos}/{len(resultados)} traducciones exitosas")
            return 0 if exitosos == len(resultados) else 1

    except KeyboardInterrupt:
        logger.info("\nProceso interrumpido por el usuario")
        logger.info("El progreso se ha guardado en la base de datos.")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


def cmd_procesar(args: argparse.Namespace) -> int:
    """Comando para procesar archivos pendientes."""
    logger = get_logger()

    processor = BatchProcessor(
        carpeta_entrada=args.entrada,
        carpeta_salida=args.salida,
        db_path=args.db,
        mover_procesados=not args.no_mover
    )

    if args.watch:
        logger.info("Modo watcher activado")
        processor.watch(intervalo=args.intervalo)
        return 0
    else:
        resultados = processor.procesar_todos()
        exitosos = sum(1 for r in resultados if r.exitoso)
        return 0 if exitosos == len(resultados) or len(resultados) == 0 else 1


def cmd_migrar_checkpoints(args: argparse.Namespace) -> int:
    """Comando para migrar checkpoints JSON a SQLite."""
    logger = get_logger()
    logger.info("Migrando checkpoints JSON a base de datos SQLite...")

    db = DatabaseManager(args.db)
    migrador = CheckpointMigrator(db, args.directorio)

    # Verificar estado actual
    estado = migrador.verificar_migracion()
    if not estado["checkpoints_pendientes"]:
        logger.info("No hay checkpoints pendientes de migrar.")
        if estado["cache_por_idioma"]:
            logger.info("\nCache existente por idioma:")
            for idioma, total in estado["cache_por_idioma"].items():
                logger.info(f"  - {idioma}: {total} traducciones")
        return 0

    logger.info(f"Checkpoints encontrados: {', '.join(estado['checkpoints_pendientes'])}")

    # Ejecutar migracion
    resultados = migrador.migrar_todos(archivar=not args.no_archivar)

    logger.info("\nMigracion completada:")
    for idioma, total in resultados.items():
        logger.info(f"  - {idioma}: {total} traducciones migradas")

    return 0


def cmd_estadisticas(args: argparse.Namespace) -> int:
    """Comando para mostrar estadisticas."""
    logger = get_logger()
    db = DatabaseManager(args.db)

    logger.info("=== Estadisticas del Sistema de Traduccion ===\n")

    # Cache por idioma
    cache = db.obtener_conteo_cache()
    if cache:
        logger.info("Cache de traducciones:")
        for idioma, total in cache.items():
            config = None
            for nombre, cfg in IDIOMAS_SOPORTADOS.items():
                if cfg.codigo == idioma:
                    config = cfg
                    break
            nombre_idioma = config.nombre if config else idioma
            logger.info(f"  - {nombre_idioma} ({idioma}): {total} traducciones")
    else:
        logger.info("Cache de traducciones: vacio")

    # Estadisticas por idioma
    logger.info("\nSesiones de traduccion:")
    stats = db.obtener_estadisticas_globales()
    if stats:
        for stat in stats:
            logger.info(f"  - {stat['idioma_destino']}: {stat['sesiones']} sesiones, "
                       f"{stat['traducciones']} traducciones")
    else:
        logger.info("  No hay sesiones registradas")

    # Historial reciente
    logger.info("\nHistorial reciente:")
    historial = db.obtener_historial(5)
    if historial:
        for h in historial:
            logger.info(f"  [{h['fecha_traduccion']}] {h['idioma_destino']}: "
                       f"{h['total_etiquetas_nuevas']} nuevas, "
                       f"{h['total_etiquetas_reutilizadas']} reutilizadas")
    else:
        logger.info("  Sin historial")

    return 0


def cmd_listar(args: argparse.Namespace) -> int:
    """Comando para listar idiomas o traducciones."""
    logger = get_logger()

    if args.tipo == "idiomas":
        logger.info("Idiomas soportados:\n")
        for nombre, config in IDIOMAS_SOPORTADOS.items():
            logger.info(f"  {nombre:<12} ({config.codigo}) - {config.nombre}")
    elif args.tipo == "traducciones":
        from traductor.utils.file_naming import FileNaming
        fn = FileNaming(args.output_dir)

        logger.info("Traducciones existentes:\n")
        for nombre, config in IDIOMAS_SOPORTADOS.items():
            archivos = fn.listar_traducciones(config)
            if archivos:
                logger.info(f"  {config.nombre} ({config.codigo}):")
                for archivo in archivos[-3:]:  # Ultimos 3
                    logger.info(f"    - {os.path.basename(archivo)}")

    return 0


def cmd_pendientes(args: argparse.Namespace) -> int:
    """Comando para listar traducciones pendientes."""
    logger = get_logger()
    db = DatabaseManager(args.db)

    # Obtener conteo por idioma
    conteo = db.contar_pendientes()

    if not conteo:
        logger.info("No hay traducciones pendientes.")
        return 0

    logger.info("=== Traducciones Pendientes ===\n")

    total_general = 0
    for idioma, total in conteo.items():
        config = None
        for nombre, cfg in IDIOMAS_SOPORTADOS.items():
            if cfg.codigo == idioma:
                config = cfg
                break
        nombre_idioma = config.nombre if config else idioma
        logger.info(f"  {nombre_idioma} ({idioma}): {total} pendientes")
        total_general += total

    logger.info(f"\nTotal: {total_general} traducciones pendientes")

    # Mostrar detalle si se solicita
    if args.detalle:
        idioma_filtro = args.idioma if args.idioma else None
        pendientes = db.obtener_pendientes(idioma_filtro)

        if pendientes:
            logger.info("\nDetalle de pendientes:")
            for p in pendientes[:args.limite]:
                texto_corto = p['texto_origen'][:60] + "..." if len(p['texto_origen']) > 60 else p['texto_origen']
                logger.info(f"  [{p['idioma_destino']}] {texto_corto}")
                logger.info(f"       Motivo: {p['motivo_fallo']}")
                logger.info(f"       Reintentos: {p['reintentos']}")

    return 0


def cmd_reintentar(args: argparse.Namespace) -> int:
    """Comando para reintentar traducciones pendientes."""
    from traductor.core.base_translator import crear_traductor

    logger = get_logger()
    db = DatabaseManager(args.db)

    # Obtener pendientes
    idioma_filtro = args.idioma if args.idioma else None
    pendientes = db.obtener_pendientes(idioma_filtro)

    if not pendientes:
        logger.info("No hay traducciones pendientes para reintentar.")
        return 0

    logger.info(f"Reintentando {len(pendientes)} traducciones pendientes...\n")

    # Agrupar por idioma
    por_idioma = {}
    for p in pendientes:
        idioma = p['idioma_destino']
        if idioma not in por_idioma:
            por_idioma[idioma] = []
        por_idioma[idioma].append(p)

    total_exito = 0
    total_fallo = 0

    for idioma, lista_pendientes in por_idioma.items():
        config = obtener_config_idioma(idioma)
        if not config:
            # Buscar por codigo
            for nombre, cfg in IDIOMAS_SOPORTADOS.items():
                if cfg.codigo == idioma:
                    config = cfg
                    break

        if not config:
            logger.error(f"No se encontro configuracion para idioma: {idioma}")
            continue

        logger.info(f"Procesando {len(lista_pendientes)} pendientes para {config.nombre}...")

        traductor = crear_traductor(tipo="google", config_destino=config)

        for p in lista_pendientes:
            texto_origen = p['texto_origen']
            try:
                traduccion = traductor.traducir(texto_origen)

                if traduccion and traduccion.strip() and traduccion != texto_origen:
                    # Exito: guardar en cache y eliminar de pendientes
                    db.guardar_en_cache(idioma, texto_origen, traduccion)
                    db.eliminar_pendiente(idioma, texto_origen)
                    total_exito += 1
                    logger.info(f"  OK: {texto_origen[:40]}...")
                else:
                    total_fallo += 1
                    logger.warning(f"  FALLO: {texto_origen[:40]}...")

            except Exception as e:
                total_fallo += 1
                logger.error(f"  ERROR: {texto_origen[:40]}... - {e}")

    logger.info(f"\nResultado: {total_exito} exitosas, {total_fallo} fallidas")

    return 0 if total_fallo == 0 else 1


def cmd_limpiar_pendientes(args: argparse.Namespace) -> int:
    """Comando para limpiar traducciones pendientes."""
    logger = get_logger()
    db = DatabaseManager(args.db)

    idioma_filtro = args.idioma if args.idioma else None

    if idioma_filtro:
        eliminados = db.limpiar_pendientes(idioma_filtro)
        logger.info(f"Eliminadas {eliminados} traducciones pendientes de {idioma_filtro}")
    else:
        eliminados = db.limpiar_pendientes()
        logger.info(f"Eliminadas {eliminados} traducciones pendientes (todos los idiomas)")

    return 0


def crear_parser() -> argparse.ArgumentParser:
    """Crea el parser de argumentos."""
    parser = argparse.ArgumentParser(
        prog="python -m traductor",
        description="Sistema de traduccion XLIFF para Docebo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m traductor procesar                    # Procesa archivos pendientes
  python -m traductor procesar --watch            # Vigila carpeta continuamente
  python -m traductor traducir archivo.xliff --idioma catalan
  python -m traductor traducir archivo.xliff --idioma catalan euskera gallego
  python -m traductor pendientes                  # Lista traducciones fallidas
  python -m traductor pendientes --detalle        # Muestra detalle de pendientes
  python -m traductor reintentar                  # Reintenta todas las pendientes
  python -m traductor reintentar --idioma ca      # Reintenta solo catalan
  python -m traductor estadisticas
  python -m traductor listar idiomas
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "--db",
        default="traductor.db",
        help="Ruta a la base de datos SQLite (default: traductor.db)"
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comando a ejecutar")

    # Comando: procesar
    p_procesar = subparsers.add_parser(
        "procesar",
        help="Procesa archivos en traduccion-pendiente/",
        description="Traduce automaticamente archivos XLIFF a catalan, gallego y euskera"
    )
    p_procesar.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Modo vigilancia: monitorea carpeta continuamente"
    )
    p_procesar.add_argument(
        "--intervalo",
        type=int,
        default=10,
        help="Segundos entre verificaciones en modo watch (default: 10)"
    )
    p_procesar.add_argument(
        "--entrada",
        default="traduccion-pendiente",
        help="Carpeta de entrada (default: traduccion-pendiente)"
    )
    p_procesar.add_argument(
        "--salida",
        default="traducidos",
        help="Carpeta de salida (default: traducidos)"
    )
    p_procesar.add_argument(
        "--no-mover",
        action="store_true",
        help="No mover archivos procesados a _procesados/"
    )
    p_procesar.set_defaults(func=cmd_procesar)

    # Comando: traducir
    p_traducir = subparsers.add_parser(
        "traducir",
        help="Traduce un archivo XLIFF",
        description="Traduce un archivo XLIFF a uno o mas idiomas destino"
    )
    p_traducir.add_argument(
        "archivo",
        help="Archivo XLIFF a traducir"
    )
    p_traducir.add_argument(
        "--idioma", "-i",
        nargs="+",
        required=True,
        help="Idioma(s) destino (ej: catalan euskera gallego)"
    )
    p_traducir.add_argument(
        "--output", "-o",
        help="Archivo de salida (solo para un idioma)"
    )
    p_traducir.add_argument(
        "--output-dir",
        default="Idiomas",
        help="Directorio base para archivos traducidos (default: Idiomas)"
    )
    p_traducir.add_argument(
        "--forzar", "-f",
        action="store_true",
        help="Forzar retraduccion (ignorar cache)"
    )
    p_traducir.set_defaults(func=cmd_traducir)

    # Comando: migrar-checkpoints
    p_migrar = subparsers.add_parser(
        "migrar-checkpoints",
        help="Migra checkpoints JSON legacy a SQLite",
        description="Busca archivos checkpoint_*.json y migra su contenido a la base de datos"
    )
    p_migrar.add_argument(
        "--directorio", "-d",
        default=".",
        help="Directorio donde buscar checkpoints (default: .)"
    )
    p_migrar.add_argument(
        "--no-archivar",
        action="store_true",
        help="No mover checkpoints migrados a legacy/"
    )
    p_migrar.set_defaults(func=cmd_migrar_checkpoints)

    # Comando: estadisticas
    p_stats = subparsers.add_parser(
        "estadisticas",
        help="Muestra estadisticas del sistema",
        description="Muestra estadisticas de cache, sesiones y traducciones"
    )
    p_stats.set_defaults(func=cmd_estadisticas)

    # Comando: listar
    p_listar = subparsers.add_parser(
        "listar",
        help="Lista idiomas o traducciones",
        description="Lista idiomas soportados o traducciones existentes"
    )
    p_listar.add_argument(
        "tipo",
        choices=["idiomas", "traducciones"],
        help="Que listar: idiomas soportados o traducciones existentes"
    )
    p_listar.add_argument(
        "--output-dir",
        default="Idiomas",
        help="Directorio de traducciones (default: Idiomas)"
    )
    p_listar.set_defaults(func=cmd_listar)

    # Comando: pendientes
    p_pendientes = subparsers.add_parser(
        "pendientes",
        help="Lista traducciones pendientes (fallidas)",
        description="Muestra traducciones que fallaron y estan pendientes de reintentar"
    )
    p_pendientes.add_argument(
        "--idioma", "-i",
        help="Filtrar por codigo de idioma (ej: ca, eu, gl)"
    )
    p_pendientes.add_argument(
        "--detalle", "-d",
        action="store_true",
        help="Mostrar detalle de cada traduccion pendiente"
    )
    p_pendientes.add_argument(
        "--limite", "-l",
        type=int,
        default=20,
        help="Limite de registros a mostrar en detalle (default: 20)"
    )
    p_pendientes.set_defaults(func=cmd_pendientes)

    # Comando: reintentar
    p_reintentar = subparsers.add_parser(
        "reintentar",
        help="Reintenta traducciones pendientes",
        description="Reintenta traducir las etiquetas que fallaron anteriormente"
    )
    p_reintentar.add_argument(
        "--idioma", "-i",
        help="Filtrar por codigo de idioma (ej: ca, eu, gl)"
    )
    p_reintentar.set_defaults(func=cmd_reintentar)

    # Comando: limpiar-pendientes
    p_limpiar = subparsers.add_parser(
        "limpiar-pendientes",
        help="Elimina traducciones pendientes",
        description="Elimina traducciones pendientes de la base de datos"
    )
    p_limpiar.add_argument(
        "--idioma", "-i",
        help="Filtrar por codigo de idioma (ej: ca, eu, gl)"
    )
    p_limpiar.set_defaults(func=cmd_limpiar_pendientes)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Funcion principal del CLI."""
    parser = crear_parser()
    args = parser.parse_args(argv)

    if args.comando is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
