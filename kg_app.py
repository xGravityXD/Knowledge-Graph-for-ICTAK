import streamlit as st
import networkx as nx
import pandas as pd
from pathlib import Path
from pyvis.network import Network
import pickle


# ---------------------------
# SAFE CSV LOADER
# ---------------------------
def load_csv(path, expected_cols):
    p = Path(path)
    if not p.exists():
        st.warning(f"Missing CSV: {p}")
        return pd.DataFrame(columns=expected_cols)

    df = pd.read_csv(p)
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""
    return df.fillna("")


# -----------------------------------------------------------
# ✅ BUILD KNOWLEDGE GRAPH (NO TRAINERS.CSV)
# -----------------------------------------------------------
def build_graph(courses_csv, students_csv, trainer_skills_csv):
    cm = load_csv(courses_csv, ["course_name", "modules"])
    st_df = load_csv(students_csv, ["student_name", "enrolled"])
    ts = load_csv(trainer_skills_csv, ["trainer_name", "skills"])

    G = nx.DiGraph()

    # -------------------------
    # COURSES + MODULES
    # -------------------------
    for _, r in cm.iterrows():
        course = r["course_name"].strip()
        modules = [m.strip() for m in str(r["modules"]).split(",") if m.strip()]

        G.add_node(course, type="Course")
        for m in modules:
            G.add_node(m, type="Module")
            G.add_edge(course, m, relation="has_module")

    # -------------------------
    # TRAINERS (+ SKILLS) + AUTO COURSE MAPPING
    # -------------------------
    for _, r in ts.iterrows():
        trainer = r["trainer_name"].strip()
        skills = [s.strip().lower() for s in str(r["skills"]).split(",") if s.strip()]

        G.add_node(trainer, type="Trainer")

        # Add skill nodes
        for sk in skills:
            G.add_node(sk, type="Skill")
            G.add_edge(trainer, sk, relation="skilled_in")

        # Auto map trainer → course if skill appears in modules
        for _, c in cm.iterrows():
            course_name = c["course_name"]
            module_text = str(c["modules"]).lower()

            if any(sk in module_text for sk in skills):
                G.add_edge(trainer, course_name, relation="teaches")

    # -------------------------
    # STUDENTS + ENROLLMENT
    # -------------------------
    for _, r in st_df.iterrows():
        student = r["student_name"].strip()
        course = r["enrolled"].strip()

        if not student:
            continue

        G.add_node(student, type="Student")

        if course:
            G.add_node(course, type="Course")
            G.add_edge(student, course, relation="enrolled_in")

    return G


# -----------------------------------------------------------
# ✅ ADVANCED FILTERING
# -----------------------------------------------------------
def filter_graph(G, keyword, allowed_types, hops):
    kw = keyword.lower().strip()

    # Filter by node type
    nodes = [n for n, d in G.nodes(data=True) if d.get("type") in allowed_types]

    # Further filter by keyword
    if kw:
        nodes = [n for n in nodes if kw in n.lower()]

    if not nodes:
        return nx.DiGraph()

    keep = set(nodes)

    # Expand by hop distance
    for _ in range(hops):
        expanded = set()
        for n in keep:
            expanded.update(G.successors(n))
            expanded.update(G.predecessors(n))
        keep.update(expanded)

    return G.subgraph(keep).copy()


