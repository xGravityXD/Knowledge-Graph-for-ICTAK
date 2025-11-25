import argparse
import pandas as pd
import networkx as nx
from pathlib import Path
from pyvis.network import Network
import pickle


# -----------------------------------------------------------
# ✅ Load CSV safely (handles missing columns / missing files)
# -----------------------------------------------------------
def load_csv(path, expected_cols):
    p = Path(path)
    if not p.exists():
        print(f"⚠️ Missing file: {p}")
        return pd.DataFrame(columns=expected_cols)

    df = pd.read_csv(p)

    # Add any missing columns
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    return df[expected_cols].fillna("")


# -----------------------------------------------------------
# ✅ Build the Knowledge Graph
# -----------------------------------------------------------
def build_graph(courses_csv, trainers_csv, students_csv, trainer_skills_csv=None):
    cm = load_csv(courses_csv, ["course_name", "modules"])
    tr = load_csv(trainers_csv, ["trainer_name", "teaches"])
    st = load_csv(students_csv, ["student_name", "enrolled"])

    if trainer_skills_csv:
        ts = load_csv(trainer_skills_csv, ["trainer_name", "skills"])
    else:
        ts = pd.DataFrame(columns=["trainer_name", "skills"])

    G = nx.DiGraph()

    # -------------------------------------------------------
    # ✅ Add Courses & Modules
    # -------------------------------------------------------
    for _, row in cm.iterrows():
        course = str(row["course_name"]).strip()
        if not course:
            continue

        G.add_node(course, type="Course")

        modules = [m.strip() for m in str(row["modules"]).split(",") if m.strip()]

        for mod in modules:
            G.add_node(mod, type="Module")
            G.add_edge(course, mod, relation="has_module")

    # -------------------------------------------------------
    # ✅ Add Trainers & "teaches"
    # -------------------------------------------------------
    for _, row in tr.iterrows():
        trainer = str(row["trainer_name"]).strip()
        if not trainer:
            continue

        G.add_node(trainer, type="Trainer")

        teaches_list = [c.strip() for c in str(row["teaches"]).split(",") if c.strip()]

        for course in teaches_list:
            if course not in G:
                G.add_node(course, type="Course")
            G.add_edge(trainer, course, relation="teaches")

    # -------------------------------------------------------
    # ✅ Add Students & "enrolled_in"
    # -------------------------------------------------------
    for _, row in st.iterrows():
        student = str(row["student_name"]).strip()
        course = str(row["enrolled"]).strip()

        if not student or not course:
            continue

        if course not in G:
            G.add_node(course, type="Course")

        G.add_node(student, type="Student")
        G.add_edge(student, course, relation="enrolled_in")

    # -------------------------------------------------------
    # ✅ Add Trainer Skills (Optional)
    # -------------------------------------------------------
    if not ts.empty:

        for _, row in ts.iterrows():
            trainer = str(row["trainer_name"]).strip()
            skills = [s.strip() for s in str(row["skills"]).split(",") if s.strip()]

            if trainer and trainer not in G:
                G.add_node(trainer, type="Trainer")

            for skill in skills:
                G.add_node(skill, type="Skill")
                G.add_edge(trainer, skill, relation="skilled_in")

        # ✅ Auto-link Skills ↔ Modules
        skill_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "Skill"]

        for module, attrs in G.nodes(data=True):
            if attrs.get("type") != "Module":
                continue

            mod_text = module.lower()

            for skill in skill_nodes:
                if skill.lower() in mod_text:
                    G.add_edge(skill, module, relation="relevant_to")

    return G


# -----------------------------------------------------------
# ✅ Keyword-Based Subgraph Filtering
# -----------------------------------------------------------
def keyword_subgraph(G, keyword):
    kw = keyword.lower().strip()
    if not kw:
        return G.copy()

    # Seed nodes that match keyword
    seeds = [n for n in G.nodes if kw in n.lower()]
    keep = set(seeds)

    # Expand neighborhood
    for n in seeds:
        neighbors = list(G.successors(n)) + list(G.predecessors(n))
        keep.update(neighbors)

        for nb in neighbors:
            keep.update(list(G.successors(nb)))
            keep.update(list(G.predecessors(nb)))

    return G.subgraph(keep).copy()


# -----------------------------------------------------------
# ✅ Generate PyVis HTML safely (NO template errors)
# -----------------------------------------------------------
def to_pyvis_html(G, output_file):
    net = Network(height="750px", width="100%", directed=True,
                  bgcolor="#111111", font_color="white")

    colors = {
        "Course": "#FFA500",
        "Module": "#87CEFA",
        "Trainer": "#98FB98",
        "Student": "#FFC0CB",
        "Skill": "#E6E6FA"
    }

    # Add nodes
    for node, attrs in G.nodes(data=True):
        ntype = attrs.get("type", "Other")
        color = colors.get(ntype, "#CCCCCC")
        title = f"{node}<br>{ntype}"
        net.add_node(node, label=node, color=color, title=title)

    # Add edges
    for u, v, attrs in G.edges(data=True):
        rel = attrs.get("relation", "")
        net.add_edge(u, v, label=rel, title=rel, arrows="to")

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # ✅ Safe HTML writing (no Jinja2 template needed)
    net.write_html(output_file)

    return output_file


# -----------------------------------------------------------
# ✅ Main Entry
# -----------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--courses", default="data/output/courses_and_modules.csv")
    ap.add_argument("--trainers", default="data/trainers.csv")
    ap.add_argument("--students", default="data/students.csv")
    ap.add_argument("--skills", default="data/output/trainer_skills.csv")
    ap.add_argument("--keyword", default="")
    ap.add_argument("--html", default="data/output/kg_result.html")
    ap.add_argument("--pickle", default="data/output/ictak_graph.pkl")
    args = ap.parse_args()

    # ✅ Build the KG
    G = build_graph(args.courses, args.trainers, args.students, args.skills)

    # ✅ Save pickle safely (NetworkX 3.x compatible)
    with open(args.pickle, "wb") as f:
        pickle.dump(G, f)
    print(f"✅ Full graph saved → {args.pickle}")

    # ✅ Filter subgraph by keyword
    sub = keyword_subgraph(G, args.keyword)

    # ✅ Save HTML visualization
    html = to_pyvis_html(sub, args.html)
    print(f"✅ Visualization saved → {html}")
    print(f"✅ Subgraph nodes: {len(sub.nodes())}, edges: {len(sub.edges())}")


if __name__ == "__main__":
    main()
