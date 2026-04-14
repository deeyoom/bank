import os
import cv2
import numpy as np
import pandas as pd
import easyocr
import base64
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Загружаем нейросеть (English, цифры). При первом запуске скачает модели (~200MB)
print("--- СИСТЕМА ЗАПУСКАЕТСЯ: ЗАГРУЗКА ИИ МОДЕЛЕЙ ---")
reader = easyocr.Reader(['en'], gpu=False)

def search_in_db(acc_num):
    """Поиск клиента в Excel базе по номеру счета"""
    try:
        if not os.path.exists('database.xlsx'):
            return {"error": "Файл базы данных не найден"}
            
        df = pd.read_excel('database.xlsx', engine='openpyxl')
        # Превращаем всё в строки для точного сравнения
        df['account_number'] = df['account_number'].astype(str).str.strip()
        
        target = str(acc_num).strip()
        result = df[df['account_number'] == target]
        
        if not result.empty:
            return result.iloc[0].to_dict()
    except Exception as e:
        print(f"Ошибка БД: {e}")
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    try:
        data = request.json
        manual_num = data.get('manual_num')

        # 1. Если это ручной поиск
        if manual_num:
            client = search_in_db(manual_num)
            return jsonify({"status": "found" if client else "not_found", "account": manual_num, "client": client})

        # 2. Если это распознавание по фото
        if data.get('image'):
            # Декодируем изображение
            img_str = data['image'].split(",")[1]
            img_bytes = base64.b64decode(img_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # EasyOCR распознает текст (allowlist только для цифр)
            # Мы используем несколько параметров для улучшения распознавания мелкого текста
            results = reader.readtext(img, allowlist='0123456789', detail=0)
            
            if results:
                # Берем первую найденную группу цифр
                found_acc = results[0]
                client = search_in_db(found_acc)
                return jsonify({
                    "status": "found" if client else "not_in_db", 
                    "account": found_acc, 
                    "client": client
                })

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

    return jsonify({"status": "searching"})

if __name__ == '__main__':
    # Включаем debug для локальной разработки
    app.run(host='0.0.0.0', port=5000, debug=True)