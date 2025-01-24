# app.py
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
from PIL import Image
import numpy as np
from stego_util import (calculate_std_dev, recursive_otsu_thresholding, 
                          get_candidate_blocks, effective_embedding,
                          extract_secret_bits, decrypt_secret_message)
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/embed', methods=['POST'])
def embed():
    try:
        # Get form data
        x0 = int(request.form['x0'])  # Change to int conversion
        secret_message = request.form['message']
        image_file = request.files['image']
        
        # Convert x0 to a float between 0 and 1 for the steganography algorithm
        x0_normalized = x0 / 1000000.0  # Normalize to [0, 1]
        
        if not image_file:
            return jsonify({'error': 'No image uploaded'}), 400
            
        if not secret_message:
            return jsonify({'error': 'No message provided'}), 400

        # Add null terminator to message
        secret_message = secret_message + '\x00'
        
        # Save and process image
        filename = secure_filename(image_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(filepath)
        
        # Load and process image
        image = Image.open(filepath)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image_array = np.array(image)
        
        # Validate image dimensions
        if image_array.shape[0] < 8 or image_array.shape[1] < 8:
            return jsonify({'error': 'Image is too small. Minimum size is 8x8 pixels.'}), 400
        
        # Process image
        block_size = 8
        
        # Calculate parameters for channels
        red_alpha = recursive_otsu_thresholding(image.split()[0], block_size)
        green_alpha = recursive_otsu_thresholding(image.split()[1], block_size)
        blue_alpha = recursive_otsu_thresholding(image.split()[2], block_size)
        
        if None in (red_alpha, green_alpha, blue_alpha):
            return jsonify({'error': 'Failed to calculate threshold values. Try a different image.'}), 400
        
        # Get candidate blocks
        candidate_blocks = get_candidate_blocks(image_array, (red_alpha, green_alpha, blue_alpha))
        
        # Check capacity
        required_bits = len(secret_message) * 8 + 12
        if len(candidate_blocks) < required_bits:
            return jsonify({
                'error': f'Image capacity too small. Need {required_bits} blocks, but only found {len(candidate_blocks)}.'
            }), 400
        
        # Prepare secret bits
        secret_bits = []
        for char in secret_message:
            char_bits = format(ord(char), '08b')
            secret_bits.extend(int(bit) for bit in char_bits)
        
        # Embed message
        effective_embedding(image_array, candidate_blocks, secret_bits, x0_normalized, (red_alpha, green_alpha, blue_alpha))
        
        # Save result to bytes buffer
        output = io.BytesIO()
        stego_image = Image.fromarray(image_array)
        stego_image.save(output, format='PNG')
        output.seek(0)
        
        # Clean up
        os.remove(filepath)
        
        # Return stego image
        return send_file(
            output,
            mimetype='image/png',
            as_attachment=True,
            download_name='stego_image.png'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/decrypt', methods=['POST'])
def decrypt():
    try:
        # Get form data
        x0 = int(request.form['x0'])  # Change to int conversion
        image_file = request.files['image']
        
        # Convert x0 to a float between 0 and 1 for the steganography algorithm
        x0_normalized = x0 / 1000000.0  # Normalize to [0, 1]
        
        if not image_file:
            return jsonify({'error': 'No image uploaded'}), 400
        
        # Save and process image
        filename = secure_filename(image_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(filepath)
        
        # Load and process image
        stego_image = Image.open(filepath)
        if stego_image.mode != 'RGB':
            stego_image = stego_image.convert('RGB')
        
        stego_image_array = np.array(stego_image)
        
        # Validate image dimensions
        if stego_image_array.shape[0] < 8 or stego_image_array.shape[1] < 8:
            return jsonify({'error': 'Image is too small. Minimum size is 8x8 pixels.'}), 400
        
        # Process image
        block_size = 8
        
        # Calculate parameters for channels
        red_alpha = recursive_otsu_thresholding(stego_image.split()[0], block_size)
        green_alpha = recursive_otsu_thresholding(stego_image.split()[1], block_size)
        blue_alpha = recursive_otsu_thresholding(stego_image.split()[2], block_size)
        
        if None in (red_alpha, green_alpha, blue_alpha):
            return jsonify({'error': 'Failed to calculate threshold values. This might not be a valid stego image.'}), 400
        
        # Get candidate blocks
        candidate_blocks = get_candidate_blocks(stego_image_array, (red_alpha, green_alpha, blue_alpha))
        
        if len(candidate_blocks) == 0:
            return jsonify({'error': 'No suitable blocks found for message extraction.'}), 400
        
        # Extract and decrypt message
        extracted_bits = extract_secret_bits(stego_image_array, candidate_blocks, x0_normalized, 
                                          (red_alpha, green_alpha, blue_alpha))
        
        if not extracted_bits:
            return jsonify({'error': 'No message bits could be extracted.'}), 400
        
        decrypted_message = decrypt_secret_message(extracted_bits)
        
        if not decrypted_message:
            return jsonify({'error': 'Could not decode a valid message from the extracted bits.'}), 400
        
        # Remove null terminator
        decrypted_message = decrypted_message.rstrip('\x00')
        
        # Clean up
        os.remove(filepath)
        
        return jsonify({'message': decrypted_message})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)