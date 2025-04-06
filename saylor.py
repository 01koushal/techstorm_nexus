import fitz  # PyMuPDF
import re
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text("text") for page in doc])

def normalize_text(text):
    return re.sub(r'\s+|\.', ' ', text).strip().upper()

def get_certificate_details(text):
    student_name = re.search(r"^(.*)\n[A-Z]+\d{3}:", text, re.MULTILINE)
    course_name = re.search(r"([A-Z]+\d{3}: .+)", text)
    cert_id = re.search(r"\b\d{8,12}[A-Z]{0,3}\b", text)

    cert_url = f"https://learn.saylor.org/admin/tool/certificate/index.php?code={cert_id.group(0)}" if cert_id else None

    return (
        student_name.group(1).strip().rstrip('.') if student_name else None,
        course_name.group(1).strip() if course_name else None,
        cert_id.group(0).strip() if cert_id else None,
        cert_url
    )

def verify_certificate(cert_url, student_name, course_name):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(cert_url)
        time.sleep(3)

        verify_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Verify']")
        verify_button.click()
        time.sleep(3)

        verified_name = driver.find_element(By.XPATH, "//td[text()='Full name']/following-sibling::td").text.strip()
        verified_course = driver.find_element(By.XPATH, "//td[text()='Certificate']/following-sibling::td").text.strip()

        if normalize_text(student_name) == normalize_text(verified_name) and normalize_text(course_name) == normalize_text(verified_course):
            return f"""Certificate is verified and authentic.

🔹 Name: {verified_name}
🔹 Course: {verified_course}
🔹 Certificate URL: {cert_url}"""
        else:
            return " Certificate details do not match."

    except Exception as e:
        return f" Error during verification: {e}"
    finally:
        driver.quit()

def run_verification(pdf_path):
    extracted_text = extract_text_from_pdf(pdf_path)
    student_name, course_name, cert_id, cert_url = get_certificate_details(extracted_text)

    if not student_name or not course_name or not cert_id or not cert_url:
        return " Could not extract all required details from the PDF."

    return verify_certificate(cert_url, student_name, course_name)
