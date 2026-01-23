#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servicios del sistema de traduccion."""

from traductor.services.translation_service import TranslationService
from traductor.services.incremental_detector import IncrementalDetector

__all__ = ["TranslationService", "IncrementalDetector"]
