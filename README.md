# Scribus Translator

## Overview

It is challenging to translate quickly and efficiently a document realized with `Scribus`. The `Scribus Translator` aims to simplify the translation by using the DeepL free API.

## Requirements

To use the `Scribus Translator`, you need to have an account on [DeepL](https://www.deepl.com) and an API key.
With a Free API key, you can translate up to 500,000 characters per month.

## Usage

To start using the `Scribus Translator`, you need to clone the repository on your local machine.

With the API key. you have two options:
- export the API key as an environment variable using this command:
```bash
export DEEPL_API_KEY=your_api_key
```   
> [!NOTE]
> You can add this command to your `.bashrc` file to make it permanent.

- pass the API key as an argument to the script using the `-k` option

#### Example

```bash

python translator.py -i example.sla -o exemple_translated.sla
```

#### Options

```bash
python translate.py --help
usage: translate.py [-h] [-f FILE] [-o OUTPUT] [-t TARGET] [-s SOURCE] [-k API_KEY] [-r RETRY] [-d DELAY] [-l LIST]

Scribus file translation

options:
  -h, --help            show this help message and exit
  -f, --file FILE       Input file to translate
  -o, --output OUTPUT   Output file path
  -t, --target TARGET   Target language code (e.g., "EN-US", "FR", "ES")
  -s, --source SOURCE   Source language code (e.g., "EN", "FR", "ES")
  -k, --api_key API_KEY DeepL API key
  -r, --retry RETRY     Number of retries for failed translations
  -d, --delay DELAY     Delay between retries in seconds
  -l, --list LIST       List supported languages <source|target>
```





