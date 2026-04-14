import os
import cv2
import numpy as np
import pandas as pd
import easyocr
import base64
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Инициализируем нейросеть (English + только цифры)
# gpu=False обязательно для бесплатного Render
print("--- LOADING AI MODELS ---")
reader = easyocr.Reader(['en'], gpu=False)

def search_in_db(acc_num):
    try:
        if not os.path.exists('database.xlsx'):
            return None
        df = pd.read_excel('database.xlsx', engine='openpyxl')
        # Очистка базы: номера в строку, убираем пробелы
        df['account_number'] = df['account_number'].astype(str).str.strip()
        target = str(acc_num).strip()
        
        result = df[df['account_number'] == target]
        if not result.empty:
            return result.iloc[0].to_dict()
    except Exception as e:
        print(f"DB Error: {e}")
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    try:
        data = request.json
        # Ручной поиск
        if data.get('manual_num'):
            client = search_in_db(data['manual_num'])
            return jsonify({"status": "found" if client else "not_found", "account": data['manual_num'], "client": client})

        # Поиск через ИИ
        if data.get('image'):
            img_str = data['image'].split(",")[1]
            img_bytes = base64.b64decode(img_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Распознавание (EasyOCR сам делает предобработку)
            # allowlist='0123456789' заставляет ИИ искать ТОЛЬКО цифры
            results = reader.readtext(img, allowlist='0123456789', detail=0)
            
            if results:
                # Берем самую длинную строку цифр, которую он нашел
                found_acc = max(results, key=len)
                client = search_in_db(found_acc)
                return jsonify({
                    "status": "found" if client else "not_in_db", 
                    "account": found_acc, 
                    "client": client
                })

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"status": "error"})
    
    return jsonify({"status": "searching"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)