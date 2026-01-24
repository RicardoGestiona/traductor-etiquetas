#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traductor de archivos XLIFF del inglés al catalán
Soporta Google Translate API y DeepL API
"""

import xml.etree.ElementTree as ET
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, List
import argparse

# Intenta importar las librerías de traducción
try:
    from google.cloud import translate_v2 as translate
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    import deepl
    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Nota: Instala 'tqdm' para ver una barra de progreso mejorada")


class TraductorXLIFF:
    """Clase principal para traducir archivos XLIFF"""
    
    def __init__(self, archivo_entrada: str, archivo_salida: str, 
                 api: str = "google", api_key: Optional[str] = None,
                 checkpoint_file: str = "checkpoint.json"):
        """
        Inicializa el traductor
        
        Args:
            archivo_entrada: Ruta del archivo XLIFF de entrada
            archivo_salida: Ruta del archivo XLIFF de salida
            api: API a usar ('google' o 'deepl')
            api_key: Clave API (necesaria para DeepL, opcional para Google)
            checkpoint_file: Archivo para guardar el progreso
        """
        self.archivo_entrada = archivo_entrada
        self.archivo_salida = archivo_salida
        self.api = api.lower()
        self.api_key = api_key
        self.checkpoint_file = checkpoint_file
        self.traducciones_hechas = 0
        self.checkpoint_data = self._cargar_checkpoint()
        
        # Inicializar el cliente de traducción
        if self.api == "google":
            if not GOOGLE_AVAILABLE:
                raise ImportError(
                    "Google Translate no disponible. Instala: pip install google-cloud-translate"
                )
            if api_key:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = api_key
            self.cliente = translate.Client()
            
        elif self.api == "deepl":
            if not DEEPL_AVAILABLE:
                raise ImportError(
                    "DeepL no disponible. Instala: pip install deepl"
                )
            if not api_key:
                raise ValueError("DeepL requiere una API key")
            self.cliente = deepl.Translator(api_key)
        else:
            raise ValueError(f"API no soportada: {api}. Usa 'google' o 'deepl'")
    
    def _cargar_checkpoint(self) -> Dict:
        """Carga el checkpoint si existe"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _guardar_checkpoint(self, trans_unit_id: str, traduccion: str):
        """Guarda el progreso en el checkpoint"""
        self.checkpoint_data[trans_unit_id] = traduccion
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoint_data, f, ensure_ascii=False, indent=2)
    
    def traducir_texto(self, texto: str, reintentos: int = 3) -> Optional[str]:
        """
        Traduce un texto del inglés al catalán
        
        Args:
            texto: Texto a traducir
            reintentos: Número de reintentos en caso de error
            
        Returns:
            Texto traducido o None si falla
        """
        if not texto or not texto.strip():
            return texto
        
        for intento in range(reintentos):
            try:
                if self.api == "google":
                    resultado = self.cliente.translate(
                        texto,
                        source_language='en',
                        target_language='ca'
                    )
                    return resultado['translatedText']
                    
                elif self.api == "deepl":
                    resultado = self.cliente.translate_text(
                        texto,
                        source_lang="EN",
                        target_lang="CA"
                    )
                    return resultado.text
                    
            except Exception as e:
                print(f"\nError en intento {intento + 1}: {e}")
                if intento < reintentos - 1:
                    time.sleep(2 ** intento)  # Espera exponencial
                else:
                    print(f"Error al traducir: {texto[:50]}...")
                    return None
        
        return None
    
    def procesar_xliff(self):
        """Procesa el archivo XLIFF completo"""
        print(f"Cargando archivo: {self.archivo_entrada}")
        
        # Parsear el XML preservando el formato
        tree = ET.parse(self.archivo_entrada)
        root = tree.getroot()
        
        # Encontrar todas las unidades de traducción
        namespace = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}
        trans_units = root.findall('.//xliff:trans-unit', namespace)
        
        if not trans_units:
            # Intenta sin namespace
            trans_units = root.findall('.//trans-unit')
        
        total_unidades = len(trans_units)
        print(f"Total de unidades de traducción encontradas: {total_unidades}")
        
        # Preparar iterador con o sin tqdm
        if TQDM_AVAILABLE:
            iterador = tqdm(trans_units, desc="Traduciendo", unit="unidad")
        else:
            iterador = trans_units
            print("Iniciando traducción...")
        
        unidades_procesadas = 0
        unidades_saltadas = 0
        
        for trans_unit in iterador:
            trans_unit_id = trans_unit.get('id', 'unknown')
            
            # Buscar elementos source y target
            source = trans_unit.find('.//xliff:source', namespace)
            target = trans_unit.find('.//xliff:target', namespace)
            
            if source is None:
                source = trans_unit.find('.//source')
            if target is None:
                target = trans_unit.find('.//target')
            
            if source is None or target is None:
                unidades_saltadas += 1
                continue
            
            # Extraer texto del source (puede estar en CDATA o texto directo)
            texto_source = self._extraer_texto(source)
            
            if not texto_source:
                unidades_saltadas += 1
                continue
            
            # Verificar si ya existe en el checkpoint
            if trans_unit_id in self.checkpoint_data:
                traduccion = self.checkpoint_data[trans_unit_id]
            else:
                # Traducir
                traduccion = self.traducir_texto(texto_source)
                
                if traduccion:
                    self._guardar_checkpoint(trans_unit_id, traduccion)
                else:
                    # Si falla, mantener el original
                    traduccion = texto_source
                    unidades_saltadas += 1
            
            # Actualizar el target
            self._actualizar_target(target, traduccion)
            
            unidades_procesadas += 1
            self.traducciones_hechas += 1
            
            # Actualizar progreso si no hay tqdm
            if not TQDM_AVAILABLE and unidades_procesadas % 100 == 0:
                porcentaje = (unidades_procesadas / total_unidades) * 100
                print(f"Progreso: {unidades_procesadas}/{total_unidades} ({porcentaje:.1f}%)")
            
            # Pequeña pausa para no saturar la API
            if unidades_procesadas % 10 == 0:
                time.sleep(0.1)
        
        # Guardar el archivo traducido
        print(f"\nGuardando archivo traducido: {self.archivo_salida}")
        tree.write(self.archivo_salida, encoding='utf-8', xml_declaration=True)
        
        print(f"\n✓ Traducción completada!")
        print(f"  - Unidades traducidas: {unidades_procesadas}")
        print(f"  - Unidades saltadas: {unidades_saltadas}")
        print(f"  - Archivo de salida: {self.archivo_salida}")
        
        # Opcional: eliminar checkpoint
        if os.path.exists(self.checkpoint_file):
            respuesta = input("\n¿Deseas eliminar el archivo de checkpoint? (s/n): ")
            if respuesta.lower() == 's':
                os.remove(self.checkpoint_file)
                print("Checkpoint eliminado.")
    
    def _extraer_texto(self, elemento: ET.Element) -> str:
        """Extrae el texto de un elemento, incluyendo CDATA"""
        texto = elemento.text or ""
        for child in elemento:
            if child.text:
                texto += child.text
            if child.tail:
                texto += child.tail
        return texto.strip()
    
    def _actualizar_target(self, elemento: ET.Element, nuevo_texto: str):
        """Actualiza el texto del elemento target, preservando CDATA si existe"""
        # Limpiar el elemento
        elemento.clear()
        elemento.text = f"<![CDATA[{nuevo_texto}]]>"


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Traduce archivos XLIFF del inglés al catalán'
    )
    parser.add_argument(
        'archivo_entrada',
        help='Archivo XLIFF de entrada'
    )
    parser.add_argument(
        '-o', '--output',
        dest='archivo_salida',
        help='Archivo XLIFF de salida (por defecto: entrada_ca.xliff)'
    )
    parser.add_argument(
        '--api',
        choices=['google', 'deepl'],
        default='google',
        help='API de traducción a usar (por defecto: google)'
    )
    parser.add_argument(
        '--api-key',
        help='Clave API (necesaria para DeepL)'
    )
    parser.add_argument(
        '--checkpoint',
        default='checkpoint.json',
        help='Archivo de checkpoint (por defecto: checkpoint.json)'
    )
    
    args = parser.parse_args()
    
    # Determinar archivo de salida
    if not args.archivo_salida:
        entrada_path = Path(args.archivo_entrada)
        args.archivo_salida = str(entrada_path.parent / f"{entrada_path.stem}_ca{entrada_path.suffix}")
    
    # Verificar que el archivo de entrada existe
    if not os.path.exists(args.archivo_entrada):
        print(f"Error: El archivo {args.archivo_entrada} no existe")
        sys.exit(1)
    
    # Crear traductor y procesar
    try:
        traductor = TraductorXLIFF(
            args.archivo_entrada,
            args.archivo_salida,
            api=args.api,
            api_key=args.api_key,
            checkpoint_file=args.checkpoint
        )
        traductor.procesar_xliff()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

