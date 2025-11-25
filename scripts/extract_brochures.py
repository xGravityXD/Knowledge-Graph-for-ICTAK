
import pdfplumber
import pytesseract
from PIL import Image
import re
import pandas as pd
from pathlib import Path
import warnings
import logging
import os

# Silence noisy logs
warnings.filterwarnings("ignore")
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# Try to set tesseract from env if provided
TES_PATH = os.environ.get("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = TES_PATH

def extract_text_from_pdf(pdf_path: Path) -> str:
    text_content = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                # OCR fallback
                try:
                    image = page.to_image(resolution=220).original
                    text = pytesseract.image_to_string(image)
                except Exception:
                    text = ""
            text_content += "\n" + (text or "")
    return text_content

def extract_course_name(text: str) -> str:
    cleaned = " ".join(text.split())

    patterns = [
        r"(Certified\s+(?:Specialist|Professional|Analyst|Engineer|Expert|Programmer)\s+in\s+[A-Za-z0-9\s/&()\-]+)",
        r"(Essential\s+Skill\s+Program\s+[A-Za-z0-9\s/&()\-]+)",
        r"(Industry\s+Readiness\s+Program\s+[A-Za-z0-9\s/&()\-]+)",
        r"([A-Za-z\s]+Programming)\s*(?:Agenda|Objectives|About)",
    ]

    for pat in patterns:
        m = re.search(pat, cleaned, flags=re.IGNORECASE)
        if m:
            course = re.sub(r"\s+", " ", m.group(1).strip())
            return course.title()

    # Fallback: lines that include "Certified" across lines
    lines = [ln.strip() for ln in text.split("\n")]
    for i, ln in enumerate(lines):
        if "Certified" in ln:
            nxt = lines[i+1] if i+1 < len(lines) else ""
            combo = (ln + " " + nxt).strip()
            combo = re.sub(r"\s+", " ", combo)
            if len(combo) > 10:
                return combo.title()

    return "Unknown Course"

def extract_modules(text: str) -> list:
    modules = []

    # Pattern 1: "Module X - Title"
    for line in text.split("\n"):
        line_strip = line.strip()
        if re.match(r"Module\s*\d+\s*[-–]\s*.+", line_strip, flags=re.IGNORECASE):
            modules.append(re.sub(r"\s+", " ", line_strip))

    # Pattern 2: Agenda section bullets
    if not modules and "Agenda" in text:
        section = ""
        try:
            if "Job Roles" in text:
                section = text.split("Agenda", 1)[1].split("Job Roles", 1)[0]
            elif "Learning Outcome" in text:
                section = text.split("Agenda", 1)[1].split("Learning Outcome", 1)[0]
            else:
                section = text.split("Agenda", 1)[1]
        except Exception:
            section = ""

        for line in section.split("\n"):
            ls = line.strip(" -•\t")
            if len(ls) > 4 and not any(k in ls for k in ["Agenda", "Certified", "Outcome", "About", "Eligibility"]):
                modules.append(re.sub(r"\s+", " ", ls))

    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for m in modules:
        if m and m not in seen:
            seen.add(m)
            ordered.append(m)
    return ordered

def process_brochures(brochure_folder: str, output_csv: str) -> pd.DataFrame:
    folder = Path(r'D:\knowledge_graph_builder\brochures')
    results = []
    for pdf_file in folder.glob("*.pdf"):
        print(f"[Brochure] Processing: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)
        course = extract_course_name(text)
        modules = extract_modules(text)

        if modules:
            results.append({
                "course_name": course,
                "modules": ", ".join(modules)
            })
        else:
            print(f"  ⚠ No modules found in {pdf_file.name}")

    df = pd.DataFrame(results, columns=["course_name", "modules"])
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.drop_duplicates().to_csv(output_csv, index=False)
    return df

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--brochures", default="data/brochures", help="Folder containing brochures")
    ap.add_argument("--out", default="data/output/courses_and_modules.csv")
    args = ap.parse_args()
    df = process_brochures(args.brochures, args.out)
    print(f"Saved {len(df)} rows to {args.out}")
