#!/usr/bin/env python3
'''
API-friendly version MySQL: retourne JSON {filename, base64_pdf, size}
DB code_agree instead of CSV
Usage: python convocation_api_mysql.py --cc X --verificateur YYY ...
'''
import os
import argparse
import sys
import json
import base64
from convocation_mysql import ConvocationGenerator

def main():
    parser = argparse.ArgumentParser(description='Convocation API generator MySQL')
    parser.add_argument('--cc', required=True)
    parser.add_argument('--verificateur', required=True)
    parser.add_argument('--num_declaration', required=True)
    parser.add_argument('--date_declaration', required=True)
    parser.add_argument('--fraude', required=True)
    parser.add_argument('--signature_admin', required=True)
    parser.add_argument('--num_convoc', required=True)
    args = parser.parse_args()

    gen = ConvocationGenerator()
    docx_path, pdf_path = gen.generate(
        args.cc, args.verificateur, 
        args.num_declaration, args.date_declaration, 
        args.fraude, args.signature_admin, args.num_convoc
    )
    
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    # JSON stdout pour serveur
    result = {
        'filename': os.path.basename(pdf_path),
        'size_bytes': len(pdf_bytes),
        'base64_pdf': base64.b64encode(pdf_bytes).decode('ascii')
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write('\n')
    sys.exit(0)

if __name__ == '__main__':
    main()

