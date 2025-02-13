import argparse
import sys
import time
import xml.etree.ElementTree as ET
import requests
import os
from pathlib import Path

class ScribusTranslator:
    def __init__(self, api_key: str):
        """
        Initialize the translator with DeepL API key
        
        Parameters:
            api_key (str): DeepL API key
        """
        self.api_key = api_key
        self.source_language = None
        self.target_language = 'EN'
        self.base_url = "https://api-free.deepl.com/"
        self.endpoints = {"translate" : "/v2/translate",
                          "languages" : "/v2/languages"}
        self.max_retries = 5
        self.retry_delay = 1
        self.chars_translated = 0
    
    def get_full_url(self, endpoint: str):
        """
        Get full URL for the specified endpoint
        
        Parameters:
            endpoint (str): Endpoint key
        
        Returns:
            str: Full URL for the endpoint
        """
        if endpoint not in self.endpoints:
            print(f"Invalid endpoint: {endpoint}", file=sys.stderr)
            return None
        
        return self.base_url + self.endpoints[endpoint]

    def is_supported_language(self, lang_code: str, typpe: str = 'target') -> bool:
        """
        Check if the specified language code is supported by DeepL API
        
        Parameters:
            lang_code (str): Language code to check
            type (str): Language type ('source' or 'target')
        
        Returns:
            bool: True if language is supported, False otherwise
        """
        languages = self.get_supported_languages(typpe)
      
        if languages is None:
            return False
        
        return lang_code in [lang['language'] for lang in languages]
    
    def get_supported_languages(self, type: str = 'target') -> list:
        """
        Get supported languages from DeepL API

        Parameters:
            type (str): Language type ('source' or 'target')
        return:
            list: List of supported languages
        """

        params = {
            'type': type 
        }

        headers = {
            'Authorization': f'DeepL-Auth-Key {self.api_key}'
        }
        
        response = requests.get(self.get_full_url("languages"), params=params, headers=headers)
        if response.status_code == 200:
            languages = response.json()
            return languages
        else:
            print(f"Error getting supported languages: {response.status_code}")
            return None
        
        
    def translate_text(self, text: str, target_lang: str, source_lang: str = None) -> str:
        """
        Translate text using DeepL API
        
        Parameters:
            text (str): Text to translate
            target_lang (str): Target language code
            
        Returns:
            str: Translated text
        """
        if not text.strip():
            return text
        
        params = {
            'auth_key': self.api_key,
            'text': text,
            'target_lang': target_lang
        }

        if source_lang is not None:
            params['source_lang'] = source_lang
        
        response = requests.post(self.get_full_url('translate'), params=params)
        
        if response.status_code == 200:
            return response.json()['translations'][0]['text']
        else:
            print(f"Error translating text: {response.status_code}", file=sys.stderr)
            return None
            
    def translate_file(self, input_file: str, output_file: str, target_lang, source_lang :str = None):
        """
        Read XML file, replace CH attribute with 'toto' in all ITEXT tags and save the result.
        
        Parameters:
            input_file (str): Path to the input XML file
            output_file (str, optional): Path to save modified XML. If None, overwrites input file
        """
        # Convert to Path object for better path handling
        input_path = Path(input_file)
        
        # Check if input file exists
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
                
        # Parse XML file
        tree = ET.parse(input_path)
        root = tree.getroot()
        
        # Find all ITEXT elements and modify their CH attribute
        total_texts = len(root.findall('.//ITEXT'))
        count = 0
        for itext in root.findall('.//ITEXT'):
            text_info = {
                'element': itext,
                'text': itext.get('CH', ''),
                'attributes': dict(itext.attrib)
            }
            retry_count = 0
            translated = self.translate_text(text_info['text'], target_lang)

            while translated is None and retry_count < self.max_retry:
                retry_count += 1
                print(f"Retrying translation for text: {text_info['text']} (retry {retry_count}/{self.max_retry})")
                time.sleep(self.retry_delay)
                translated = self.translate_text(text_info['text'], target_lang, source_lang)

            if translated is None:
                print(f"Failed to translate text: {text_info['text']} after {self.max_retry} retries, original text will be used")
                translated = text_info['text']

            itext.set('CH', translated)
            count += 1
            print(f"{text_info['text']} -> {translated} : {count}/{total_texts} texts: {round(count/total_texts*100, 2)}%")
        
        # Write the modified XML to file
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

    def print_supported_languages(self, typpe : str):
        languages = None
        if typpe == 'source':
            print("Supported source languages:")
            languages = self.get_supported_languages('source')
        elif typpe == 'target':
            print("Supported target languages:")
            languages = self.get_supported_languages('target')
        
        for lang in languages:
            print(f"{lang['language']} - {lang.get('name', 'N/A')} - Support formality: {lang.get('supports_formality', 'N/A')}")
        
