#!/usr/bin/env python3

import logging
import os
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd
from docxtpl import DocxTemplate
import subprocess

BASE_DIR = Path(__file__).resolve().parent

class ConvocationGenerator:
    def __init__(self, template_path: str = 'Convocation_modele.docx', output_dir: str = 'output'):
        self.template_path = BASE_DIR / template_path
        self.output_dir = BASE_DIR / output_dir
        
        #self.template_path = Path(template_path)
        #self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(exist_ok=True)
        self.doc = DocxTemplate(self.template_path)

    def _get_initiales(self, verificateur: str) -> str:
        return ''.join(word[0].upper() for word in verificateur.split() if word)
    
    def _get_chef(self, signature_admin: str) -> str:
        return "Chef de Visite" if signature_admin=="OUATTARA KARIM" else "Chef de Visite Adjoint"

    def generate(self, cc: str, csv_path: str = 'CODE_AGREE.csv', verificateur: str = '', num_declaration: str = '', date_declaration: str = '', fraude: str = '', signature_admin: str = '', num_convoc: str = '0001') -> Tuple[str, str]:
        df = pd.read_csv(csv_path, encoding='utf-8-sig', sep=';')
        mask = df.iloc[:,0].astype(str).str.strip() == cc
        if not mask.any():
            raise ValueError(f'CC {cc} not found in {csv_path}')
        row = df[mask].iloc[0]
        initiales = self._get_initiales(verificateur)
        chef = self._get_chef(signature_admin)
        annee = pd.Timestamp.now().year
        FRAUDE_MAP = {
            'FDE': 'FAUSSE DECLARATION ESPECE',
            'FDV': 'FAUSSE DECLARATION VALEUR', 
            'EXC': 'EXCEDENT'
        }
        
        fraude_libelle = FRAUDE_MAP.get(fraude.upper(), fraude)
        
        context = {
            'compte_contribuale': str(row.iloc[0]),
            'societe': str(row.iloc[1]),
            'verificateur': verificateur,
            'initiales': initiales,
            'num_convoc': num_convoc,
            'num_declaration': num_declaration,
            'date_declaration': date_declaration,
            'fraude': fraude_libelle,
            'date': pd.Timestamp.now().strftime('%d/%m/%Y'),
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
        logging.info(f'Docx sauvé : {docx_path}')
        
        subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(self.output_dir),
            str(docx_path)
        ], check=True)
        
        logging.info(f'PDF généré : {pdf_path}')
        print(f'[1/1] OK : {pdf_path}')
        return str(docx_path), str(pdf_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Générateur convocation single CC.')
    parser.add_argument('--cc', required=True, help='N° Compte Contribuable')
    parser.add_argument('--verificateur', required=True)
    parser.add_argument('--num_declaration', required=True)
    parser.add_argument('--date_declaration', required=True)
    parser.add_argument('--fraude', required=True)
    parser.add_argument('--signature_admin', required=True)
    parser.add_argument('--csv', default='CODE_AGREE.csv')
    parser.add_argument('--num_convoc', default='0001', help='Numéro convocation (0001)')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    gen = ConvocationGenerator()
    gen.generate(args.cc, args.csv, args.verificateur, args.num_declaration, args.date_declaration, args.fraude, args.signature_admin, args.num_convoc)
    print('Convocation générée avec succès!')


if __name__ == '__main__':
    main()
