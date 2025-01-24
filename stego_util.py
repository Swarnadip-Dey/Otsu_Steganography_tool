# steganography.py
import numpy as np
import math
from PIL import Image

def calculate_std_dev(image, block_size):
    image_array = np.array(image, dtype=np.float32)
    height, width = image_array.shape[:2]
    step = block_size // 2
    std_dev_image = np.zeros((height, width), dtype=np.float32)
    for y in range(0, height - block_size + 1, step):
        for x in range(0, width - block_size + 1, step):
            block = image_array[y:y+block_size, x:x+block_size]
            std_dev = np.std(block)
            std_dev_image[y:y+block_size, x:x+block_size] = std_dev
    return std_dev_image

def otsu_threshold(std_dev_image):
    std_dev_values = std_dev_image.flatten()
    hist = np.histogram(std_dev_values, bins=256)[0]
    hist = hist.astype(float) / std_dev_values.size
    best_threshold = 0
    max_variance = 0
    for t in range(1, 256):
        w0 = np.sum(hist[:t])
        w1 = 1 - w0
        u0 = np.sum(np.arange(t) * hist[:t]) / w0 if w0 > 0 else 0
        u1 = np.sum(np.arange(t, 256) * hist[t:]) / w1 if w1 > 0 else 0
        variance = w0 * w1 * (u0 - u1) ** 2
        if variance > max_variance:
            max_variance = variance
            best_threshold = t
    xi = best_threshold
    return xi

def fake_embedding(image_array, witness_image):
    stego_array = image_array.copy()
    for y in range(image_array.shape[0]):
        for x in range(image_array.shape[1]):
            if witness_image[y, x] == 255:
                if np.random.rand() < 0.5:
                    stego_array[y, x] += 1
    return stego_array

def recursive_otsu_thresholding(image, block_size, epsilon=0.1, max_iterations=10):
    xi = otsu_threshold(calculate_std_dev(image, block_size))
    alpha = 1
    for k in range(max_iterations):
        threshold = alpha * xi
        witness_cover = np.zeros_like(image, dtype=np.uint8)
        witness_stego = np.zeros_like(image, dtype=np.uint8)
        witness_cover[calculate_std_dev(image, block_size) > threshold] = 255
        stego_image_array = fake_embedding(np.array(image), witness_cover)
        witness_stego[calculate_std_dev(Image.fromarray(stego_image_array), block_size) > threshold] = 255
        if np.array_equal(witness_cover, witness_stego):
            return alpha
        alpha += k * epsilon
    return None

def ikeda_map_modified(x_n, x_0, mu=1, h=0.5, m=20):
    return x_n + h * (-mu * x_n + m * math.sin(x_0))

def generate_ikeda_sequence(x0, sequence_length, mu=1, h=0.5, m=20):
    sequence = [x0]
    x_n = x0
    for _ in range(sequence_length - 1):
        x_n = ikeda_map_modified(x_n, sequence[-1], mu, h, m)
        sequence.append(x_n)
    return sequence

def generate_keystream(block_size, x0, mu=1, h=0.5, m=20):
    sequence_length = block_size * block_size - 1
    sequence = generate_ikeda_sequence(x0, sequence_length, mu, h, m)
    keystream = [int(x * 1000) % 2 for x in sequence]
    return keystream

def get_neighbor_pixels(image_array, y, x, offsets):
    neighbors = []
    for dy, dx in offsets:
        ny, nx = y + dy, x + dx
        if 0 <= ny < image_array.shape[0] and 0 <= nx < image_array.shape[1]:
            neighbors.append(image_array[ny, nx])
    return neighbors

def get_candidate_blocks(image_array, alpha_values, block_size=8, threshold_factor=0.8):
    candidate_blocks = []
    for y in range(0, image_array.shape[0] - block_size + 1, block_size):
        for x in range(0, image_array.shape[1] - block_size + 1, block_size):
            block = image_array[y:y+block_size, x:x+block_size]
            std_devs = [np.std(block[:, :, c]) for c in range(3)]
            if all(std_dev > alpha * threshold_factor for std_dev, alpha in zip(std_devs, alpha_values)):
                candidate_blocks.append((y, x))
    return candidate_blocks

def effective_embedding(image_array, candidate_blocks, secret_bits, x0, alpha_values):
    block_size = 4
    alpha_R, alpha_G, alpha_B = alpha_values

    # Add delimiter
    delimiter = "101010101010"
    for bit in delimiter:
        secret_bits.append(int(bit))

    # Pad secret message if necessary
    while len(secret_bits) < len(candidate_blocks):
        secret_bits.append(0)

    for idx, (y, x) in enumerate(candidate_blocks):
        keystream = generate_keystream(block_size, x0)
        offsets = [(-1, 0), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 1)]
        selected_offsets = [offsets[i] for i in range(len(offsets)) if keystream[i] == 1]
        neighbor_pixels = get_neighbor_pixels(image_array, y, x, selected_offsets)

        for channel in range(1):
            central_pixel_binary = format(image_array[y, x, channel], '08b')
            neighbor_pixels_binary = ''.join(format(p[channel], '08b') for p in neighbor_pixels)
            binary_sequence = neighbor_pixels_binary + central_pixel_binary

            num_padding_bits = 128 - len(binary_sequence)
            padding_sequence = generate_ikeda_sequence(x0, num_padding_bits)
            padding_bits = ''.join(str(int(x * 1000) % 2) for x in padding_sequence)

            final_sequence = binary_sequence + padding_bits
            parity = sum(int(bit) for bit in final_sequence) % 2

            secret_bit = secret_bits[idx]

            if (parity == 0 and secret_bit == 0) or (parity == 1 and secret_bit == 1):
                pass
            else:
                image_array[y, x, channel] ^= 1

def extract_secret_bits(image_array, candidate_blocks, x0, alpha_values):
    block_size = 4
    alpha_R, alpha_G, alpha_B = alpha_values

    extracted_bits = []

    for idx, (y, x) in enumerate(candidate_blocks):
        keystream = generate_keystream(block_size, x0)
        offsets = [(-1, 0), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 1)]
        selected_offsets = [offsets[i] for i in range(len(offsets)) if keystream[i] == 1]
        neighbor_pixels = get_neighbor_pixels(image_array, y, x, selected_offsets)

        extracted_bit_sequence = ""

        for channel in range(1):
            central_pixel_binary = format(image_array[y, x, channel], '08b')
            neighbor_pixels_binary = ''.join(format(p[channel], '08b') for p in neighbor_pixels)
            binary_sequence = neighbor_pixels_binary + central_pixel_binary

            num_padding_bits = 128 - len(binary_sequence)
            padding_sequence = generate_ikeda_sequence(x0, num_padding_bits)
            padding_bits = ''.join(str(int(x * 1000) % 2) for x in padding_sequence)

            final_sequence = binary_sequence + padding_bits
            parity = sum(int(bit) for bit in final_sequence) % 2

            extracted_bit = parity
            extracted_bit_sequence += str(extracted_bit)

        extracted_bits.append(extracted_bit_sequence)

    return extracted_bits

def decrypt_secret_message(extracted_bits):
    delimiter = "101010101010"
    extracted_bits = ''.join(extracted_bits)
    
    message_bits = extracted_bits.split(delimiter)[0]
    
    message = ""
    for i in range(0, len(message_bits), 8):
        if i + 8 <= len(message_bits):
            byte = message_bits[i:i+8]
            try:
                message += chr(int(byte, 2))
            except ValueError:
                continue
    
    return message