# -----------------------------------------------------------
# ✅ CLEAN VISUALIZATION
# -----------------------------------------------------------
def show_graph(G, layout, show_labels, glow):

    net = Network(
        height="750px",
        width="100%",
        bgcolor="#0d1117",
        font_color="white",
        directed=True,
    )

    colors = {
        "Course": "#FFA726",
        "Module": "#42A5F5",
        "Trainer": "#66BB6A",
        "Student": "#FF7043",
        "Skill": "#AB47BC",
        "Unknown": "#BDBDBD",
    }

    # ✅ Add nodes
    for n, attrs in G.nodes(data=True):
        t = attrs.get("type", "Unknown")

        net.add_node(
            n,
            label=n if show_labels else "",
            color=colors.get(t, "#CCCCCC"),
            shape="dot",
            size=18,
            borderWidth=3 if glow else 1,
            shadow=glow,
            title=f"{n} ({t})"
        )

    # ✅ Add edges
    for u, v, attrs in G.edges(data=True):
        rel = attrs.get("relation", "")
        net.add_edge(u, v, arrows="to", label=rel if show_labels else "")

    # ✅ Layout settings (JSON safe)
    if layout == "Hierarchical":
        options = r"""
        {
          "layout": {
            "hierarchical": {
              "enabled": true,
              "direction": "LR",
              "levelSeparation": 200,
              "nodeSpacing": 200
            }
          },
          "physics": { "enabled": false }
        }
        """
    else:
        options = r"""
        {
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -20000,
              "centralGravity": 0.15,
              "springLength": 150,
              "springConstant": 0.05,
              "damping": 0.08,
              "avoidOverlap": 1
            }
          }
        }
        """

    net.set_options(options)

    net.write_html("kg_final_ui.html")
    with open("kg_final_ui.html", "r", encoding="utf-8") as f:
        st.components.v1.html(f.read(), height=760, scrolling=False)


# -----------------------------------------------------------
# ✅ STREAMLIT APP
# -----------------------------------------------------------
st.set_page_config(page_title="ICTAK Knowledge Graph", layout="wide")
st.title("🌐 ICTAK Knowledge Graph")


# ✅ SIDEBAR WITH UNIQUE KEYS (IMPORTANT)
with st.sidebar:
    st.header("🔍 Search & Filters")

    keyword = st.text_input("Search keyword:", "", key="search_keyword_input")

    allowed_types = st.multiselect(
        "Node Types to Display:",
        ["Course", "Module", "Trainer", "Student", "Skill"],
        default=["Course", "Module", "Trainer", "Skill"],
        key="allowed_types_selector"
    )

    hops = st.slider("Expand Relationships (Hops)", 0, 3, 1, key="hops_slider")

    layout = st.selectbox(
        "Layout:",
        ["Force-Directed", "Hierarchical"],
        key="layout_selector"
    )

    show_labels = st.checkbox("Show Labels", True, key="labels_checkbox")
    glow = st.checkbox("Glow Effects", True, key="glow_checkbox")


# ✅ Build graph (uses ONLY courses, students, trainer_skills)
G = build_graph(
    "data/output/courses_and_modules.csv",
    "data/students.csv",
    "data/output/trainer_skills.csv",
)

# ✅ Filter graph
subG = filter_graph(G, keyword, allowed_types, hops)

# ✅ Display
show_graph(subG, layout, show_labels, glow)


# -----------------------------------------------------------
# ✅ DOWNLOAD SECTION
# -----------------------------------------------------------

st.subheader("📥 Download Filtered Graph Data")

# Prepare CSVs
nodes_df = pd.DataFrame([
    {"node": n, "type": d.get("type", "Unknown")}
    for n, d in subG.nodes(data=True)
])

edges_df = pd.DataFrame([
    {"source": u, "target": v, "relation": d.get("relation", "")}
    for u, v, d in subG.edges(data=True)
])

# Download nodes
st.download_button(
    "📄 Download Nodes (CSV)",
    nodes_df.to_csv(index=False),
    "nodes.csv",
    "text/csv",
    key="download_nodes"
)

# Download edges
st.download_button(
    "🔗 Download Edges (CSV)",
    edges_df.to_csv(index=False),
    "edges.csv",
    "text/csv",
    key="download_edges"
)

# Download full graph as pickle
pickle_bytes = pickle.dumps(G)
st.download_button(
    "🧠 Download Full Graph (Pickle)",
    pickle_bytes,
    "full_graph.pkl",
    "application/octet-stream",
    key="download_pickle"
)

# Download interactive HTML
with open("kg_final_ui.html", "rb") as f:
    html_data = f.read()

st.download_button(
    "🌐 Download Interactive Graph (HTML)",
    html_data,
    "interactive_graph.html",
    "text/html",
    key="download_html"
)
