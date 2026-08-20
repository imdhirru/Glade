import React, { useState } from 'react';
import './WorkflowDisplay.css';
import StageView from './StageView';
import NextBestActionCard from './NextBestActionCard';

export default function WorkflowDisplay({ workflow, onBack }) {
  const [expandedStage, setExpandedStage] = useState(0);

  if (!workflow) {
    return <div>Loading...</div>;
  }

  const stages = workflow.stages || [];
  const nextBestAction = workflow.next_best_action;

  return (
    <div className="workflow-display">
      <div className="workflow-header">
        <button className="back-button" onClick={onBack}>
          ← Back
        </button>

        <div className="workflow-info">
          <h2 className="workflow-goal">{workflow.goal}</h2>
          <div className="workflow-meta">
            <span className={`complexity-badge complexity-${workflow.goal_analysis?.complexity || 'medium'}`}>
              {workflow.goal_analysis?.complexity?.toUpperCase()}
            </span>
            <span className="stage-count">
              {stages.length} Stages • {workflow.micro_wins?.length || 0} Micro-Wins
            </span>
          </div>
        </div>
      </div>

      <div className="workflow-content">
        <div className="stages-container">
          {stages.map((stage, index) => (
            <React.Fragment key={stage.stage_id}>
              <StageView
                stage={stage}
                stageNumber={index + 1}
                isExpanded={expandedStage === index}
                onToggle={() => setExpandedStage(expandedStage === index ? -1 : index)}
                microWins={workflow.micro_wins?.filter(mw =>
                  stage.micro_wins?.includes(mw.id)
                ) || []}
              />

              {index < stages.length - 1 && (
                <div className="stage-divider">
                  <span className="divider-icon">↓</span>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>

        <aside className="workflow-sidebar">
          {nextBestAction && (
            <NextBestActionCard action={nextBestAction} workflow={workflow} />
          )}

          <div className="workflow-summary">
            <h3>Summary</h3>
            <p className="summary-text">
              {workflow.goal_analysis?.interpretation || workflow.goal_analysis?.interpreted_goal}
            </p>

            <div className="success-metrics">
              <h4>Success Metrics</h4>
              <ul className="metrics-list">
                {workflow.success_metrics?.slice(0, 3).map((metric, index) => (
                  <li key={index}>
                    <span className="metric-name">{metric.metric}</span>
                    <span className="metric-target">{metric.target}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="workflow-actions">
            <button className="action-button primary-button">
              Start Workflow
            </button>
            <button className="action-button secondary-button">
              Save for Later
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
