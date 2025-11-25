import pdfplumber
import pytesseract
from PIL import Image
import re
import pandas as pd
from pathlib import Path
import warnings
import logging

# --- Setup ---
warnings.filterwarnings("ignore")
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# ✅ Change this to your local Tesseract path if needed
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---------------- TEXT EXTRACTION ----------------
def extract_text_from_pdf(pdf_path):
    """Extracts text from both text-based and image-based PDFs"""
    text_content = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                img = page.to_image(resolution=200).original
                text = pytesseract.image_to_string(img)
            text_content += "\n" + (text or "")
    return text_content


# ---------------- COURSE EXTRACTION ----------------
def extract_course_name(text):
    """Extracts course name from various ICTAK brochure types"""
    cleaned = " ".join(text.split())

    # Try multiple patterns (Certified, Essential, Industry Readiness, etc.)
    patterns = [
        r"(Certified\s+(?:Specialist|Professional|Analyst|Engineer|Expert|Programmer)\s+in\s+[A-Za-z\s/&()]+)",
        r"(Essential\s+Skill\s+Program\s+[A-Za-z\s/&()]+)",
        r"(Industry\s+Readiness\s+Program\s+[A-Za-z\s/&()]+)",
        r"(Python\s+Programming)",
    ]

    for pat in patterns:
        match = re.search(pat, cleaned, re.IGNORECASE)
        if match:
            course = re.sub(r"\s+", " ", match.group(1).strip())
            return course.title()

    # Fallback: try a "Certified" word followed by two lines
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "Certified" in line:
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            combined = (line + " " + next_line).strip()
            return re.sub(r"\s+", " ", combined.title())

    return "Unknown Course"


# ---------------- MODULE EXTRACTION ----------------
def extract_modules(text):
    """Extracts modules or agenda items"""
    modules = []

    # --- Case 1: 'Module X - ...' pattern ---
    for line in text.split("\n"):
        line = line.strip()
        if re.match(r"Module\s*\d+\s*[-–]", line, re.IGNORECASE):
            modules.append(line)

    # --- Case 2: 'Agenda' section ---
    if not modules and "Agenda" in text:
        try:
            section = ""
            if "Job Roles" in text:
                section = text.split("Agenda")[1].split("Job Roles")[0]
            elif "Learning Outcome" in text:
                section = text.split("Agenda")[1].split("Learning Outcome")[0]
            else:
                section = text.split("Agenda")[1]
            for line in section.split("\n"):
                line = line.strip()
                if len(line) > 5 and not any(k in line for k in ["Agenda", "Certified", "Outcome", "About"]):
                    modules.append(line)
        except Exception:
            pass

    # Clean and deduplicate
    modules = [re.sub(r"\s+", " ", m).strip() for m in modules if m]
    return list(dict.fromkeys(modules))  # preserve order


# ---------------- PROCESS ALL BROCHURES ----------------
def process_brochures(folder_path):
    folder = Path(folder_path)
    results = []

    for pdf_file in folder.glob("*.pdf"):
        print(f"📄 Processing: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)
        course = extract_course_name(text)
        modules = extract_modules(text)

        if not modules:
            print(f"⚠️ No modules found in {pdf_file.name}")
        else:
            module_str = ", ".join(modules)
            results.append({
                "course_name": course,
                "modules": module_str
            })
            print(f"✅ Found {len(modules)} modules for {course}")

    return results


# ---------------- SAVE RESULTS ----------------
def save_to_csv(results):
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "courses_and_modules.csv"

    df = pd.DataFrame(results)
    df.drop_duplicates(inplace=True)
    df.to_csv(output_path, index=False)

    print(f"\n✅ Saved to: {output_path.resolve()}")
    print(df.head())


# ---------------- MAIN ----------------
if __name__ == "__main__":
    folder_path = input("Enter folder path containing brochures: ").strip()
    data = process_brochures(folder_path)
    save_to_csv(data)
