import pandas as pd
from pathlib import Path

def generate_trainers_csv(courses_file, trainer_skills_file, output_file):
    courses_df = pd.read_csv(courses_file)
    skills_df = pd.read_csv(trainer_skills_file)

    rows = []

    for _, t in skills_df.iterrows():
        trainer = str(t["trainer_name"]).strip()

        # ✅ Handle missing / NaN skills
        raw_skills = t.get("skills", "")
        if isinstance(raw_skills, float):  # means NaN
            raw_skills = ""

        trainer_skills = [
            s.strip().lower()
            for s in str(raw_skills).split(",")
            if isinstance(s, str) and s.strip()
        ]

        teaches = []

        for _, c in courses_df.iterrows():
            course_name = str(c["course_name"]).strip()
            modules = str(c["modules"]).lower()

            # ✅ Skip if trainer has no skills
            if not trainer_skills:
                continue

            # ✅ Match any skill with course modules
            if any(skill in modules for skill in trainer_skills):
                teaches.append(course_name)

        # ✅ Remove duplicates
        teaches = list(set(teaches))

        rows.append({
            "trainer_name": trainer,
            "teaches": ", ".join(teaches) if teaches else ""
        })

    df = pd.DataFrame(rows, columns=["trainer_name", "teaches"])
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)

    print(f"✅ Generated {len(df)} trainer-course mappings → {output_file}")
    return df


if __name__ == "__main__":
    generate_trainers_csv(
        "data/output/courses_and_modules.csv",
        "data/output/trainer_skills.csv",
        "data/trainers.csv"
    )
