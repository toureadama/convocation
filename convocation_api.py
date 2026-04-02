#!/usr/bin/env python3
'''
API-friendly version: retourne JSON {filename, base64_pdf, size}
Usage: python convocation_api.py --cc XXX --verificateur YYY ...
'''
import argparse
import sys
import json
import base64
from convocation import ConvocationGenerator

def main():
    parser = argparse.ArgumentParser(description='Convocation API generator')
    parser.add_argument('--cc', required=True)
    parser.add_argument('--verificateur', required=True)
    parser.add_argument('--num_declaration', required=True)
    parser.add_argument('--date_declaration', required=True)
    parser.add_argument('--fraude', required=True)
    parser.add_argument('--signature_admin', required=True)
    parser.add_argument('--num_convoc', required=True)
    args = parser.parse_args()

    gen = ConvocationGenerator()
    filename, pdf_bytes = gen.generate_pdf_bytes(
        args.cc, 'CODE_AGREE.csv', args.verificateur, 
        args.num_declaration, args.date_declaration, 
        args.fraude, args.signature_admin, args.num_convoc
    )
    
    # JSON stdout pour serveur
    result = {
        'filename': filename,
        'size_bytes': len(pdf_bytes),
        'base64_pdf': base64.b64encode(pdf_bytes).decode('ascii')
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write('\n')
    sys.exit(0)

if __name__ == '__main__':
    main()

