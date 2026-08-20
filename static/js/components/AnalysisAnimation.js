import React, { useState, useEffect } from 'react';
import './AnalysisAnimation.css';

const ANALYSIS_STEPS = [
  "Understanding intent...",
  "Mapping dependencies...",
  "Building workflow...",
  "Creating Micro-Wins..."
];

export default function AnalysisAnimation() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep(prev => (prev + 1) % ANALYSIS_STEPS.length);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="analysis-animation">
      <div className="animation-container">
        <div className="animated-dots">
          <span className="dot"></span>
          <span className="dot"></span>
          <span className="dot"></span>
        </div>
        <p className="analysis-text">{ANALYSIS_STEPS[currentStep]}</p>
      </div>

      <div className="progress-steps">
        {ANALYSIS_STEPS.map((step, index) => (
          <div
            key={index}
            className={`step-indicator ${index <= currentStep ? 'active' : ''}`}
          >
            <span className="step-number">{index + 1}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