def main():

    # Initialize argument parser
    parser = argparse.ArgumentParser(description='Scribus file translation')
    
    # Add command line arguments
    parser.add_argument('-f', '--file', required=False, help='Input file to translate')
    parser.add_argument('-o', '--output', required=False, help='Output file path')
    parser.add_argument('-t', '--target', required=False, help='Target language code (e.g., "EN-US", "FR", "ES")')
    parser.add_argument('-s', '--source', required=False, help='Source language code (e.g., "EN", "FR", "ES")')
    parser.add_argument('-k', '--api_key', required=False, help='DeepL API key')
    parser.add_argument('-r', '--retry', required=False, help='Number of retries for failed translations', type=int, default=5)
    parser.add_argument('-d', '--delay', required=False, help='Delay between retries in seconds', type=int, default=1)
    parser.add_argument('-l', '--list', required=False, help='List supported languages <source|target>', type=str)

    args=parser.parse_args()

    # get DeepL api key
    if args.api_key:
        api_key = args.api_key
    elif os.getenv('DEEPL_API_KEY'):
        api_key = os.getenv('DEEPL_API_KEY')
    else:
        print("Please provide DeepL API key using --api_key argument or DEEPL_API_KEY environment variable")
        exit(1)
    
    # Initialize translator        
    translator = ScribusTranslator(api_key)

    if args.list:
        if args.list not in ['source', 'target']:
            print(f"Invalid list type: {args.list}")
            exit(1)
        translator.print_supported_languages(args.list)
        exit(0)

    # Verify language codes
    if args.targetlanguage:
        if not translator.is_supported_language(args.targetlanguage, 'target'):
            print(f"Target language code not supported: {args.targetlanguage}")
            exit(1)
        translator.target_language = args.targetlanguage
    else:
        print("Please provide target language code using -t or --targetlanguage argument")
        exit(1)

    if args.sourcelanguage:
        if not translator.is_supported_language(args.sourcelanguage, 'source'):
            print(f"Source language code not supported: {args.sourcelanguage}")
            exit(1)
        translator.source_language = args.sourcelanguage    
    
    # Verify input file
    if args.file is None:
        print("Please provide input file using -f or --file argument")
        exit(1)
    else:
        if not os.path.isfile(args.file):
            print(f"Input file not found: {args.file}")
            exit(1)

    # Verify retry and delay values
    if args.retry:
        if args.retry < 0:
            print("Number of retries must be a positive number")
            exit(1)
        translator.max_retries = args.retry
    
    if args.delay:
        if args.delay < 0:
            print("Delay must be a positive number")
            exit(1)
        translator.retry_delay = args.delay
    
    # Define input and output files
    input_file = args.file

    if not args.output:
        file_name = input_file.rsplit('.', 1)
        output_file = f"{file_name[-2]}_translated_to_{args.targetlanguage}.{file_name[-1]}"
    else:
        output_file = args.output
    
    # Translate file
    translator.translate_file(input_file, output_file, translator.target_language, translator.source_language)
    print(f"Translation completed. Output saved to {output_file}")

if __name__ == "__main__":
    main()