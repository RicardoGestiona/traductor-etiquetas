#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Esquema de base de datos SQLite para el sistema de traduccion.

Tablas:
- traducciones: Registro de sesiones de traduccion
- cache_traducciones: Cache global de traducciones por idioma
"""

# Esquema SQL para crear las tablas
SCHEMA_SQL = """
-- Tabla de sesiones de traduccion
CREATE TABLE IF NOT EXISTS traducciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idioma_origen TEXT NOT NULL,
    idioma_destino TEXT NOT NULL,
    nombre_fichero_original TEXT NOT NULL,
    nombre_fichero_destino TEXT NOT NULL,
    fecha_traduccion DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_etiquetas_fichero_original INTEGER DEFAULT 0,
    total_etiquetas_traducidas INTEGER DEFAULT 0,
    total_etiquetas_nuevas INTEGER DEFAULT 0,
    total_etiquetas_reutilizadas INTEGER DEFAULT 0,
    duracion_segundos REAL DEFAULT 0,
    estado TEXT DEFAULT 'completado'
);

-- Indices para busquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_traducciones_idioma_destino
ON traducciones(idioma_destino);

CREATE INDEX IF NOT EXISTS idx_traducciones_fecha
ON traducciones(fecha_traduccion);

-- Cache global de traducciones
CREATE TABLE IF NOT EXISTS cache_traducciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idioma_destino TEXT NOT NULL,
    hash_origen TEXT NOT NULL,
    texto_origen TEXT NOT NULL,
    texto_traducido TEXT NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    veces_usado INTEGER DEFAULT 1,
    UNIQUE(idioma_destino, hash_origen)
);

-- Indices para el cache
CREATE INDEX IF NOT EXISTS idx_cache_idioma_hash
ON cache_traducciones(idioma_destino, hash_origen);

CREATE INDEX IF NOT EXISTS idx_cache_idioma
ON cache_traducciones(idioma_destino);

-- Tabla de metadatos del sistema
CREATE TABLE IF NOT EXISTS metadatos (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insertar version del esquema
INSERT OR REPLACE INTO metadatos (clave, valor)
VALUES ('schema_version', '1.0.0');
"""

# Consultas SQL frecuentes
QUERIES = {
    # Cache de traducciones
    "buscar_cache": """
        SELECT texto_traducido
        FROM cache_traducciones
        WHERE idioma_destino = ? AND hash_origen = ?
    """,

    "insertar_cache": """
        INSERT OR REPLACE INTO cache_traducciones
        (idioma_destino, hash_origen, texto_origen, texto_traducido, veces_usado)
        VALUES (?, ?, ?, ?,
            COALESCE((SELECT veces_usado + 1 FROM cache_traducciones
                      WHERE idioma_destino = ? AND hash_origen = ?), 1))
    """,

    "actualizar_uso_cache": """
        UPDATE cache_traducciones
        SET veces_usado = veces_usado + 1
        WHERE idioma_destino = ? AND hash_origen = ?
    """,

    # Sesiones de traduccion
    "insertar_traduccion": """
        INSERT INTO traducciones
        (idioma_origen, idioma_destino, nombre_fichero_original, nombre_fichero_destino,
         total_etiquetas_fichero_original, total_etiquetas_traducidas,
         total_etiquetas_nuevas, total_etiquetas_reutilizadas, duracion_segundos, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,

    "obtener_estadisticas_idioma": """
        SELECT
            COUNT(*) as total_sesiones,
            SUM(total_etiquetas_traducidas) as total_traducciones,
            SUM(total_etiquetas_nuevas) as total_nuevas,
            SUM(total_etiquetas_reutilizadas) as total_reutilizadas,
            MAX(fecha_traduccion) as ultima_traduccion
        FROM traducciones
        WHERE idioma_destino = ?
    """,

    "obtener_estadisticas_globales": """
        SELECT
            idioma_destino,
            COUNT(*) as sesiones,
            SUM(total_etiquetas_traducidas) as traducciones,
            MAX(fecha_traduccion) as ultima
        FROM traducciones
        GROUP BY idioma_destino
        ORDER BY ultima DESC
    """,

    "contar_cache_por_idioma": """
        SELECT idioma_destino, COUNT(*) as total
        FROM cache_traducciones
        GROUP BY idioma_destino
    """,

    # Historial
    "obtener_historial": """
        SELECT * FROM traducciones
        ORDER BY fecha_traduccion DESC
        LIMIT ?
    """,
}
