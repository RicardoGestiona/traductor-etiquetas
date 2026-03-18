#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para insertar traducciones manuales en cache y limpiar pendientes.

Uso: python scripts/insertar_cache_manual.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from traductor.database.db_manager import DatabaseManager


# Textos originales exactos tal como aparecen en la BD (con HTML entities)
TEXTO_COACHING = (
    "&lt;strong&gt;{name}&lt;/strong&gt;'s coaching session "
    "(from &lt;strong&gt;{from}&lt;/strong&gt; to &lt;strong&gt;{to}&lt;/strong&gt;) "
    "has &lt;strong&gt;{number} users&lt;/strong&gt; assigned"
)

TEXTO_DELETE_ACCOUNT = (
    "Hello,&lt;br&gt;A user asked to delete their account within the mobile app."
    "&lt;br&gt;&lt;br&gt;Username: {username}&lt;br&gt;Name: {firstname} {lastname}"
    "&lt;br&gt;Email: {email}&lt;br&gt;&lt;br&gt;Please manage the account deletion request "
    "in accordance with the regulations in force in your country."
)

# Traducciones manuales preservando HTML entities y {placeholders}
TRADUCCIONES_MANUALES = [
    # --- Texto 1: Coaching session ---
    (
        "ca",
        TEXTO_COACHING,
        "La sessió de coaching de &lt;strong&gt;{name}&lt;/strong&gt; "
        "(de &lt;strong&gt;{from}&lt;/strong&gt; a &lt;strong&gt;{to}&lt;/strong&gt;) "
        "té &lt;strong&gt;{number} usuaris&lt;/strong&gt; assignats"
    ),
    (
        "eu",
        TEXTO_COACHING,
        "&lt;strong&gt;{name}&lt;/strong&gt;-(r)en coaching saioa "
        "(&lt;strong&gt;{from}&lt;/strong&gt;-(e)tik &lt;strong&gt;{to}&lt;/strong&gt;-(e)ra) "
        "&lt;strong&gt;{number} erabiltzaile&lt;/strong&gt; esleituta ditu"
    ),
    (
        "gl",
        TEXTO_COACHING,
        "A sesión de coaching de &lt;strong&gt;{name}&lt;/strong&gt; "
        "(de &lt;strong&gt;{from}&lt;/strong&gt; a &lt;strong&gt;{to}&lt;/strong&gt;) "
        "ten &lt;strong&gt;{number} usuarios&lt;/strong&gt; asignados"
    ),
    # --- Texto 2: Delete account ---
    (
        "ca",
        TEXTO_DELETE_ACCOUNT,
        "Hola,&lt;br&gt;Un usuari ha sol·licitat eliminar el seu compte "
        "des de l'aplicació mòbil.&lt;br&gt;&lt;br&gt;Nom d'usuari: {username}"
        "&lt;br&gt;Nom: {firstname} {lastname}&lt;br&gt;Correu electrònic: {email}"
        "&lt;br&gt;&lt;br&gt;Si us plau, gestioneu la sol·licitud d'eliminació "
        "del compte d'acord amb la normativa vigent al vostre país."
    ),
    (
        "gl",
        TEXTO_DELETE_ACCOUNT,
        "Ola,&lt;br&gt;Un usuario solicitou eliminar a súa conta "
        "desde a aplicación móbil.&lt;br&gt;&lt;br&gt;Nome de usuario: {username}"
        "&lt;br&gt;Nome: {firstname} {lastname}&lt;br&gt;Correo electrónico: {email}"
        "&lt;br&gt;&lt;br&gt;Por favor, xestione a solicitude de eliminación "
        "da conta de acordo coa normativa vixente no seu país."
    ),
]


def main():
    db = DatabaseManager("traductor.db")

    print("=== Insercion manual de traducciones en cache ===\n")

    for idioma, texto_origen, texto_traducido in TRADUCCIONES_MANUALES:
        db.guardar_en_cache(idioma, texto_origen, texto_traducido)
        db.eliminar_pendiente(idioma, texto_origen)
        print(f"  [OK] [{idioma}] {texto_origen[:60]}...")

    print(f"\n  Total: {len(TRADUCCIONES_MANUALES)} traducciones insertadas en cache")

    # Verificar que no quedan pendientes
    pendientes = db.contar_pendientes()
    if pendientes:
        print(f"\n  Pendientes restantes: {pendientes}")
    else:
        print("\n  0 traducciones pendientes. Todo limpio.")


if __name__ == "__main__":
    main()
