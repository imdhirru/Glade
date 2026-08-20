import React, { useState } from 'react';
import './MicroWinCard.css';

export default function MicroWinCard({ microWin }) {
  const [expanded, setExpanded] = useState(false);

  if (!microWin) {
    return null;
  }

  const status = microWin.status || 'pending';
  const statusIcon = {
    completed: '✓',
    in_progress: '⏳',
    pending: '○'
  }[status] || '○';

  const difficultyColor = {
    easy: 'easy',
    medium: 'medium',
    hard: 'hard'
  }[microWin.difficulty] || 'medium';

  return (
    <div className={`micro-win-card micro-win-${status}`}>
      <div className="micro-win-header">
        <div className="win-status">
          <span className={`status-icon status-${status}`}>{statusIcon}</span>
        </div>

        <div className="win-main-info">
          <h4 className="win-title">{microWin.title}</h4>
          <div className="win-badges">
            <span className="time-badge">
              ⏱ {microWin.estimated_time} min
            </span>
            <span className={`difficulty-badge difficulty-${difficultyColor}`}>
              {microWin.difficulty}
            </span>
          </div>
        </div>

        <button
          className={`expand-button ${expanded ? 'expanded' : ''}`}
          onClick={() => setExpanded(!expanded)}
          aria-label="Toggle details"
        >
          {expanded ? '−' : '+'}
        </button>
      </div>

      {expanded && (
        <div className="micro-win-details">
          <p className="description">{microWin.description}</p>

          {microWin.ai_guidance && (
            <div className="ai-guidance-box">
              <div className="guidance-header">
                <span className="guidance-icon">💡</span>
                <strong>AI Guidance</strong>
              </div>
              <p className="guidance-text">{microWin.ai_guidance}</p>
            </div>
          )}

          {microWin.dependencies && microWin.dependencies.length > 0 && (
            <div className="dependencies-box">
              <strong>Requires first:</strong>
              <ul className="dependencies-list">
                {microWin.dependencies.map((dep, idx) => (
                  <li key={idx}>{dep}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="actions-box">
            {status === 'pending' && (
              <button className="start-button">
                Start Micro-Win
              </button>
            )}
            {status === 'in_progress' && (
              <>
                <button className="continue-button">
                  Continue
                </button>
                <button className="complete-button">
                  Mark Complete
                </button>
              </>
            )}
            {status === 'completed' && (
              <div className="completed-message">
                ✓ Completed
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
