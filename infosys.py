import fitz  # PyMuPDF for PDF processing
import cv2
import numpy as np
import pytesseract
import json
import os
import re
from pyzbar.pyzbar import decode
from datetime import datetime

# Set up Tesseract OCR (Modify this path if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Set the file path statically (Change this to your actual file)
file_path = input("Enter the path to your certificate PDF: ")

def extract_qr_from_pdf(pdf_path):
    """Extracts QR code from a PDF by converting the first page to an image."""
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap()
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))

    # Convert to OpenCV format
    if img.shape[-1] == 4:
        cv_img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    else:
        cv_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    return extract_qr_from_image_array(cv_img)

def extract_qr_from_image(image_path):
    """Extracts QR code from an image file."""
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not read the image file. Check the path.")
        return None

    return extract_qr_from_image_array(image)

def extract_qr_from_image_array(image):
    """Extracts QR code from an OpenCV image array with enhancements."""
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    qr_codes = decode(gray)
    if qr_codes:
        for qr in qr_codes:
            return qr.data.decode('utf-8')
    return None

def extract_text_from_certificate(file_path):
    """Extracts visible text from the certificate using OCR."""
    text = ""
    if file_path.lower().endswith(".pdf"):
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text")
    else:
        img = cv2.imread(file_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
    return text

def normalize_date(date_text):
    """Converts a date string to 'YYYY-MM-DD' format."""
    try:
        return datetime.strptime(date_text, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return date_text  # If parsing fails, return the original

def verify_certificate(file_path):
    """Verifies if the certificate is real or fake by comparing extracted details with QR data."""
    
    if file_path.lower().endswith(".pdf"):
        qr_data = extract_qr_from_pdf(file_path)
    else:
        qr_data = extract_qr_from_image(file_path)

    if not qr_data:
        print("\nNo QR Code found.")
        return

    print("\nExtracted QR Code Data:", qr_data)

    try:
        qr_json = json.loads(qr_data)
        cert_details = {
            "issuedTo": qr_json["credentialSubject"]["issuedTo"].strip().lower(),
            "course": qr_json["credentialSubject"]["course"].strip().lower(),
            "completedOn": qr_json["credentialSubject"]["completedOn"][:10]  # Extract YYYY-MM-DD
        }
        print("\nExtracted Certificate Details from QR JSON:")
        print("Issued To:", cert_details["issuedTo"])
        print("Course:", cert_details["course"])
        print("Completed On:", cert_details["completedOn"])

    except json.JSONDecodeError:
        print("\nQR Code does not contain JSON. Unable to verify.")
        return

    # Extract text from the certificate
    extracted_text = extract_text_from_certificate(file_path).strip().lower()
    print("\nExtracted Text from Certificate:\n", extracted_text)

    # Normalize the date in OCR text
    match = re.search(r"on (\w+ \d{1,2}, \d{4})", extracted_text)
    ocr_date = normalize_date(match.group(1)) if match else None

    # Verify details
    if (
        cert_details["issuedTo"] in extracted_text and
        cert_details["course"] in extracted_text and
        (ocr_date == cert_details["completedOn"])
    ):
        print("\nCertificate is GENUINE. Data matches the official record.")
    else:
        print("\nCertificate is FAKE. Data does not match official records.")

# Check if the file exists
if os.path.exists(file_path):
    verify_certificate(file_path)
else:
    print("Error: File not found. Please provide a valid file path.")