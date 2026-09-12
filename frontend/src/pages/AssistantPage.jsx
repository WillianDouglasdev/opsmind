import { useState } from "react";
import {
  ArrowRight,
  DatabaseZap,
  FileText,
  LoaderCircle,
  Send,
  Sparkles,
} from "lucide-react";
import { askAssistant, getExecutiveSummary } from "../services/api.js";
import { formatAlertMetric } from "../utils/alerts.js";

const suggestedQuestions = [
  "Por que os atrasos aumentaram?",
  "Qual filial está com pior desempenho?",
  "Temos risco de estoque?",
  "Quais clientes estratégicos precisam de atenção?",
  "O que aconteceu com os chamados?",
  "Resuma a operação.",
];

const intentLabels = {
  DELIVERY_DELAYS: "Entregas e atrasos",
  CUSTOMER_RISK: "Clientes estratégicos",
  INVENTORY_RISK: "Risco de estoque",
  BRANCH_PERFORMANCE: "Desempenho de filial",
  TICKET_ANALYSIS: "Análise de chamados",
  EXECUTIVE_SUMMARY: "Resumo executivo",
  UNKNOWN: "Fora do escopo atual",
};

const providerLabels = {
  mock: "Modo local",
  gemini: "Gemini",
  fallback: "Fallback local",
};

function AssistantPage() {
  // A página mantém somente a interação atual; a demo não persiste histórico de conversa.
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  async function submitQuestion(selectedQuestion) {
    const normalizedQuestion = selectedQuestion.trim();
    if (!normalizedQuestion || loading) return;

    setQuestion(normalizedQuestion);
    setSubmittedQuestion(normalizedQuestion);
    setLoading(true);
    setError(false);
    try {
      setResult(await askAssistant(normalizedQuestion));
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  async function generateExecutiveSummary() {
    if (loading) return;
    setSubmittedQuestion("Resumo executivo da operação");
    setLoading(true);
    setError(false);
    try {
      setResult(await getExecutiveSummary());
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    submitQuestion(question);
  }

  return (
    <div className="assistant-page">
      <section className="panel assistant-hero">
        <div className="assistant-hero-copy">
          <span className="assistant-symbol"><Sparkles size={24} /></span>
          <div>
            <span className="assistant-eyebrow">Inteligência operacional assistida</span>
            <h2>Consulte a operação com linguagem natural</h2>
            <p>
              O OpsMind2 AI explica analytics e investigações já calculados pelo backend,
              sempre acompanhado das evidências utilizadas.
            </p>
          </div>
        </div>
        <button
          className="executive-button"
          type="button"
          disabled={loading}
          onClick={generateExecutiveSummary}
        >
          <FileText size={16} /> Gerar resumo executivo
        </button>
      </section>

      <section className="assistant-suggestions" aria-labelledby="suggestions-title">
        <div className="assistant-section-label">
          <span id="suggestions-title">Perguntas sugeridas</span>
          <small>Selecione um tema para começar</small>
        </div>
        <div className="suggestion-list">
          {suggestedQuestions.map((suggestion) => (
            <button
              type="button"
              key={suggestion}
              disabled={loading}
              onClick={() => submitQuestion(suggestion)}
            >
              {suggestion}<ArrowRight size={13} />
            </button>
          ))}
        </div>
      </section>

      <section className="panel assistant-query-card">
        <form onSubmit={handleSubmit}>
          <label htmlFor="assistant-question">Pergunte sobre sua operação</label>
          <div className="assistant-input-row">
            <input
              id="assistant-question"
              type="text"
              value={question}
              maxLength={500}
              disabled={loading}
              placeholder="Pergunte sobre sua operação..."
              onChange={(event) => setQuestion(event.target.value)}
            />
            <button type="submit" disabled={loading || !question.trim()}>
              {loading
                ? <><LoaderCircle className="spin" size={16} /> Analisando dados...</>
                : <><Send size={16} /> Analisar</>}
            </button>
          </div>
          <small>{question.length}/500 caracteres</small>
        </form>
      </section>

      {error && (
        <div className="panel assistant-error" role="alert">
          <Sparkles size={20} />
          <div><strong>Não foi possível concluir a análise.</strong><span>Tente novamente em instantes.</span></div>
        </div>
      )}

      {result && !error && (
        <section className="assistant-result" aria-live="polite">
          <article className="panel assistant-answer-card">
            <div className="assistant-answer-heading">
              <span className="assistant-symbol small"><Sparkles size={18} /></span>
              <div>
                <span>OpsMind2 AI</span>
                <small>{providerLabels[result.provider]}</small>
              </div>
              <span className="intent-badge">{intentLabels[result.intent]}</span>
            </div>
            <p className="assistant-question-copy">“{submittedQuestion}”</p>
            <p className="assistant-answer-copy">{result.answer}</p>
          </article>

          {result.evidence.length > 0 && (
            <section className="assistant-evidence" aria-labelledby="assistant-evidence-title">
              <div className="assistant-section-label evidence-label">
                <span id="assistant-evidence-title"><DatabaseZap size={14} /> Evidências utilizadas</span>
                <small>Valores calculados pelo backend</small>
              </div>
              <div className="assistant-evidence-grid">
                {result.evidence.map((evidence) => (
                  <article className="panel assistant-evidence-card" key={evidence.label}>
                    <strong>{formatAlertMetric(evidence)}</strong>
                    <span>{evidence.label}</span>
                  </article>
                ))}
              </div>
            </section>
          )}
        </section>
      )}

      <p className="assistant-disclaimer">
        As análises são geradas a partir dos dados disponíveis na demonstração.
      </p>
    </div>
  );
}

export default AssistantPage;
