# 🔋 Battery Electrolyte AI Agent

A multi-agent AI system for battery electrolyte design, powered by GPT-4.1 and RAG (Retrieval-Augmented Generation).

![Demo](https://img.shields.io/badge/Demo-Vercel-black)
![License](https://img.shields.io/badge/License-MIT-blue)

## 🌟 Features

- **Multi-Agent Architecture**: Coordinated agents for literature search, property analysis, experiment planning, and performance prediction
- **Chemistry-Agnostic**: Supports Li-ion, Zn, Na-ion, Mg, and solid-state battery chemistries
- **RAG-Powered Literature Search**: Upload your own research papers (PDF, DOCX, TXT) for context-aware recommendations
- **User-Specified Materials**: Input custom electrolyte materials for tailored experiment plans
- **Performance Prediction**: LLM-based predictions for capacity retention, cycle life, and ionic conductivity
- **Beautiful UI**: Modern React frontend with dark theme and smooth animations

## 🚀 Live Demo

The frontend demo is available at: [Vercel Deployment](https://battery-ai-agent-psi.vercel.app/)

> ⚠️ **Note**: The demo frontend is for UI demonstration only. The backend API requires local deployment.

## 📦 Installation

### Prerequisites

- Python 3.12+
- Node.js 18+
- OpenAI API Key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Run the server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm start
```

The frontend will be available at `http://localhost:3000`

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATOR AGENT                                  │
│                         (Query Classification & Routing)                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│   │ Literature  │  │  Property   │  │ Experiment  │  │ Performance │          │
│   │  RAG Agent  │  │Compatibility│  │  Planning   │  │ Prediction  │          │
│   │             │  │   Agent     │  │   Agent     │  │   Agent     │          │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
│         │                │                │                │                    │
│         ▼                ▼                ▼                ▼                    │
│   ┌─────────────────────────────────────────────────────────────────┐          │
│   │                         LLM Service (GPT-4.1)                    │          │
│   └─────────────────────────────────────────────────────────────────┘          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
battery_agent_demo/
├── backend/
│   ├── agents/
│   │   ├── orchestrator_agent.py    # Main coordinator
│   │   ├── literature_rag_agent.py  # RAG search
│   │   ├── property_compatibility_agent.py
│   │   ├── experiment_planning_agent.py
│   │   └── performance_prediction_agent.py
│   ├── services/
│   │   ├── llm_service.py           # OpenAI integration
│   │   └── document_service.py      # Document processing
│   ├── main.py                      # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── styles/
│   │   └── App.js
│   ├── package.json
│   └── vercel.json
└── README.md
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/query` | POST | Process electrolyte design query |
| `/api/upload` | POST | Upload document (PDF, DOCX, TXT) |
| `/api/index` | POST | Index uploaded documents |
| `/api/documents` | GET | Get document status |
| `/api/health` | GET | Health check |

## 🧪 Example Queries

- "Design a high-voltage electrolyte for NMC cathode with silicon anode"
- "What additives improve cycle life for fast-charging applications?"
- "Design electrolyte for reversible zinc metal chemistry"
- "Sodium-ion battery electrolyte with good low-temperature performance"

## 🛠️ Technologies

- **Backend**: FastAPI, LangChain, ChromaDB, OpenAI
- **Frontend**: React, Framer Motion
- **Embeddings**: OpenAI text-embedding-3-large
- **LLM**: GPT-4.1

## 📄 License

MIT License - feel free to use and modify for your research!

## 👤 Author

Kevin Wang - [GitHub](https://github.com/KevinWang676)

## 🙏 Acknowledgments

- OpenAI for GPT-4.1 and embedding models
- LangChain for RAG infrastructure
- The battery research community for domain knowledge
