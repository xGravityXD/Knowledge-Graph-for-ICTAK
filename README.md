
# ICTAK Knowledge Graph Builder (Free, Local)

End-to-end pipeline to extract **courses & modules** from ICTAK brochures, parse **faculty LinkedIn resumes** for skills, and build a **searchable knowledge graph** (Courses ↔ Modules ↔ Trainers ↔ Students ↔ Skills).

## ✨ Features
- PDF extraction with OCR fallback (Tesseract)
- Works across multiple brochure formats (Industry Readiness, Essential Skill Program, etc.)
- Faculty resume parsing → skills extraction (keyword-based)
- Knowledge Graph using NetworkX
- Interactive visualization with PyVis
- Streamlit UI for uploads and keyword search

## 📦 Setup

```bash
python -m venv .venv
. .venv/Scripts/activate    # Windows
pip install -r requirements.txt
```

Install Tesseract OCR engine (if you need OCR fallback):
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Then set env var (example): `set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe`

## 🚀 Run
```bash
streamlit run app.py
```

## 📁 Inputs
- Upload brochures (PDF) → extracts `courses_and_modules.csv`
- Upload resumes (PDF) → extracts `trainer_skills.csv`
- Upload `trainers.csv` (columns: `trainer_name, teaches`)
- Upload `students.csv` (columns: `student_name, enrolled`)

## 🔎 Search
Type a keyword (e.g., "Python", "MERN", "Selenium") and the graph filters to the relevant subgraph including neighbors.

