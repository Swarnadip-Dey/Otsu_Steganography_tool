// static/js/main.js
class SteganographyApp {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
        this.setupTabSwitching();
    }

    initializeElements() {
         // Background
        this.background = document.querySelector('.background');

        // Forms
        this.embedForm = document.getElementById('embedForm');
        this.decryptForm = document.getElementById('decryptForm');

        // Results
        this.embedResult = document.getElementById('embedResult');
        this.embedError = document.getElementById('embedError');
        this.decryptResult = document.getElementById('decryptResult');
        this.decryptError = document.getElementById('decryptError');

         // Decrypted message elements
        this.decryptedMessageContainer = document.getElementById('decryptedMessageContainer');
        this.decryptedMessage = document.getElementById('decryptedMessage');


        // Card and card content
        this.card = document.querySelector('.card')
        this.cardContent = document.querySelector('.card-content')

        // Processing overlay
        this.processingOverlay = document.createElement('div');
        this.processingOverlay.className = 'processing-overlay';
        this.processingOverlay.innerHTML = `
            <div class="processing-content">
                <img src="" alt="Processing Image" class="processing-image"/>
                <div class="processing-dots"></div>
            </div>
        `;
        document.body.appendChild(this.processingOverlay);
        this.processingImage = this.processingOverlay.querySelector('.processing-image')
    }

   attachEventListeners() {
        this.embedForm.addEventListener('submit', (e) => this.handleEmbedSubmit(e));
        this.decryptForm.addEventListener('submit', (e) => this.handleDecryptSubmit(e));
           // Image upload listeners
        const imageEmbedInput = document.getElementById('imageEmbed');
        const imageDecryptInput = document.getElementById('imageDecrypt');
        imageEmbedInput.addEventListener('change', (e) => this.handleImageUpload(e.target, "embed"));
        imageDecryptInput.addEventListener('change', (e) => this.handleImageUpload(e.target, "decrypt"));


        // Add input validation for x0
        const x0Inputs = document.querySelectorAll('input[name="x0"]');
        x0Inputs.forEach(input => {
            input.addEventListener('input', (e) => this.validateX0Input(e.target));
        });
    }
        handleImageUpload(input, tabId) {
        const file = input.files[0];
        if (file) {
            const imageUrl = URL.createObjectURL(file);
            this.card.style.backgroundImage = `url('${imageUrl}')`;
            this.card.style.backgroundSize = `cover`;
             // Clear the card's background image when the tab is changed
            const tabButton = document.querySelector(`[data-tab="${tabId}"]`)
            tabButton.addEventListener("click", () => {
                this.card.style.backgroundImage = ""
                this.clearDecryptedMessage()
            })
            this.clearDecryptedMessage()
        }
    }


    validateX0Input(input) {
        let value = parseInt(input.value, 10);
        if (isNaN(value)) {
            input.setCustomValidity('Please enter a valid integer');
        } else if (value < 0 || value > Number.MAX_SAFE_INTEGER) {
            input.setCustomValidity(`Value must be a non-negative integer less than ${Number.MAX_SAFE_INTEGER}`);
        } else {
            input.setCustomValidity('');
        }
    }

    clearDecryptedMessage() {
         this.decryptedMessage.value = "";
         this.decryptedMessageContainer.classList.add("hidden")
    }

     setupTabSwitching() {
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons and content
                tabButtons.forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

                // Add active class to clicked button and corresponding content
                button.classList.add('active');
                const tabId = button.getAttribute('data-tab');
                document.getElementById(tabId).classList.add('active');
                 this.clearDecryptedMessage();
            });
        });
    }

      showProcessing(imageFile) {
           this.processingOverlay.style.display = 'flex';
          if(imageFile){
              const imageUrl = URL.createObjectURL(imageFile)
                this.processingImage.src = imageUrl
                this.card.classList.add("processing")
          }
      }

       hideProcessing() {
          this.processingOverlay.style.display = 'none';
          this.processingImage.src = ""
          this.card.classList.remove("processing")
    }

    async handleEmbedSubmit(event) {
        event.preventDefault();
        this.embedResult.classList.add('hidden');
        this.embedError.classList.add('hidden');

        const formData = new FormData(this.embedForm);
        const imageFile = this.embedForm.querySelector('input[name="image"]').files[0];
        this.showProcessing(imageFile)
        try {
            const response = await fetch('/embed', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                this.downloadSteganoImage(blob, 'stego_image.png');
                this.showResult(this.embedResult, 'Image embedded successfully.');

            } else {
                const errorData = await response.json();
                this.showResult(this.embedError, errorData.error, true);
            }
        } catch (error) {
            this.showResult(this.embedError, 'An error occurred during embedding.', true);
        } finally {
            this.hideProcessing();
        }
    }

    async handleDecryptSubmit(event) {
        event.preventDefault();
        this.decryptResult.classList.add('hidden');
        this.decryptError.classList.add('hidden');

        const formData = new FormData(this.decryptForm);
         const imageFile = this.decryptForm.querySelector('input[name="image"]').files[0];
        this.showProcessing(imageFile)
        try {
            const response = await fetch('/decrypt', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                console.log("message is ", data.message);
                 this.decryptedMessage.value = data.message;
                 console.log("message is ", this.decryptedMessage.value);
                 this.decryptedMessageContainer.style.display = "block";
                  this.showResult(this.decryptResult, 'Decryption successful.');
            } else {
                const errorData = await response.json();
                  this.clearDecryptedMessage();
                this.showResult(this.decryptError, errorData.error, true);
            }
        } catch (error) {
             this.clearDecryptedMessage();
            this.showResult(this.decryptError, 'An error occurred during decryption.', true);
        } finally {
            this.hideProcessing();
        }
    }

    downloadSteganoImage(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showResult(element, message, isError = false) {
         console.log("showResult: ", message)
        element.textContent = message;
        element.classList.remove('hidden');
        if (isError) {
             element.classList.add('error')
             element.classList.remove('success')
        }
        else {
            element.classList.remove('error')
            element.classList.add('success')
        }
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SteganographyApp();
});