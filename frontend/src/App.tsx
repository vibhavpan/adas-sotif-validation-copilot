import React, { useState } from 'react';
import { Upload, Play, AlertTriangle, CheckCircle, FileCode, Activity } from 'lucide-react';
import ReactDiffViewer from 'react-diff-viewer-continued';
import { validateScenario } from './services/api';
import { ValidationResponse } from './types';
import ReactMarkdown from 'react-markdown';
import './index.css'

export default function App() {
  const [scenarioFile, setScenarioFile] = useState<File | null>(null);
  const [telemetryFile, setTelemetryFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ValidationResponse | null>(null);

  const handleRunValidation = async () => {
    if (!scenarioFile || !telemetryFile){ 
      alert("Please select both an OpenScenario (.xosc) file and a Telemetry (.csv)")
      return;
    }
    setLoading(true);
    try {
      const data = await validateScenario(scenarioFile, telemetryFile);
      setResult(data);
    } catch (err) {
      console.error('Validation Error:',err);
      alert('Validation failed. Ensure FastAPI server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">
      {/* Top Navigation / Header */}
      <header className="mb-8 border-b border-slate-800 pb-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-indigo-400">
            <Activity className="w-6 h-6" /> ADAS Validation Copilot
          </h1>
          <p className="text-slate-400 text-sm">Closed-loop SOTIF & OpenSCENARIO Triage Engine</p>
        </div>
        <span className="bg-emerald-500/10 text-emerald-400 text-xs px-3 py-1 rounded-full border border-emerald-500/20">
          Gemini 2.5 Flash Connected
        </span>
      </header>

      {/* Main Dashboard Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Panel: File Selection & Trigger */}
        <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 flex flex-col gap-6 h-fit">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Upload className="w-5 h-5 text-indigo-400" /> Artifact Ingestion
          </h2>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">OpenSCENARIO (.xosc)</label>
            <input
              type="file"
              accept=".xosc,.xml"
              onChange={(e) => setScenarioFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Telemetry Log (.csv)</label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setTelemetryFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
            />
          </div>

          <button
            onClick={handleRunValidation}
            disabled={!scenarioFile || !telemetryFile || loading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 font-semibold rounded-lg flex items-center justify-center gap-2 transition cursor-pointer disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="animate-pulse">Running LangGraph Agent...</span>
            ) : (
              <>
                <Play className="w-4 h-4" /> Start Automated Triage
              </>
            )}
          </button>
        </div>

        {/* Right Panel: Agent Diagnostics, Simulation & XML Diff */}
        <div className="lg:col-span-2 space-y-6">
          {result ? (
            <>
              {/* Diagnosis Box */}
              <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                <h3 className="text-md font-semibold text-amber-400 mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" /> Gemini AI Root Cause Analysis
                </h3>
               
                  {/* Prose classes handle line height, list padding, and heading margins automatically */}
                  <div className="prose prose-invert prose-slate prose-sm max-w-none">
                    <ReactMarkdown>{result.diagnosis}</ReactMarkdown>
                  </div>
              </div>

              {/* Simulation Result Output */}
              <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400" /> esmini Headless Simulation Run
                </h3>
                <div className="bg-slate-950 p-4 rounded-lg font-mono text-xs text-slate-400 overflow-x-auto">
                  <p className="text-emerald-400 mb-1">Exit Code: {result.simulation_result.exit_code}</p>
                  <pre>{result.simulation_result.logs}</pre>
                </div>
              </div>

              {/* Side-by-Side Code Diff Viewer */}
              <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 overflow-hidden">
                <h3 className="text-md font-semibold mb-4 flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-indigo-400" /> Proposed OpenSCENARIO XML Patch
                </h3>
                <div className="rounded-lg overflow-hidden text-xs">
                  <ReactDiffViewer
                    oldValue={result?.original_xml && result.original_xml.trim() !== "" ? result.original_xml : "<!-- Loading or Original XML empty -->"}
                    newValue={result?.patched_xml && result.patched_xml.trim() !== "" ? result.patched_xml : "<!-- Loading or Patched XML empty -->"}
                    splitView={true}
                    useDarkTheme={true}
                    leftTitle="Original Scenario"
                    rightTitle="Patched Fix"
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="h-64 border-2 border-dashed border-slate-800 rounded-xl flex items-center justify-center text-slate-600">
              Upload scenario and telemetry artifacts to trigger the validation agent.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}