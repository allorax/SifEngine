import React from 'react';
import {
  Zap,
  FileText,
  BrainCircuit,
  TrendingUp,
  ShieldCheck,
  Database,
  Target
} from 'lucide-react';

export default function AboutWindow() {
  return (
    <div className="about-page">
      <div className="about-hero">
        <div className="about-hero-icon">
          <ShieldCheck />
        </div>

        <div>
          <div className="about-eyebrow">
            ABOUT SIFENGINE
          </div>

          <h1>
            Severe Injury & Fatality Analytics Engine
          </h1>

          <p>
            SIFEngine is an AI-powered workplace safety analytics
            system designed to identify serious injury and fatality
            precursors hidden inside unsafe-act, unsafe-condition,
            and near-miss reports.
          </p>
        </div>
      </div>

      <div className="about-section">
        <div className="about-section-header">
          <div className="about-section-title">
            <Zap />
            <h2>How SIFEngine Smart Automation Works</h2>
          </div>

          <span className="about-badge">
            AUTOMATED AI/ML PIPELINE
          </span>
        </div>

        <div className="about-pipeline">
          <div className="about-step">
            <div className="about-step-icon blue">
              <FileText />
            </div>

            <div className="about-step-label blue-text">
              STEP 1: AUTOMATED NLP EXTRACTION
            </div>

            <h3>
              Unstructured Narrative Processing
            </h3>

            <p>
              Automatically parses raw incident descriptions,
              extracts precursor hazards such as equipment,
              height, chemical exposure, severity metrics, and
              near-miss intensity with zero human entry.
            </p>
          </div>

          <div className="about-step">
            <div className="about-step-icon green">
              <BrainCircuit />
            </div>

            <div className="about-step-label green-text">
              STEP 2: UNSUPERVISED VECTOR CLUSTERING
            </div>

            <h3>
              Hidden Pattern Discovery
            </h3>

            <p>
              Converts text into 384D semantic vectors and uses
              unsupervised density clustering to discover new
              danger patterns and sub-hazards automatically.
            </p>
          </div>

          <div className="about-step">
            <div className="about-step-icon purple">
              <TrendingUp />
            </div>

            <div className="about-step-label purple-text">
              STEP 3: AUTOMATED THREAT FORECASTING
            </div>

            <h3>
              Predictive Incident Prevention
            </h3>

            <p>
              Calculates objective five-factor threat scores and
              predicts upcoming incident-rate trends, automatically
              flagging rapidly growing hazards.
            </p>
          </div>
        </div>
      </div>

      <div className="about-info-grid">
        <div className="about-info-card">
          <Database />
          <div>
            <h3>Data-Driven Safety</h3>
            <p>
              Turns large volumes of workplace incident narratives
              into structured safety intelligence.
            </p>
          </div>
        </div>

        <div className="about-info-card">
          <Target />
          <div>
            <h3>Risk Prioritization</h3>
            <p>
              Helps safety teams focus attention on hazards with
              the greatest potential for serious outcomes.
            </p>
          </div>
        </div>

        <div className="about-info-card">
          <ShieldCheck />
          <div>
            <h3>Preventive Intelligence</h3>
            <p>
              Moves safety analysis beyond reporting past incidents
              toward identifying emerging threats before they escalate.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}