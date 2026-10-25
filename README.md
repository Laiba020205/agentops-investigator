

\# AgentOps Investigator



\*\*An AI agent observability and root-cause analysis platform.\*\*



AgentOps Investigator captures AI agent execution traces, identifies common execution failures, and provides actionable diagnostic recommendations. It combines a deterministic rule-based investigator with a Gemini-powered investigator and presents the results in an interactive React dashboard.



\## Features



\- \*\*Execution tracing:\*\* Capture agent starts, tool calls, tool results, errors, and completion events.

\- \*\*Rule-based investigation:\*\* Diagnose common failures using deterministic diagnostic rules.

\- \*\*LLM-powered investigation:\*\* Use Google Gemini to analyze traces and generate structured diagnoses.

\- \*\*Evidence validation:\*\* Verify that cited event sequence numbers exist in the recorded trace.

\- \*\*Deterministic safeguards:\*\* Correct diagnoses when the trace contains decisive evidence of known failure patterns.

\- \*\*Interactive dashboard:\*\* Run demo scenarios, inspect trace timelines, and view diagnoses and recommendations.

\- \*\*Scenario simulation:\*\* Test successful execution, missing arguments, timeouts, repeated tool calls, malformed responses, unsupported answers, conflicting evidence, and multiple failures.

\- \*\*Investigator benchmarking:\*\* Compare diagnostic accuracy, evidence validity, API call success, and latency.



\## Architecture



```text

&#x20;                React + Vite Dashboard

&#x20;                         |

&#x20;                         | HTTP / JSON

&#x20;                         v

&#x20;                   FastAPI Backend

&#x20;                         |

&#x20;             +-----------+-----------+

&#x20;             |           |           |

&#x20;             v           v           v

&#x20;        Execution     Rule-Based    Gemini

&#x20;          Agent      Investigator Investigator

&#x20;             |

&#x20;             v

&#x20;       Trace Collector

&#x20;             |

&#x20;             v

&#x20;      Recorded Events

&#x20;             |

&#x20;             v

&#x20;      Diagnosis + Evidence

```



\## Technology Stack



| Component | Technology |

|---|---|

| Backend | Python, FastAPI |

| Frontend | React, Vite, JavaScript |

| LLM integration | Google Gemini API |

| Data validation | Pydantic |

| Testing | Pytest |

| Observability | Custom execution trace collector |



\## Project Structure



```text

agentops-investigator/

├── app/

│   ├── agents/

│   │   ├── execution\_agent.py

│   │   ├── investigator.py

│   │   ├── llm\_investigator.py

│   │   └── replay.py

│   ├── tools/

│   │   └── mock\_crm.py

│   ├── tracing/

│   │   ├── collector.py

│   │   └── models.py

│   └── main.py

├── benchmark/

├── tests/

├── frontend/

├── .env.example

├── .gitignore

└── README.md

```



\*The tree above describes the main project components; individual filenames may vary with the current repository.\*



\## Getting Started



\### Prerequisites



\- Python 3.10 or later

\- Node.js and npm

\- A Google Gemini API key for LLM-powered investigation



\### 1. Clone the repository



```bash

git clone <YOUR\_GITHUB\_REPOSITORY\_URL>

cd agentops-investigator

```



\### 2. Set up the Python backend



Create and activate a virtual environment.



\*\*Windows PowerShell:\*\*



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



Install the project's Python dependencies:



```powershell

pip install -r requirements.txt

```



Create a `.env` file in the project root:



```env

GEMINI\_API\_KEY=your\_gemini\_api\_key

GEMINI\_MODEL=gemini-flash-latest

```



Keep your real API key private. Never commit `.env` to version control.



Start the backend:



```powershell

uvicorn app.main:app --reload

```



The API is available at `http://127.0.0.1:8000`.



Interactive API documentation is available at `http://127.0.0.1:8000/docs`.



\### 3. Set up the frontend



Open a second terminal:



```powershell

cd frontend

npm install

npm run dev

```



Open the local URL printed by Vite, usually `http://localhost:5173`.



\### 4. Run the tests



From the project root, with the virtual environment activated:



```powershell

python -m pytest -q

```



\### 5. Run the investigator benchmark



```powershell

python -m benchmark.compare\_investigators

```



The benchmark report is written to `benchmark/compare\_report.json`.



\## API Endpoints



| Method | Endpoint | Purpose |

|---|---|---|

| GET | `/health` | Check API health |

| POST | `/runs/demo` | Run a demo scenario |

| GET | `/runs/{run\_id}` | Retrieve an execution trace |

| GET | `/runs/{run\_id}/investigation` | Run rule-based investigation |

| GET | `/runs/{run\_id}/llm-investigation` | Run Gemini-powered investigation |

| POST | `/runs/{run\_id}/replay` | Replay a run with a supplied order ID |



\### Example: Run a timeout scenario



```http

POST /runs/demo

Content-Type: application/json



{

&#x20; "scenario": "timeout"

}

```



The response contains a run ID, execution status, answer, and trace events.



\## Benchmark Results



Latest recorded benchmark run:



| Metric | Result |

|---|---:|

| Scenarios evaluated | 11 |

| Rule-based accuracy | 100% (11/11) |

| Combined Gemini-system accuracy | 100% (11/11) |

| Gemini API call success | 100% (11/11) |

| Evidence validity | 100% |

| Average rule-based latency | 0.02 ms |

| Average Gemini latency | Approximately 1.56 seconds |



The combined Gemini-system result includes deterministic validation safeguards; it does not represent Gemini's independent accuracy.



\*\*Evaluation limitation:\*\* These results apply to the current 11-scenario benchmark. They do not establish generalization to unseen production traces. Latency may vary with API availability, network conditions, and model behavior.



\## Security and Limitations



\- The demo uses a mock CRM tool and in-memory trace collection.

\- Recorded runs may be lost when the backend process restarts.

\- Gemini-powered investigation requires a valid API key and network access.

\- This project is a prototype and has not been validated for production use.

\- Never commit API keys, credentials, or other secrets.



\## Future Improvements



\- Persistent trace storage

\- More diverse and unseen benchmark scenarios

\- Production-grade authentication and access control

\- Configurable tracing and monitoring integrations

\- Deployment and operational monitoring



\## License



Choose and add a license before distributing or accepting contributions.



