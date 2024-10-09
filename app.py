from flask import Flask, request, jsonify
import cv2
import numpy as np
from passporteye import read_mrz  # Import passporteye
import re
from datetime import datetime

app = Flask(__name__)

def clean_mrz(mrz: str) -> str:
    cleaned_mrz = re.sub(r'[K<]+$', '<<<<<<<<<<<<<<', mrz)
    cleaned_mrz = re.sub(r'K+', '<', cleaned_mrz)
    return cleaned_mrz

def convert_mrz_date(mrz_date: str) -> str:
    date_obj = datetime.strptime(mrz_date, '%y%m%d')
    return date_obj.strftime('%Y-%m-%d')

@app.route('/ocr', methods=['POST'])
def ocr_image():
    file = request.files['image']
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    blurred = cv2.GaussianBlur(img, (0, 0), 9)
    sharpened = cv2.addWeighted(img, 1.5, blurred, -0.5, 0)
    temp_image_path = 'upload/temp_passport_image.jpg'
    cv2.imwrite(temp_image_path, sharpened)
    mrz = read_mrz(temp_image_path)

    if mrz is not None:
        mrz_data = mrz.to_dict()
        raw_first = mrz_data['raw_text'].split("\n")[0]
        raw_second = mrz_data['raw_text'].split("\n")[1] 
        
        return jsonify({
            'number': mrz_data['number'].replace('<', ''),
            'surname': mrz_data['surname'],
            'names': mrz_data['names'],
            'nationality': mrz_data['nationality'],
            'date_of_birth': convert_mrz_date(mrz_data['date_of_birth']),
            'expiration_date': convert_mrz_date(mrz_data['expiration_date']),
            'sex': "L" if mrz_data['sex'] == "M" else "P",
            'raw_first': clean_mrz(raw_first),
            'raw_second': raw_second
        })
    else:
        return jsonify({'error': 'MRZ not found'})

@app.route('/')
def health_check():
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(8080))
