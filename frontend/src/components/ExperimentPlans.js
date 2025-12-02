import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './ExperimentPlans.css';

function ExperimentPlans({ plans }) {
  const [expandedPlan, setExpandedPlan] = useState(null);

  if (!plans || plans.length === 0) return null;

  const togglePlan = (planId) => {
    setExpandedPlan(expandedPlan === planId ? null : planId);
  };

  const getPriorityColor = (score) => {
    if (score >= 0.9) return '#10b981';
    if (score >= 0.85) return '#22d3ee';
    return '#f59e0b';
  };

  return (
    <div className="experiment-plans">
      <div className="plans-header">
        <h2>Experiment Plans</h2>
        <span className="plans-count">{plans.length} plans generated</span>
      </div>

      <div className="plans-grid">
        {plans.map((plan, index) => (
          <motion.div
            key={plan.plan_id}
            className={`plan-card ${expandedPlan === plan.plan_id ? 'expanded' : ''}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div 
              className="plan-header"
              onClick={() => togglePlan(plan.plan_id)}
            >
              <div className="plan-rank">#{index + 1}</div>
              <div className="plan-title-section">
                <h3 className="plan-title">{plan.title}</h3>
                <div className="plan-meta">
                  <span className="plan-cost">{plan.estimated_cost}</span>
                  <span className="plan-time">{plan.estimated_time}</span>
                </div>
              </div>
              <div 
                className="plan-priority"
                style={{ '--priority-color': getPriorityColor(plan.priority_score) }}
              >
                <span className="priority-value">{(plan.priority_score * 100).toFixed(0)}</span>
                <span className="priority-label">Priority</span>
              </div>
              <div className="expand-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M6 9L12 15L18 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>

            <AnimatePresence>
              {expandedPlan === plan.plan_id && (
                <motion.div
                  className="plan-details"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="detail-section">
                    <h4>Formulation</h4>
                    <div className="formulation-table">
                      {plan.formulation.map((component, i) => (
                        <div key={i} className="formulation-row">
                          <span className="component-role">{component.role}</span>
                          <span className="component-name">
                            {component.name}
                            {component.abbreviation && (
                              <span className="component-abbr">({component.abbreviation})</span>
                            )}
                          </span>
                          <span className="component-conc">
                            {component.concentration} {component.unit}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="detail-section">
                    <h4>Rationale</h4>
                    <p className="rationale-text">{plan.rationale}</p>
                    {plan.llm_rationale && (
                      <div className="llm-rationale">
                        <div className="llm-badge">
                          <span>🤖 GPT-4.1 Analysis</span>
                        </div>
                        <p>{plan.llm_rationale}</p>
                      </div>
                    )}
                  </div>

                  <div className="detail-section">
                    <h4>Predicted Performance</h4>
                    {plan.prediction_confidence && (
                      <div className="prediction-confidence">
                        <span className="confidence-label">Model Confidence:</span>
                        <span className="confidence-value">{(plan.prediction_confidence * 100).toFixed(0)}%</span>
                      </div>
                    )}
                    <div className="performance-grid">
                      <div className="perf-item">
                        <span className="perf-label">Capacity Retention (100 cycles)</span>
                        <span className="perf-value">
                          {plan.predicted_performance?.capacity_retention_percent 
                            ? `${plan.predicted_performance.capacity_retention_percent}%`
                            : plan.predicted_performance?.capacity_retention_100cycles || 'N/A'}
                        </span>
                      </div>
                      <div className="perf-item">
                        <span className="perf-label">Cycle Life</span>
                        <span className="perf-value">
                          {plan.predicted_performance?.cycle_stability_cycles 
                            ? `${plan.predicted_performance.cycle_stability_cycles} cycles`
                            : plan.predicted_performance?.cycle_life || 'N/A'}
                        </span>
                      </div>
                      <div className="perf-item">
                        <span className="perf-label">Rate Capability (2C)</span>
                        <span className="perf-value">
                          {plan.predicted_performance?.rate_capability_2C_percent 
                            ? `${plan.predicted_performance.rate_capability_2C_percent}%`
                            : plan.predicted_performance?.rate_capability_2C || 'N/A'}
                        </span>
                      </div>
                      <div className="perf-item">
                        <span className="perf-label">Ionic Conductivity</span>
                        <span className="perf-value">
                          {plan.predicted_performance?.ionic_conductivity_mS_cm 
                            ? `${plan.predicted_performance.ionic_conductivity_mS_cm} mS/cm`
                            : 'N/A'}
                        </span>
                      </div>
                      <div className="perf-item">
                        <span className="perf-label">Temperature Range</span>
                        <span className="perf-value">
                          {plan.predicted_performance?.temperature_range_C 
                            || plan.predicted_performance?.temperature_range 
                            || 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="detail-section">
                    <h4>Experimental Steps</h4>
                    <ol className="steps-list">
                      {plan.experimental_steps.map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ol>
                  </div>

                  <div className="detail-section safety">
                    <h4>⚠️ Safety Considerations</h4>
                    <ul className="safety-list">
                      {plan.safety_considerations.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

export default ExperimentPlans;

