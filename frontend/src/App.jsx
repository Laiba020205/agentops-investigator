
import { useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

const scenarios = [
  { value: "success", label: "Successful execution" },
  { value: "missing_order_id", label: "Missing order ID" },
  { value: "timeout", label: "Tool timeout" },
  { value: "repeated_tool_call", label: "Repeated tool call" },
  { value: "malformed_tool_response", label: "Malformed tool response" },
  { value: "unsupported_answer", label: "Unsupported answer" },
  { value: "conflicting_evidence", label: "Conflicting evidence" },
  { value: "multiple_failures", label: "Multiple failures" },
  { value: "misleading_answer", label: "Misleading answer" },
];

function App() {
  const [scenario, setScenario] = useState("success");
  const [run, setRun] = useState(null);
  const [diagnosis, setDiagnosis] = useState(null);
  const [investigator, setInvestigator] = useState("rule");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function request(path, options = {}) {
    const response = await fetch(`${API}${path}`, options);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.detail || `Request failed with status ${response.status}`
      );
    }

    return data;
  }

  async function runDemo() {
    setLoading(true);
    setError("");
    setRun(null);
    setDiagnosis(null);

    try {
      const data = await request("/runs/demo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ scenario }),
      });

      setRun(data);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot connect to FastAPI. Check that the backend is running on port 8000."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  async function investigate() {
    if (!run?.run_id) return;

    setLoading(true);
    setError("");
    setDiagnosis(null);

    try {
      const endpoint =
        investigator === "gemini"
          ? "llm-investigation"
          : "investigation";

      const data = await request(
        `/runs/${encodeURIComponent(run.run_id)}/${endpoint}`
      );

      setDiagnosis(data.investigation);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot connect to FastAPI. Check that the backend is running."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  const trace = run?.trace || [];

  function formatLabel(value) {
    return String(value || "unknown").replaceAll("_", " ");
  }

  function getEventSummary(event) {
    const output = event.output_data || {};

    if (output.error) return output.error;
    if (output.status) return `Order status: ${output.status}`;
    if (event.input_data?.order_id) {
      return `Order ID: ${event.input_data.order_id}`;
    }

    return "";
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/">
          <span className="brand-mark">A</span>
          <span>
            AgentOps <span className="muted">Investigator</span>
          </span>
        </a>

        <span className="status">
          <span className="status-dot" />
          Local environment
        </span>
      </header>

      <section className="hero">
        <p className="eyebrow">AGENT RELIABILITY WORKSPACE</p>
        <h1>Understand what went wrong.</h1>
        <p className="hero-copy">
          Inspect agent execution traces, identify root causes, and get
          actionable recommendations.
        </p>

        <div className="scenario-control">
          <label className="field-label" htmlFor="scenario">
            Choose an execution scenario
          </label>

          <select
            id="scenario"
            value={scenario}
            onChange={(event) => setScenario(event.target.value)}
            disabled={loading}
          >
            {scenarios.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <button
          className="primary-button"
          onClick={runDemo}
          disabled={loading}
        >
          {loading ? "Working..." : "▶  Run demo agent"}
        </button>
      </section>

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

      <section className="metrics">
        <article className="metric-card">
          <span className="metric-label">Run ID</span>
          <strong className="metric-value small-value">
            {run?.run_id ? `${run.run_id.slice(0, 12)}…` : "—"}
          </strong>
        </article>

        <article className="metric-card">
          <span className="metric-label">Trace events</span>
          <strong className="metric-value">{trace.length}</strong>
        </article>

        <article className="metric-card">
          <span className="metric-label">Execution status</span>
          <strong className="metric-value small-value">
            {run?.status || "Pending"}
          </strong>
        </article>
      </section>

      <section className="workspace">
        <article className="panel trace-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">OBSERVABILITY</p>
              <h2>Execution trace</h2>
            </div>

            <span className="count-pill">{trace.length} events</span>
          </div>

          {trace.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">⌁</div>
              <h3>No execution yet</h3>
              <p>
                Choose a scenario and run the demo agent to populate the
                trace timeline.
              </p>
            </div>
          ) : (
            <div className="timeline">
              {trace.map((event, index) => (
                <div className="timeline-item" key={event.event_id || index}>
                  <div
                    className={`timeline-marker ${
                      event.event_type === "error" ||
                      event.status === "failure"
                        ? "marker-error"
                        : ""
                    }`}
                  >
                    {event.event_type === "error" ? "!" : index + 1}
                  </div>

                  <div className="event-content">
                    <div className="event-title-row">
                      <strong>{formatLabel(event.event_type)}</strong>
                      <span
                        className={`event-status ${
                          event.status === "failure" ? "failure" : ""
                        }`}
                      >
                        {event.status || "recorded"}
                      </span>
                    </div>

                    <p>{event.name || "Agent event"}</p>

                    {getEventSummary(event) && (
                      <p
                        className={
                          event.event_type === "error" ||
                          event.status === "failure"
                            ? "event-error"
                            : "event-detail"
                        }
                      >
                        {getEventSummary(event)}
                      </p>
                    )}

                    <span className="sequence">
                      Sequence {event.sequence}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="panel diagnosis-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">ROOT-CAUSE ANALYSIS</p>
              <h2>Investigation</h2>
            </div>

            <span className="ai-badge">AI + Rules</span>
          </div>

          <label className="field-label" htmlFor="investigator">
            Investigation engine
          </label>

          <select
            id="investigator"
            value={investigator}
            onChange={(event) => {
              setInvestigator(event.target.value);
              setDiagnosis(null);
              setError("");
            }}
            disabled={loading}
          >
            <option value="rule">Rule-based investigator</option>
            <option value="gemini">Gemini investigator</option>
          </select>

          <button
            className="secondary-button"
            onClick={investigate}
            disabled={!run || loading}
          >
            {loading ? "Analyzing..." : "Investigate trace →"}
          </button>

          {!diagnosis ? (
            <div className="empty-state diagnosis-empty">
              <div className="empty-icon">⌕</div>
              <h3>Diagnosis will appear here</h3>
              <p>
                Run an agent, select an investigation engine, and inspect
                the findings.
              </p>
            </div>
          ) : (
            <div className="diagnosis-result">
              <span className="result-label">ROOT CAUSE</span>

              <h3>{formatLabel(diagnosis.root_cause)}</h3>

              <div className="confidence-row">
                <span>Confidence</span>
                <strong>
                  {Math.round((diagnosis.confidence ?? 0) * 100)}%
                </strong>
              </div>

              <div className="confidence-track">
                <div
                  style={{
                    width: `${
                      Math.max(
                        0,
                        Math.min(100, (diagnosis.confidence ?? 0) * 100)
                      )
                    }%`,
                  }}
                />
              </div>

              <h4>Evidence</h4>

              {diagnosis.evidence?.length ? (
                diagnosis.evidence.map((item, index) => (
                  <div
                    className="evidence-card"
                    key={`${item.sequence}-${index}`}
                  >
                    <span>Sequence {item.sequence}</span>
                    <p>
                      {item.explanation ||
                        item.error ||
                        "Supporting trace event"}
                    </p>
                  </div>
                ))
              ) : (
                <p className="muted">No specific evidence was returned.</p>
              )}

              <h4>Recommended action</h4>
              <p className="recommendation">
                {diagnosis.recommendation}
              </p>
            </div>
          )}
        </article>
      </section>

      <footer>
        AgentOps Investigator <span>·</span> Trace. Diagnose. Improve.
      </footer>
    </main>
  );
}

export default App;
