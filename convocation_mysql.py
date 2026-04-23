#!/usr/bin/env python3

import logging
import os
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd
from docxtpl import DocxTemplate
import subprocess
import shutil
from db_config import get_db_connection, close_connection

class ConvocationGenerator:
    def __init__(self, template_path: str = 'Convocation_modele.docx', output_dir: str = 'output'):
        self.template_path = Path(template_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.doc = DocxTemplate(self.template_path)
        
    def _get_civilite_by_verif(self, verificateur: str):
        """Find user civilité by full name (verificateur) in users table."""
        conn = get_db_connection()
        if not conn:
            raise ValueError("MySQL connection failed")
        cursor = conn.cursor(dictionary=True)

        # Split verificateur name into parts (e.g., "TOURE ADAMA" -> ["TOURE", "ADAMA"])
        name_parts = verificateur.strip().split()
        if len(name_parts) < 2:
            close_connection(conn)
            raise ValueError(f'Invalid verificateur name format: {verificateur}. Expected "NOM PRENOM"')

        nom = name_parts[0]
        prenom = ' '.join(name_parts[1:])

        # Search by nom and prenom
        cursor.execute(
            'SELECT civilite, nom, prenom FROM users WHERE nom = %s AND prenom = %s AND is_active = 1',
            (nom, prenom)
        )
        user = cursor.fetchone()
        close_connection(conn)

        if not user:
            raise ValueError(f'User {nom} {prenom} not found in users table')

        return dict(user)

    def _get_initiales(self, verificateur: str) -> str:
        return ''.join(word[0].upper() for word in verificateur.split() if word)
    
    def _get_chef(self, signature_admin: str) -> str:
        return "Chef de Visite" if signature_admin=="COULIBALY KARIM" else "Chef de Visite Adjoint"

    def _convert_with_libreoffice(self, docx_path: str, pdf_path: str) -> bool:
        """Enhanced LibreOffice detection - Windows/Linux/Mac. Phase 1 Opti."""
        logging.info(f"[PDF] Converting {docx_path} → {pdf_path}")
        
        # ✅ PHASE 1: Robust multi-platform detection
        paths = {
            'linux': [
                shutil.which('libreoffice'),
                shutil.which('soffice'),
                '/usr/bin/libreoffice',
                '/usr/bin/soffice',
                '/opt/libreoffice/program/soffice',
                '/opt/libreoffice/LO-core/soffice',
                '/usr/lib/libreoffice/program/soffice',
                os.getenv('LO_PATH', '/usr/bin/libreoffice')
            ],
            'darwin': [  # macOS
                shutil.which('libreoffice'),
                '/Applications/LibreOffice.app/Contents/MacOS/soffice',
            ],
            'win32': [
                shutil.which('soffice'),
                shutil.which('libreoffice'),
                r'C:\Program Files\LibreOffice\program\soffice.exe',
                r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
                r'C:\Program Files\LibreOffice 7*\program\soffice.exe',  # Wildcard
                os.getenv('LO_PATH'),
            ]
        }
        
        candidate_paths = paths.get(sys.platform, paths['linux'])
        soffice_exe = None
        
        # Test all candidates
        for path in candidate_paths:
            if path and isinstance(path, str) and os.path.exists(path) and os.access(path, os.X_OK):
                soffice_exe = path
                logging.info(f"[PDF✓] LibreOffice found: {soffice_exe}")
                break
        
        if not soffice_exe:
            logging.warning("[PDF✗] LibreOffice NOT found - paths exhausted")
            return False

        # Enhanced conversion with Render-specific fixes
        output_dir = os.path.dirname(pdf_path) or '/app/output'  # Render default
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"[PDF] Created output directory: {output_dir}")

        base_cmd = [
            soffice_exe, '--headless', '--norestore',
            '--convert-to', 'pdf:writer_pdf_Export',
            '--outdir', output_dir, docx_path
        ]

        # On Linux (e.g., Render), use xvfb-run for headless display
        if sys.platform.startswith('linux'):
            # Check if xvfb is available
            if shutil.which('xvfb-run'):
                cmd = ['xvfb-run', '-a'] + base_cmd
            else:
                logging.warning("[PDF] xvfb-run not found, trying direct LibreOffice")
                cmd = base_cmd
        else:
            cmd = base_cmd

        # Environment variables for Linux/Render compatibility
        env = {**os.environ,
                'HOME': os.path.expanduser('~'),
                'DISPLAY': ':1',  # For xvfb
                'XAUTHORITY': os.path.expanduser('~/.Xauthority'),
                'LD_LIBRARY_PATH': '/opt/libreoffice/program:$LD_LIBRARY_PATH'}
        
        try:
            logging.info(f"[PDF] Executing command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,  # Increased timeout for Render
                env=env, cwd=output_dir
            )

            logging.info(f"[PDF] Command exit code: {result.returncode}")
            if result.stdout:
                logging.debug(f"[PDF] stdout: {result.stdout[:200]}")
            if result.stderr:
                logging.debug(f"[PDF] stderr: {result.stderr[:200]}")

            if result.returncode == 0 and os.path.exists(pdf_path):
                logging.info(f"[PDF✓] LibreOffice success: {pdf_path}")
                return True
            else:
                logging.warning(f"[PDF✗] LO failed (code {result.returncode}): {result.stderr[:300]}")
                return False

        except subprocess.TimeoutExpired:
            logging.error("[PDF✗] LibreOffice timeout (120s)")
            return False
        except Exception as e:
            logging.error(f"[PDF✗] LibreOffice error: {e}")
            return False

            # Convert using LibreOffice headless mode
            output_dir = os.path.dirname(pdf_path) or '.'
            cmd = [
                soffice_exe,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                docx_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, 'HOME': os.path.expanduser('~')}
            )

            if result.returncode != 0:
                logging.warning(f"LibreOffice conversion failed: {result.stderr}")
                return False

            # Verify output file exists
            if not os.path.exists(pdf_path):
                logging.warning(f"PDF file not created by LibreOffice: {pdf_path}")
                return False

            logging.info(f"Successfully converted with LibreOffice: {pdf_path}")
            return True

        except Exception as e:
            logging.warning(f"LibreOffice conversion error: {e}")
            return False

    def _convert_with_word(self, docx_path: str, pdf_path: str) -> bool:
        """Enhanced MS Word fallback - Windows only. Phase 1."""
        if sys.platform != 'win32':
            return False

        try:
            import win32com.client
            import win32api
            from pywintypes import com_error
        except ImportError:
            logging.info("[PDF] pywin32 missing - Word fallback disabled")
            return False

        try:
            # Verify Word installed via registry/COM
            word = win32com.client.Dispatch("Word.Application")
            if not word:
                logging.warning("[PDF] Word COM unavailable")
                return False
                
            word.Visible = False
            word.DisplayAlerts = 0  # wdAlertsNone
            
            doc = word.Documents.Open(os.path.abspath(docx_path))
            doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)  # PDF
            doc.Close()
            word.Quit()
            
            if os.path.exists(pdf_path):
                logging.info(f"[PDF✓] Word success: {pdf_path}")
                return True
            else:
                logging.warning("[PDF✗] Word created no output")
                return False
                
        except Exception as e:
            logging.warning(f"[PDF✗] Word error: {e}")
            return False

    def _convert_to_pdf(self, docx_path: str, pdf_path: str):
        """Convert DOCX to PDF using LibreOffice or Microsoft Word."""
        # Try LibreOffice first (cross-platform)
        if self._convert_with_libreoffice(docx_path, pdf_path):
            return

        # If on Windows and LibreOffice failed, try Microsoft Word
        if sys.platform == 'win32':
            if self._convert_with_word(docx_path, pdf_path):
                return

        # If we get here, both methods failed
        raise RuntimeError(
            "PDF conversion failed. Please install either:\n"
            "1. LibreOffice (recommended, cross-platform): https://www.libreoffice.org/\n"
            "2. Microsoft Word (Windows only) with pywin32: pip install pywin32"
        )

    def _get_company_by_cc(self, cc: str):
        conn = get_db_connection()
        if not conn:
            raise ValueError("MySQL connection failed")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT cc, societe FROM code_agree WHERE cc = %s LIMIT 1", (cc,))
        row = cursor.fetchone()
        close_connection(conn)
        if not row:
            raise ValueError(f'CC {cc} not found in code_agree')
        return dict(row)

    def _get_operateur_by_imp(self, imp: str):
        conn = get_db_connection()
        if not conn:
            raise ValueError("MySQL connection failed")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT code_operateur, nom_operateur FROM operateur WHERE code_operateur = %s LIMIT 1", (imp,))
        row_imp = cursor.fetchone()
        close_connection(conn)
        if not row_imp:
            raise ValueError(f'code_operateur {imp} not found in operateur')
        return dict(row_imp )

    def generate(self, cc: str, code_imp: str, verificateur: str = '', type_dossier: str = '', num_declaration: str = '', date_declaration: str = '', fraude: str = '', signature_admin: str = '', num_convoc: str = '0001') -> Tuple[str, str]:
        row = self._get_company_by_cc(cc)
        row_imp = self._get_operateur_by_imp(code_imp)
        initiales = self._get_initiales(verificateur)
        civilite = self._get_civilite_by_verif(verificateur)
        Init_Adm  = self._get_initiales(signature_admin)
        chef = self._get_chef(signature_admin)
        annee = pd.Timestamp.now().strftime('%Y')
        FRAUDE_MAP = {
            'FDE': 'FAUSSE DECLARATION ESPECE',
            'FDV': 'FAUSSE DECLARATION VALEUR', 
            'ESP': 'ENLEVEMENT SANS PERMIS',
            'EXC': 'EXCEDENT'
        }
        
        fraude_libelle = FRAUDE_MAP.get(fraude.upper(), fraude)
        
        context = {
            'compte_contribuale': row['cc'],
            'societe': row['societe'],
            'code_operateur': row_imp['code_operateur'],
            'operateur': row_imp['nom_operateur'],
            'verificateur': verificateur,
            'init_adm': Init_Adm,
            'initiales': initiales,
            'num_convoc': num_convoc,
            'num_declaration': num_declaration,
            'date_declaration': date_declaration,
            'fraude': fraude_libelle,
            'date': pd.Timestamp.now().strftime('%d/%m/%Y'),
            'numMY': pd.Timestamp.now().strftime('%m/%Y'),
            'annee': annee,
            'administrateur': signature_admin,
            'chef': chef
        }

        self.doc.render(context)
        docx_name = f"Convocation_{initiales}_{annee}_{num_convoc}.docx"
        pdf_name = f"Convocation_{initiales}_{annee}_{num_convoc}.pdf"
        docx_path = self.output_dir / docx_name
        pdf_path = self.output_dir / pdf_name

        self.doc.save(docx_path)

        # Cross-platform PDF conversion using LibreOffice (works on Linux/Render & Windows)
        try:
            self._convert_to_pdf(str(docx_path), str(pdf_path))
            logging.info(f'PDF generated: {pdf_path}')

            # Remove DOCX file after successful PDF conversion
            if os.path.exists(docx_path):
                os.remove(docx_path)
                logging.info(f'DOCX removed: {docx_path}')
        except FileNotFoundError as e:
            logging.error(f"PDF conversion failed - LibreOffice not found: {e}")
            raise RuntimeError("LibreOffice is required for PDF conversion. Install it or use Windows with MS Word.")
        except Exception as e:
            logging.error(f"PDF conversion failed: {e}")
            raise RuntimeError(f"PDF conversion failed: {e}")
        
        print(f'OK : {pdf_path}')
        
        return str(docx_path), str(pdf_path)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Générateur convocation SQLite local.')
    parser.add_argument('--cc', required=True, help='N° Code Déclarant')
    parser.add_argument('--code_imp', required=True, help='N° Code Opérateur')
    parser.add_argument('--verificateur', required=True)
    parser.add_argument('--type_dossier', required=True, help='Type de dossier (BDAP/DARRV)')
    parser.add_argument('--num_declaration', required=True)
    parser.add_argument('--date_declaration', required=True)
    parser.add_argument('--fraude', required=True)
    parser.add_argument('--signature_admin', required=True)
    parser.add_argument('--num_convoc', default='0001')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    gen = ConvocationGenerator()
    try:
        gen.generate(args.cc, args.code_imp, args.verificateur, args.type_dossier, args.num_declaration, args.date_declaration, args.fraude, args.signature_admin, args.num_convoc)
    except Exception as e:
        logging.error(f"Generation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
