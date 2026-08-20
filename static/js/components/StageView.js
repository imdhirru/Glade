import React from 'react';
import './StageView.css';
import MicroWinCard from './MicroWinCard';

export default function StageView({ stage, stageNumber, isExpanded, onToggle, microWins }) {
  if (!stage) {
    return null;
  }

  const stageStatus = stage.status || 'pending';
  const statusIcon = {
    completed: '✓',
    in_progress: '⏳',
    pending: '○'
  }[stageStatus] || '○';

  return (
    <div className={`stage-container stage-${stageStatus}`}>
      <div className="stage-card" onClick={onToggle}>
        <div className="stage-header">
          <div className="stage-info">
            <span className="status-icon">{statusIcon}</span>
            <div className="stage-text">
              <h3 className="stage-name">
                Stage {stageNumber}: {stage.name}
              </h3>
              <p className="stage-description">{stage.description}</p>
            </div>
          </div>

          <div className="stage-controls">
            <span className="micro-win-count">
              {microWins.length} steps
            </span>
            <button
              className={`expand-button ${isExpanded ? 'expanded' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                onToggle();
              }}
            >
              {isExpanded ? '−' : '+'}
            </button>
          </div>
        </div>

        {isExpanded && (
          <div className="stage-content">
            <div className="micro-wins-list">
              {microWins.map((microWin) => (
                <MicroWinCard key={microWin.id} microWin={microWin} />
              ))}
            </div>

            {microWins.length === 0 && (
              <p className="no-wins-message">
                No micro-wins defined for this stage yet.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
