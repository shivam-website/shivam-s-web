from flask import Flask, render_template, request, jsonify
import pytesseract
from PIL import Image
import datetime
import webbrowser
import requests
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config.update({
    'UPLOAD_FOLDER': 'uploads',
    'ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg', 'gif'},
    'MAX_CONTENT_LENGTH': 5 * 1024 * 1024  # 5MB max upload size
})

# Initialize Tesseract
pytesseract.pytesseract.tesseract_cmd = ("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# Get API key from environment
api_key = ("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 ")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def ask_ai(prompt):
    """Query OpenRouter API with improved error handling"""
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            },
            timeout=30  # Add timeout
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"API Error: {str(e)}"
    except KeyError:
        return "Error processing API response"

def process_image(image_path, instruction=None):
    """Process image with error handling"""
    try:
        extracted_text = pytesseract.image_to_string(Image.open(image_path)).strip()
        if instruction:
            return filter_text(extracted_text, instruction)
        return extracted_text
    except Exception as e:
        return f"Image processing error: {str(e)}"

def filter_text(text, instruction):
    """Improved text filtering"""
    return '\n'.join([line for line in text.split('\n') if instruction.lower() in line.lower()])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def handle_query():
    # Handle text/instructions
    instruction = request.form.get('instruction', '').strip()
    image_file = request.files.get('image')
    
    response = None
    
    # Handle image upload
    if image_file and allowed_file(image_file.filename):
        try:
            # Save image temporarily
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(save_path)
            
            # Process image
            extracted_text = process_image(save_path, instruction)
            
            if not extracted_text:
                return jsonify({"response": "No text found in image"})
                
            response = ask_ai(extracted_text)
            
            # Clean up temporary file
            os.remove(save_path)
        except Exception as e:
            return jsonify({"response": f"Error: {str(e)}"})
    
    # Handle text-only query
    if not response and instruction:
        # Handle special commands
        if 'your name' in instruction:
            response = "My name is JARVIS."
        elif 'shivam' in instruction:
            response = "MR.Shivam is my developer."
        elif 'time' in instruction:
            response = datetime.datetime.now().strftime('%I:%M %p')
        elif 'date' in instruction:
            response = datetime.datetime.now().strftime('%B %d, %Y')
        elif 'open youtube' in instruction:
            webbrowser.open("https://youtube.com")
            response = "Opening YouTube"
        elif 'open google' in instruction:
            webbrowser.open("https://google.com")
            response = "Opening Google"
        elif 'play music' in instruction:
            webbrowser.open("https://youtu.be/IrZC5H5ZSm8?si=SWddD_ohU8xW65Lw")
            response = "Playing music"
        else:
            response = ask_ai(instruction)
    
    if not response:
        return jsonify({"response": "Please provide either text or image input"})
    
    return jsonify({"response": response.replace("\n", "\n\n")})  # Preserve paragraphs

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=False)  # Disable debug in production