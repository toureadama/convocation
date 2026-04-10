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

    def _convert_to_pdf(self, docx_path: str, pdf_path: str):
        """Convert DOCX to PDF using LibreOffice headless mode (cross-platform)."""
        # Find LibreOffice executable
        libreoffice_paths = {
            'linux': [
                '/usr/bin/libreoffice',
                '/usr/bin/soffice',
                '/opt/libreoffice/program/soffice',
            ],
            'win32': [
                r'C:\Program Files\LibreOffice\program\soffice.exe',
                r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
            ],
        }

        soffice_exe = shutil.which('libreoffice') or shutil.which('soffice')

        if not soffice_exe:
            for path in libreoffice_paths.get(sys.platform, []):
                if os.path.exists(path):
                    soffice_exe = path
                    break

        if not soffice_exe:
            raise FileNotFoundError(
                "LibreOffice not found. Install it from https://www.libreoffice.org/"
            )

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
            raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

        # Verify output file exists
        if not os.path.exists(pdf_path):
            raise RuntimeError(f"PDF file not created after conversion: {pdf_path}")

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
