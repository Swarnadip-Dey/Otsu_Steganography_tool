# Image Steganography Web Application

This web application demonstrates image steganography techniques, allowing users to embed secret messages within images and subsequently extract them. It utilizes the Flask framework, Pillow (PIL) for image processing, and custom steganography algorithms defined in `stego_util.py`.

## Features

*   **Message Embedding:** Embed a secret message within an image using a chaotic Ikeda map-based embedding scheme.
*   **Message Extraction:** Extract a hidden message from an image using the same Ikeda map-based algorithm and a delimiter.
*   **Adaptive Block Selection:** Uses recursive Otsu thresholding to identify suitable blocks within the image for embedding based on standard deviation.
*   **Error Handling:** Includes robust error handling to guide users through potential issues such as incorrect input or insufficient image capacity.
*   **Secure File Handling:** Uses `werkzeug.utils.secure_filename` to sanitize uploaded filenames, preventing potential security vulnerabilities.

## Technologies Used

*   **Flask:** A micro web framework for Python.
*   **Pillow (PIL):** Python Imaging Library for image processing.
*   **NumPy:**  For numerical operations, especially for image manipulation and statistical calculations.
*   **HTML/CSS/JavaScript:** For the user interface.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate   # On Windows
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**

    ```bash
    python app.py
    ```

2.  **Open the application in your web browser:**

    Navigate to `http://127.0.0.1:5000/` or the address displayed in your terminal.

### Embedding a Message

1.  **Navigate to the Embedding Page:** The main index page provides the embedding functionality.
2.  **Upload an Image:** Click the "Choose File" button to select an image file (PNG, JPG, JPEG supported).
3.  **Enter the Secret Message:** Type your secret message into the "Message" text area. Ensure the message isn't overly long, relative to image size to avoid errors.
4.  **Enter x0:** Enter the x0 value. This is important and must be remembered for extraction. The value represents the initial value for the Ikeda map.  **Important:** x0 should be an *integer* value. It will be normalized in code for usage.
5.  **Click "Embed":**  This will embed the message in the image and prompt you to download the stego image.

### Extracting a Message

1.  **Navigate to the Extraction Page:** The main index page provides the extraction functionality.
2.  **Upload the Stego Image:** Click the "Choose File" button to select the image containing the hidden message.
3.  **Enter x0:** Enter the exact same x0 value used during embedding. This is crucial for successful extraction. **Important:** x0 should be an *integer* value. It will be normalized in code for usage.
4.  **Click "Decrypt":** The extracted message will be displayed on the page.

## Files

*   `app.py`: The main Flask application file.  Handles routing, form processing, and calls the steganography functions.
*   `stego_util.py`: Contains the steganography algorithms, including:
    *   `calculate_std_dev`: Calculates the standard deviation of image blocks.
    *   `otsu_threshold`: Implements Otsu's thresholding algorithm.
    *   `recursive_otsu_thresholding`: Adaptively determines a threshold for block selection.
    *   `ikeda_map_modified`: Calculates the Ikeda map.
    *   `generate_ikeda_sequence`: Generates Ikeda sequence used for the key stream.
    *   `get_candidate_blocks`: Identifies blocks suitable for embedding.
    *   `effective_embedding`: Embeds the secret message into the image.
    *   `extract_secret_bits`: Extracts the hidden message from the image.
    *   `decrypt_secret_message`: Decodes the extracted bits into a human-readable message.
*   `templates/index.html`: The HTML template for the web application. Provides the UI for embedding and extraction.
*   `uploads/`:  A directory to store uploaded images temporarily.  This directory is created automatically if it doesn't exist.
*   `requirements.txt`: A list of Python packages required to run the application.

## Algorithm Details

The steganography algorithm utilizes a modified Ikeda map to generate a pseudo-random keystream.  This keystream is then used to determine which bits in the image will be modified to encode the secret message. Recursive Otsu thresholding is employed to select candidate blocks for embedding, enhancing the robustness of the method.

1.  **Block Selection:** The image is divided into blocks, and the standard deviation of each block is calculated.  Recursive Otsu thresholding is used to adaptively determine a threshold value. Blocks with a standard deviation above this threshold are considered candidates for embedding.
2.  **Key Generation:** A modified Ikeda map (a chaotic map) is used to generate a pseudo-random keystream based on the `x0` value. **The Ikeda model is used for random number generation, creating a unique key for each pixel or block being processed. While this process can be computationally intensive, potentially increasing the embedding and extraction times, it significantly enhances the security by making it difficult for unauthorized parties to predict the embedding pattern.** The `x0` value serves as the seed for the chaotic sequence.
3.  **Embedding:** For each candidate block, the keystream determines which bits are modified to embed the secret message. The LSB of selected pixels are flipped if the parity of the neighbouring pixels, concatenated with the central pixel's bits and padding, does not match the secret bit to be embedded.
4.  **Extraction:** The process is reversed to extract the secret message. Using the same `x0` value, the keystream is regenerated, and the parity checks are performed on the corresponding pixels in each candidate block to recover the hidden bits.

## Error Handling

The application includes error handling to address common issues:

*   **No Image Uploaded:**  Displays an error if the user attempts to embed or extract a message without uploading an image.
*   **No Message Provided:** Displays an error if the user attempts to embed a message without entering any text.
*   **Image Too Small:**  Displays an error if the uploaded image is too small for the algorithm to function (minimum 8x8 pixels).
*   **Failed to Calculate Threshold Values:**  Indicates a problem with the image characteristics, preventing proper block selection.
*   **Image Capacity Too Small:**  Indicates that the image does not have enough suitable blocks to embed the entire message.
*   **Invalid Stego Image:**  Indicates that the uploaded image may not be a valid stego image or that the x0 value is incorrect.
*   **No Message Bits Could Be Extracted:**  Indicates that no valid message bits can be extracted.

## Security Considerations

*   **x0 Value:** The `x0` value is crucial for both embedding and extraction. If this value is lost or incorrect, the message cannot be recovered. **Keep this value secure and remember it.**
*   **Image Size:** The capacity of the image limits the length of the secret message that can be embedded. Larger images can accommodate longer messages.
*   **Robustness:** The steganography method is not entirely robust against image manipulations. Changes to the image (e.g., compression, resizing) may corrupt the hidden message.
*   **Filename Sanitization:** The application uses `werkzeug.utils.secure_filename` to sanitize uploaded filenames, preventing potential path traversal vulnerabilities.
*   **Temporary File Storage:**  Uploaded images are stored temporarily in the `uploads/` directory.  These files are deleted after processing to minimize the risk of exposure.

## Future Enhancements

*   **Improved Robustness:** Implement techniques to make the steganography method more resistant to image manipulations (e.g., error correction codes, spread spectrum techniques).
*   **Encryption:** Add encryption to the secret message before embedding to further enhance security.
*   **User Authentication:** Implement user authentication to restrict access to the embedding and extraction features.
*   **GUI Improvements:** Enhance the user interface for a better user experience.  Provide visual feedback on embedding progress and capacity.
*   **Support for More Image Formats:** Extend support to other image formats.
*   **Error Correction:** Implement error correction schemes to improve the message recovery under image manipulation.

## Contributing

Contributions are welcome!  Please submit pull requests with bug fixes, new features, or improvements to the documentation.
