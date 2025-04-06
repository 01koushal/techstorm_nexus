import fitz  # PyMuPDF
from pyzbar.pyzbar import decode
from PIL import Image
import io
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def extract_qr_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    img_list = page.get_images(full=True)

    for img in img_list:
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image = Image.open(io.BytesIO(image_bytes))
        decoded_objects = decode(image)
        for obj in decoded_objects:
            if obj.type == 'QRCODE':
                return obj.data.decode('utf-8')
    return None

def extract_text_from_certificate(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)
    return text.strip()

def extract_details_from_certificate(pdf_path):
    text = extract_text_from_certificate(pdf_path)
    lines = text.split("\n")
    name = lines[0].strip() if len(lines) > 0 else None
    course_name = lines[1].strip() if len(lines) > 1 else None
    return {"name": name, "course_name": course_name}

def scrape_with_selenium(url):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)

        page_text = driver.find_element(By.TAG_NAME, "body").text
        page_title = driver.title
        driver.quit()

        name_match = re.search(r"verify that (.+?) has completed", page_text)
        course_match = re.search(r"course (.+?) on Alison", page_text)

        name = name_match.group(1).strip() if name_match else None
        course_name = course_match.group(1).strip() if course_match else None

        return {"title": page_title, "content": page_text, "name": name, "course_name": course_name}
    
    except Exception as e:
        return {"error": f"Selenium failed: {str(e)}"}

def is_course_match(pdf_course, url_course):
    if not pdf_course or not url_course:
        return False
    pdf_course_cleaned = pdf_course.replace(" - Revised", "").strip()
    return pdf_course_cleaned.lower() == url_course.lower()

# ✅ This function is called from your Flask app
def run_verification(pdf_path):
    qr_url = extract_qr_from_pdf(pdf_path)
    if not qr_url:
        return "❌ No QR code found on certificate."

    page_data = scrape_with_selenium(qr_url)
    if "error" in page_data:
        return f"❌ {page_data['error']}"

    pdf_details = extract_details_from_certificate(pdf_path)

    name_match = (pdf_details["name"] == page_data["name"])
    course_match = is_course_match(pdf_details["course_name"], page_data["course_name"])

    if name_match and course_match:
        return f"✅ Valid Alison Certificate for {pdf_details['name']} - {pdf_details['course_name']}"
    else:
        return (
            f"❌ Fake Certificate\n\n"
            f"Expected Name: {page_data['name']} | Found: {pdf_details['name']}\n"
            f"Expected Course: {page_data['course_name']} | Found: {pdf_details['course_name']}"
        )
