import React, { useState } from 'react';
import './HeroPage.css';
import AnalysisAnimation from './AnalysisAnimation';
import WorkflowDisplay from './WorkflowDisplay';

const EXAMPLE_SUGGESTIONS = [
  "Increase my online store sales",
  "Launch my portfolio website",
  "Learn React in 30 days",
  "Prepare for my next exam",
  "Start a small online business"
];

export default function HeroPage() {
  const [goal, setGoal] = useState("");
  const [loading, setLoading] = useState(false);
  const [workflow, setWorkflow] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async (goalText = goal) => {
    if (!goalText.trim()) {
      setError("Please enter a goal");
      return;
    }

    if (goalText.length < 10) {
      setError("Goal should be at least 10 characters");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/workflow/analyze-goal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal: goalText })
      });

      if (!response.ok) {
        throw new Error("Failed to analyze goal");
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Failed to create workflow");
      }

      setWorkflow(data.workflow);
      setGoal("");
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setGoal(suggestion);
  };

  const handleSuggestionSubmit = (suggestion) => {
    handleAnalyze(suggestion);
  };

  // Show workflow if available
  if (workflow) {
    return <WorkflowDisplay workflow={workflow} onBack={() => setWorkflow(null)} />;
  }

  return (
    <div className="hero-page">
      <div className="hero-content">
        <div className="hero-header">
          <h1 className="hero-title">
            Turn Intent Into Action
          </h1>
          <p className="hero-subtitle">
            Glade understands what you're trying to achieve and breaks complexity
            into achievable steps.
          </p>
        </div>

        <div className="goal-input-section">
          <div className="input-wrapper">
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
              placeholder="What do you want to accomplish?"
              className="goal-input"
              disabled={loading}
            />

            <button
              onClick={() => handleAnalyze()}
              disabled={loading || !goal.trim()}
              className="submit-button"
            >
              {loading ? "Analyzing..." : "Break It Down →"}
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}
        </div>

        {loading && <AnalysisAnimation />}

        {!loading && !workflow && (
          <div className="suggestions-section">
            <p className="suggestions-label">Try:</p>
            <div className="suggestions-grid">
              {EXAMPLE_SUGGESTIONS.map((suggestion, index) => (
                <div
                  key={index}
                  className="suggestion-chip"
                  onClick={() => handleSuggestionClick(suggestion)}
                  onDoubleClick={() => handleSuggestionSubmit(suggestion)}
                >
                  <span className="suggestion-icon">✨</span>
                  <span className="suggestion-text">{suggestion}</span>
                </div>
              ))}
            </div>
            <p className="suggestions-hint">Click to fill, double-click to analyze</p>
          </div>
        )}
      </div>

      <div className="hero-footer">
        <p className="tagline">
          From overwhelming goals to executable AI workflows.
        </p>
      </div>
    </div>
  );
}
