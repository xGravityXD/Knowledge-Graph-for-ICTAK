📘 ICTAK Knowledge Graph

A complete Knowledge Graph system built for ICTAK that extracts text from PDFs, identifies key entities (courses, modules, trainers, skills), maps relationships, and visualizes everything in an interactive HTML graph.

🚀 Features

🔍 PDF Text Extraction

Reads and cleans data from ICTAK PDF documents
Converts content into a structured format for processing

🧠 Entity Detection

Automatically detects:
Courses
Modules
Trainers
Skills
Topics

🔗 Relationship Mapping

Builds accurate connections such as:
Course → Modules
Module → Skills
Trainer → Courses

🌐 Interactive Graph Visualizations

Generates dynamic HTML graphs using PyVis, including:
kg.html
kg_final_ui.html
kg_smart.html

These visuals allow easy exploration of learning paths and relationships.

🗂 Project Structure
Knowledge-Graph-for-ICTAK/
│
├── data/                   # Source PDFs and processed data
├── lib/                    # Utility modules and helpers
├── scripts/                # Automation scripts
│
├── extract-from-pdf.py     # Extracts and cleans text from PDFs
├── kg_app.py               # Backend logic for building the Knowledge Graph
├── kg.html                 # Basic graph UI
├── kg_final_ui.html        # Enhanced interactive graph UI
├── kg_smart.html           # Smart layout UI

⚙️ How It Works

User provides ICTAK course PDFs
System extracts raw data using Python text-extraction libraries
NLP logic + rules identify entities
NetworkX + PyVis builds a graph
Interactive HTML UIs visualize the graph

🛠 Technologies Used
Python 3
PyPDF / PDFMiner
NetworkX
PyVis
HTML / CSS / JavaScript

📈 Future Improvements

Automated PDF upload UI
Database storage for extracted entities
Search + filter in graph UI
Improved NLP accuracy
Streamlit dashboard to control the pipeline

🤝 Contributions
Contributions, issues, and feature requests are welcome.

📄 License

⚠️ This project currently does not include a license.
This means:
Others cannot reuse, modify, or distribute  without permission
