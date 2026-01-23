#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modulo de base de datos para el sistema de traduccion."""

from traductor.database.db_manager import DatabaseManager
from traductor.database.models import SCHEMA_SQL

__all__ = ["DatabaseManager", "SCHEMA_SQL"]
