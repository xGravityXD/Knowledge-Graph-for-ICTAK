import pandas as pd
import re
from pathlib import Path

INPUT_FILE = "data/output/courses_and_modules.csv"
OUTPUT_FILE = "data/output/courses_and_modules_cleaned.csv"


def clean_and_split_modules(mod_text):
    if not isinstance(mod_text, str):
        return []

    text = mod_text.strip()

    # Replace long paragraphs with line breaks
    text = re.sub(r"[;•\-\n]+", "\n", text)

    # Split by common delimiters
    parts = re.split(r"[,\n]+", text)

    cleaned = []

    for p in parts:
        p = p.strip()

        # Skip empty or useless lines
        if not p:
            continue

        # Skip extremely long paragraphs (PDF artifacts)
        if len(p) > 80:
            continue

        # Remove numbering
        p = re.sub(r"^\d+[\)\.\- ]+", "", p)
        p = re.sub(r"^Module\s*\d+[:\- ]*", "", p, flags=re.I)

        # Remove leftover symbols
        p = p.replace("•", "").strip()

        if len(p) > 1:
            cleaned.append(p)

    return cleaned


def main():
    df = pd.read_csv(INPUT_FILE)

    cleaned_courses = []

    for _, row in df.iterrows():
        course = row["course_name"]
        modules_raw = row["modules"]

        modules_cleaned = clean_and_split_modules(modules_raw)

        cleaned_courses.append({
            "course_name": course,
            "modules": ", ".join(modules_cleaned)
        })

    out_df = pd.DataFrame(cleaned_courses)
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUTPUT_FILE, index=False)

    print("Cleaned modules saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
