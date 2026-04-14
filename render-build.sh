#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Устанавливаем системный Tesseract
apt-get update && apt-get install -y tesseract-ocr