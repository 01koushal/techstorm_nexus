from flask import Flask, render_template, request
import os
import PyPDF2
import fitz
from pyzbar.pyzbar import decode
from PIL import Image
import io
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ====== Utility Functions ======

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            return "".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        return None

def extract_images_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        images = []
        for page in doc:
            for img in page.get_images(full=True):
                base_image = doc.extract_image(img[0])
                image_bytes = base_image["image"]
                images.append(Image.open(io.BytesIO(image_bytes)))
        return images
    except:
        return []

def detect_qr_platform(pdf_path):
    for image in extract_images_from_pdf(pdf_path):
        for obj in decode(image):
            qr_data = obj.data.decode("utf-8").strip()
            if qr_data.startswith("{"):
                try:
                    qr_json = json.loads(qr_data)
                    if "issuanceDate" in qr_json and "credentialSubject" in qr_json:
                        return "infosys"
                except:
                    pass
            if qr_data.startswith("http"):
                return "alison"
    return None

def is_image_based_pdf(pdf_path):
    return not extract_text_from_pdf(pdf_path) and bool(extract_images_from_pdf(pdf_path))

def detect_certification_platform(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    if text and "coursera" in text.lower():
        return "coursera"
    qr = detect_qr_platform(pdf_path)
    if qr:
        return qr
    return "udemy" if is_image_based_pdf(pdf_path) else "saylor"

# ====== Dynamically Run Platform Logic ======

def execute_script(platform, pdf_path):
    try:
        if platform == "coursera":
            import coursera
            return coursera.run_verification(pdf_path)
        elif platform == "udemy":
            import udemy
            return udemy.run_verification(pdf_path)
        elif platform == "alison":
            import alison
            return alison.run_verification(pdf_path)
        elif platform == "saylor":
            import saylor
            return saylor.run_verification(pdf_path)
        elif platform == "infosys":
            import infosys
            return infosys.run_verification(pdf_path)
        else:
            return "❌ No matching script found for platform."
    except Exception as e:
        return f"❌ Error running verification for {platform}: {str(e)}"

# ====== Routes ======

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    file = request.files['certificate']
    if not file or not file.filename.endswith('.pdf'):
        return "Please upload a valid PDF", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    platform = detect_certification_platform(filepath)
    output = execute_script(platform, filepath)

    return render_template("result.html", platform=platform.capitalize(), output=output)

# ====== Run App ======

if __name__ == '__main__':
    app.run(debug=True)
