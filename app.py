import os
import pandas as pd
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

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

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    acc_num = data.get('acc_num')
    client = search_in_db(acc_num)
    if client:
        return jsonify({"status": "found", "client": client})
    return jsonify({"status": "not_found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)