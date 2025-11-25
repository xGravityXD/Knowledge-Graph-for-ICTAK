import pdfplumber
import pandas as pd
from pathlib import Path
import re

# Extend/adjust as you like
DEFAULT_SKILLS = [
    "python","java","javascript","react","reactjs","node","nodejs","express",
    "mongodb","sql","linux","cloud","aws","azure","docker","kubernetes",
    "selenium","automation testing","manual testing","cyber security",
    "penetration testing","wireshark","metasploit","nmap","burp suite",
    "html","css","bootstrap","redux","git","github",
    "data science","machine learning","deep learning","nlp"
]

def clean_name_from_filename(stem: str) -> str:
    """
    Convert file stem (e.g., 'Profile (11) - remya_u_l') to a clean person name.
    Rules:
    - Drop common junk tokens (profile, resume, cv, linkedin, ictak)
    - Replace separators with spaces
    - Collapse multiple spaces
    - Title-case words (keeps initials reasonably well)
    """
    s = stem

    # remove common prefixes/junk
    s = re.sub(r"(?i)\b(profile|resume|cv|linkedin|ictak)\b", " ", s)

    # replace separators with spaces
    s = s.replace("_", " ").replace("-", " ")

    # drop bracketed/parenthetical junk like (11)
    s = re.sub(r"\([^)]*\)", " ", s)

    # drop stray digits-only tokens
    s = re.sub(r"\b\d+\b", " ", s)

    # collapse spaces
    s = re.sub(r"\s+", " ", s).strip()

    # if nothing left, fallback
    if not s:
        return stem

    # title-case but keep common uppercase acronyms short
    # (this is simple; you can customize for your names)
    return " ".join(w if w.isupper() and len(w) <= 3 else w.title() for w in s.split())

def extract_text(pdf_path: Path) -> str:
    """We still read text to mine skills; name comes from filename only."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += "\n" + page_text
    except Exception:
        # If text layer fails, just return empty; skills will be blank for this file
        pass
    return text

def extract_skills(text: str, vocab=None):
    """Simple keyword match over résumé text layer."""
    if vocab is None:
        vocab = DEFAULT_SKILLS
    tl = text.lower()
    found = []
    for skill in vocab:
        if skill in tl:
            found.append(skill.title())
    # dedupe & sort for consistency
    return sorted(list(set(found)))

def process_resumes(resume_folder: str, output_csv: str) -> pd.DataFrame:
    folder = Path(r'D:\knowledge_graph_builder\profiles')
    rows = []

    for pdf in folder.glob("*.pdf"):
        trainer_name = clean_name_from_filename(pdf.stem)
        text = extract_text(pdf)
        skills = extract_skills(text)

        rows.append({
            "trainer_name": trainer_name,
            "skills": ", ".join(skills)
        })

    df = pd.DataFrame(rows, columns=["trainer_name", "skills"]).drop_duplicates()
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"✅ Parsed {len(df)} trainers → {output_csv}")
    return df

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumes", default="data/resumes")
    ap.add_argument("--out", default="data/output/trainer_skills.csv")
    args = ap.parse_args()
    process_resumes(args.resumes, args.out)
