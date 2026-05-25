# 🌿 GreenOps Refactor

> **AI-Powered Green Software Engineering Dashboard**  
> Analyze, score, and refactor Python code for maximum energy efficiency and minimum carbon footprint.

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)](https://python.org)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![Ollama](https://img.shields.io/badge/AI-Ollama%20qwen2.5-black?logo=ollama)](https://ollama.ai)
[![Carbon Zone](https://img.shields.io/badge/Grid-IN--WE%20Maharashtra-00c853)](https://electricitymaps.com)

---

## 📋 Project Overview

GreenOps Refactor is a comprehensive tool designed to help developers build sustainable software. It uses static code analysis, machine learning, and real-world environmental data to provide a "Green Score" and AI-driven refactoring suggestions.

### 🌟 Key Features

*   **🔍 Static Feature Extraction**: Parses Python code using `libcst` to extract 14 energy-critical features (loops, nesting, recursion, vectorization, etc.).
*   **🧠 ML Energy Prediction**: Uses an XGBoost-powered regression model (selected via 5-fold cross-validation) to estimate energy consumption (kWh).
*   **🌍 Real-time Carbon Tracking**: Fetches live grid intensity data from the **Electricity Maps API** (targeting the Maharashtra IN-WE zone).
*   **⚖️ Relative Green Scoring**: A 0–100 composite index that uses smooth logarithmic scaling to reward even minor efficiency gains.
*   **⚡ AI Refactoring Dashboard**: Generates "Greener" versions of your code using **Ollama (qwen2.5-coder)** with a guaranteed **Before vs. After** comparison of energy and carbon savings.
*   **🛠 Structural Safety Floor**: A physics-based correction engine that ensures the ML model's noise doesn't produce unrealistic energy predictions.

---

## 🗂 Folder Structure

```text
greenops/
├── app.py                  # Flask orchestration & comparative analysis engine
├── benchmark.py            # Training dataset generator
├── context_integrator.py   # Carbon API, hardware context & Green Score math
├── feature_extractor.py    # Static analysis (libcst/ast) traversal logic
├── training_model1.py      # ML pipeline (training, selection & prediction)
├── templates/              # Dashboard UI
│   ├── index.html          # Code submission interface
│   └── result.html         # Comparative analysis & AI results
├── .env.example            # Template for API keys and config
├── Dockerfile              # Multi-stage build for the app
├── docker-compose.yml      # Orchestrates App + Ollama services
├── requirements.txt        # Python dependencies
├── COMPLETE_PROJECT_DETAILS.md # Technical breakdown of every file
└── README.md               # You are here
```

---

## 🚀 Getting Started

### 1. Prerequisites
*   **Python 3.11+**
*   **Ollama** (Download from [ollama.ai](https://ollama.ai))
*   **Git**

### 2. Setup & Installation
```bash
# Clone the repository
git clone https://github.com/your-repo/greenops-refactor.git
cd greenops-refactor/files/Mini_project

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize the AI & Model
```bash
# Pull the AI model for refactoring
ollama pull qwen2.5-coder:1.5b  # Or 7b for better results

# Train the energy predictor (Required for first run)
python training_model1.py
```

### 4. Run the Application
```bash
python app.py
```
Visit **`http://localhost:5000`** in your browser.

---

## 🐳 Docker Deployment (Recommended)

Run the entire stack (including the AI engine) with a single command:

```bash
# Build the model locally first
python training_model1.py

# Launch services
docker-compose up --build -d

# Pull the model inside the container
docker exec -it greenops-ollama ollama pull qwen2.5-coder:1.5b
```

---

## 🔬 Core Methodology

### The Green Score Formula
The project uses a weighted index (0–100) to evaluate code sustainability:
1.  **Energy (40 pts)**: Log-linear mapping of predicted kWh vs. a "perfect" reference.
2.  **Structure (30 pts)**: Penalizes nesting/recursion; rewards vectorization (NumPy).
3.  **Carbon (20 pts)**: Rewards running on cleaner grids (low gCO₂/kWh).
4.  **Quality (10 pts)**: Evaluates error handling and I/O efficiency.

### Amazon AWS Graviton Optimization
The project is optimized for **ARM64 (AWS Graviton)** architectures. 
- **Detection**: Automatically detects if running on ARM/Graviton.
- **Efficiency**: Applies a **40% energy reduction bonus** in calculations when deployed on Graviton, reflecting real-world performance-per-watt gains.

### Structural Safety Floor
To prevent ML model "hallucinations" (where optimized code might be predicted to use more energy due to noise), the system implements a **Physics-based Safety Floor**:
- If structural complexity (loops/nesting) decreases but the ML model predicts higher energy, the system applies a deterministic reduction based on the structural delta.

---

## 🛠 Tech Stack
- **Backend**: Flask (Python)
- **ML**: Scikit-learn, XGBoost, Pandas
- **Static Analysis**: LibCST, AST
- **AI**: Ollama (qwen2.5-coder)
- **APIs**: Electricity Maps
- **Infrastructure**: Docker, AWS Graviton (Optimized)

---

## 👨‍🔬 Authors & License
Project - Green Software Engineering.
Distributed under the MIT License.
