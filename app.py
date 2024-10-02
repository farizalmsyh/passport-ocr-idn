from flask import Flask, request, jsonify
import cv2
import numpy as np
from passporteye import read_mrz  # Import passporteye
import re
from datetime import datetime

app = Flask(__name__)

def clean_mrz(mrz: str) -> str:
    # Remove excess 'K' characters and replace them with '<'
    # Regular expression will find runs of characters that are either 'K' or '<'
    cleaned_mrz = re.sub(r'[K<]+$', '<<<<<<<<<<<<<<', mrz)  # Replace excess trailing 'K's or '<'s with proper '<<<<'
    
    # For multiple errors like 'K' or missing '<', we further clean:
    cleaned_mrz = re.sub(r'K+', '<', cleaned_mrz)  # Replace all 'K's in the middle with '<'
    
    return cleaned_mrz

def convert_mrz_date(mrz_date: str) -> str:
    # Parse the YYMMDD format and convert it to a datetime object
    date_obj = datetime.strptime(mrz_date, '%y%m%d')
    
    # Format the date as YYYY-MM-DD
    return date_obj.strftime('%Y-%m-%d')

@app.route('/ocr', methods=['POST'])
def ocr_image():
    # Get the uploaded image file
    file = request.files['image']

    # Read the image using OpenCV
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(img, (0, 0), 9)

    # Sharpen the image
    sharpened = cv2.addWeighted(img, 1.5, blurred, -0.5, 0)

    # Save the processed image temporarily to pass to passporteye
    temp_image_path = 'temp_passport_image.jpg'
    cv2.imwrite(temp_image_path, sharpened)

    # Perform OCR using passporteye's MRZ reader
    mrz = read_mrz(temp_image_path)

    if mrz is not None:
        mrz_data = mrz.to_dict()
        return jsonify({
            # 'result': clean_mrz(mrz_data['raw_text']).replace('\n', ''),
            # 'exact': mrz_data,
            'number': mrz_data['number'].replace('<', ''),
            'surname': mrz_data['surname'],
            'names': mrz_data['names'],
            'nationality': mrz_data['nationality'],
            'date_of_birth': convert_mrz_date(mrz_data['date_of_birth']),
            'expiration_date': convert_mrz_date(mrz_data['expiration_date']),
            'sex': "L" if mrz_data['sex'] == "M" else "P",
        })
    else:
        return jsonify({'error': 'MRZ not found'})

# Health check route
@app.route('/')
def health_check():
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(8080))
