import React from 'react';
import './NextBestActionCard.css';

export default function NextBestActionCard({ action, workflow }) {
  if (!action) {
    return null;
  }

  return (
    <div className="next-best-action-card">
      <div className="card-header">
        <span className="lightning-icon">⚡</span>
        <h3>Next Best Action</h3>
      </div>

      <div className="action-content">
        <h4 className="action-title">{action.title}</h4>

        {action.reason && (
          <div className="action-reason">
            <p className="reason-label">Why?</p>
            <p className="reason-text">{action.reason}</p>
          </div>
        )}

        {action.estimated_time && (
          <div className="action-meta">
            <span className="meta-item">
              ⏱ {action.estimated_time} minutes
            </span>
          </div>
        )}
      </div>

      <button className="cta-button">
        {action.action_button_text || 'Start Micro-Win'} →
      </button>

      <div className="action-description">
        <p className="description-text">
          This is the most impactful step you can take right now. Completing it
          will unlock the next stage of your workflow.
        </p>
      </div>
    </div>
  );
}
