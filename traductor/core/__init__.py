#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modulos core del sistema de traduccion."""

from traductor.core.xliff_parser import XLIFFParser, TransUnit
from traductor.core.base_translator import BaseTranslator

__all__ = ["XLIFFParser", "TransUnit", "BaseTranslator"]
