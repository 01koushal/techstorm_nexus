import fitz  # PyMuPDF
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse

TRUSTED_DOMAINS = {
    "coursera.org": "coursera",
    "www.coursera.org": "coursera",
    "udemy.com": "udemy",
    "www.udemy.com": "udemy",
    "ude.my": "udemy",
    "nptel.ac.in": "nptel",
    "www.nptel.ac.in": "nptel",
    "edx.org": "edx",
    "www.edx.org": "edx"
}

def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

def extract_verification_link(text):
    text = text.replace("\n", " ").replace("  ", " ")
    match = re.search(r"https?://[a-zA-Z0-9./\-]+", text)
    return match.group(0).strip() if match else None

def detect_platform(verification_link, extracted_text):
    if verification_link:
        domain = urlparse(verification_link).netloc.lower()
        return TRUSTED_DOMAINS.get(domain, "unknown")
    if "Udemy" in extracted_text or "Certificate of Completion" in extracted_text:
        return "udemy"
    return "unknown"

def get_name_from_verification_page(verification_link):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.get(verification_link)
        time.sleep(10)
        all_text = driver.execute_script("return document.body.innerText;")
        driver.quit()

        match = re.search(r"This is to certify that\s+([A-Za-z\s]+)", all_text)
        if match:
            return match.group(1).strip()

        match = re.search(r"Completed by\s+([A-Za-z]+)\s+([A-Za-z]+)", all_text)
        if match:
            return f"{match.group(1)} {match.group(2)}"

        return "Name Not Found in Extracted Text"
    except Exception as e:
        return f"Error: {e}"

def extract_details(file_path):
    extracted_text = extract_text_from_pdf(file_path)
    verification_link = extract_verification_link(extracted_text)
    platform = detect_platform(verification_link, extracted_text)
    return extracted_text, verification_link, platform

# ✅ This is what your Flask app will now call
def run_verification(file_path):
    extracted_text, verification_link, platform = extract_details(file_path)

    if platform in ["coursera", "udemy"]:
        if not verification_link:
            return "❌ No verification link found. Possibly Fake."

        student_name_from_web = get_name_from_verification_page(verification_link)
        if not student_name_from_web or "Error" in student_name_from_web:
            return "❌ Unable to retrieve student name. Check the verification page manually."

        extracted_name = extracted_text.split("\n")[1].strip()

        if extracted_name.lower() == student_name_from_web.lower():
            return f"✅ Valid {platform.capitalize()} Certificate for {extracted_name}"
        else:
            return f"❌ Fake Certificate (Expected: {student_name_from_web}, Found: {extracted_name})"

    return f"❌ Unknown platform '{platform}'. Cannot verify certificate."
