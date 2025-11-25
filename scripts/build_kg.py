
import pandas as pd
import networkx as nx
import os

def build_kg(courses_modules_csv: str,
             trainers_csv: str,
             students_csv: str,
             trainer_skills_csv: str | None = None) -> nx.DiGraph:
    G = nx.DiGraph()

    # Load core data
    cm = pd.read_csv(courses_modules_csv) if courses_modules_csv else pd.DataFrame(columns=["course_name","modules"])
    trainers = pd.read_csv(trainers_csv) if trainers_csv else pd.DataFrame(columns=["trainer_name","teaches"])
    students = pd.read_csv(students_csv) if students_csv else pd.DataFrame(columns=["student_name","enrolled"])
    tskills = pd.read_csv(trainer_skills_csv) if (trainer_skills_csv and len(trainer_skills_csv)>0 and os.path.exists(trainer_skills_csv)) else pd.DataFrame(columns=["trainer_name","skills"])

    # Courses & Modules
    for _, row in cm.iterrows():
        course = str(row["course_name"]).strip()
        if not course:
            continue
        G.add_node(course, type="Course")

        modules = [m.strip() for m in str(row["modules"]).split(",") if m.strip()]
        for mod in modules:
            G.add_node(mod, type="Module")
            G.add_edge(course, mod, relation="has_module")

    # Trainers & teaches edges
    for _, row in trainers.iterrows():
        trainer = str(row["trainer_name"]).strip()
        G.add_node(trainer, type="Trainer")
        teach_list = [t.strip() for t in str(row.get("teaches","")).split(",") if t.strip()]
        for c in teach_list:
            if c not in G:
                G.add_node(c, type="Course")
            G.add_edge(trainer, c, relation="teaches")

    # Students & enrollment
    for _, row in students.iterrows():
        student = str(row["student_name"]).strip()
        course = str(row.get("enrolled","")).strip()
        if not student or not course:
            continue
        if course not in G:
            G.add_node(course, type="Course")
        G.add_node(student, type="Student")
        G.add_edge(student, course, relation="enrolled_in")

    # Trainer skills (optional) + skill-to-module links
    if not tskills.empty:
        for _, row in tskills.iterrows():
            tr = str(row["trainer_name"]).strip()
            skills = [s.strip() for s in str(row.get("skills","")).split(",") if s.strip()]
            if tr not in G:
                G.add_node(tr, type="Trainer")
            for sk in skills:
                G.add_node(sk, type="Skill")
                G.add_edge(tr, sk, relation="skilled_in")

        # link skills to modules if name appears inside module text (bag-of-words heuristic)
        for mod, mdata in [(n, d) for n, d in G.nodes(data=True) if d.get("type")=="Module"]:
            ml = mod.lower()
            for sk in [n for n, d in G.nodes(data=True) if d.get("type")=="Skill"]:
                if sk.lower() in ml:
                    G.add_edge(sk, mod, relation="relevant_to")

    return G

def keyword_subgraph(G: nx.DiGraph, keyword: str) -> nx.DiGraph:
    kw = (keyword or "").lower().strip()
    if not kw:
        return G
    seed = [n for n in G.nodes() if kw in n.lower()]
    keep = set(seed)
    for n in seed:
        nbrs = list(G.successors(n)) + list(G.predecessors(n))
        keep.update(nbrs)
        # also include neighbors of neighbors for context
        for nb in nbrs:
            keep.update(list(G.successors(nb)))
            keep.update(list(G.predecessors(nb)))
    return G.subgraph(keep).copy()
