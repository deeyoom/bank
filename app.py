import os
import cv2
import numpy as np
import pandas as pd
import pytesseract
import base64
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# На Render tesseract обычно уже установлен в системе. 
# Если запускаешь на Windows, укажи путь: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def search_in_db(acc_num):
    try:
        if not os.path.exists('database.xlsx'): return None
        df = pd.read_excel('database.xlsx', engine='openpyxl')
        df['account_number'] = df['account_number'].astype(str).str.strip()
        result = df[df['account_number'] == str(acc_num).strip()]
        return result.iloc[0].to_dict() if not result.empty else None
    except: return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    try:
        data = request.json
        if data.get('manual_num'):
            client = search_in_db(data['manual_num'])
            return jsonify({"status": "found" if client else "not_found", "account": data['manual_num'], "client": client})

        if data.get('image'):
            img_str = data['image'].split(",")[1]
            img_bytes = base64.b64decode(img_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # ПРЕДОБРАБОТКА (для мелкого текста и рукописи)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

            # Распознавание только цифр
            custom_config = r'--oem 3 --psm 6 outputbase digits'
            found_acc = pytesseract.image_to_string(gray, config=custom_config).strip()
            
            # Очистка от мусора (оставляем только цифры)
            found_acc = "".join(filter(str.isdigit, found_acc))

            if found_acc:
                client = search_in_db(found_acc)
                return jsonify({"status": "found" if client else "not_in_db", "account": found_acc, "client": client})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "searching"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)