#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servicios del sistema de traduccion."""

from traductor.services.translation_service import TranslationService
from traductor.services.incremental_detector import IncrementalDetector
from traductor.services.batch_processor import BatchProcessor

__all__ = ["TranslationService", "IncrementalDetector", "BatchProcessor"]
