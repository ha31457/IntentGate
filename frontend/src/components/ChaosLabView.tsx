"use client";

import React, { useState, useEffect } from "react";
import { fetchChaosScenarios, injectChaos, resetChaos, ChaosScenario } from "../lib/api";
import { Zap, AlertOctagon, RefreshCw, CheckCircle2, ShieldAlert } from "lucide-react";

export const ChaosLabView: React.FC = () => {
  const [scenarios, setScenarios] = useState<ChaosScenario[]>([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const loadScenarios = async () => {
    setLoading(true);
    try {
      const list = await fetchChaosScenarios();
      setScenarios(list);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScenarios();
  }, []);

  const handleToggle = async (scenarioId: string, currentActive: boolean) => {
    try {
      await injectChaos(scenarioId, !currentActive);
      setMsg(`Scenario '${scenarioId}' ${!currentActive ? 'ACTIVATED' : 'DEACTIVATED'}`);
      await loadScenarios();
    } catch (e: any) {
      setMsg("Injection failed: " + e.message);
    }
  };

  const handleReset = async () => {
    try {
      await resetChaos();
      setMsg("All failure scenarios and circuit breakers reset!");
      await loadScenarios();
    } catch (e: any) {
      setMsg("Reset failed: " + e.message);
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Zap className="w-7 h-7 text-amber-400" />
            Chaos & Reliability Failure Lab
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time failure injection suite to demonstrate IntentGate's deterministic guardrails during pitch demo.
          </p>
        </div>
        <button
          onClick={handleReset}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded-xl text-xs flex items-center gap-2 border border-slate-700 transition"
        >
          <RefreshCw className="w-4 h-4 text-amber-400" />
          Reset All Failure Injections
        </button>
      </div>

      {msg && (
        <div className="bg-amber-950/60 border border-amber-800/80 text-amber-200 px-4 py-3 rounded-xl text-xs font-mono">
          {msg}
        </div>
      )}

      {/* Scenario Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {scenarios.map((sc) => (
          <div
            key={sc.id}
            className={`rounded-2xl p-5 border transition-all flex flex-col justify-between ${
              sc.active
                ? "bg-amber-950/20 border-amber-500/50 glow-amber"
                : "bg-[#0f172a] border-slate-800/80 hover:border-slate-700"
            }`}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-white flex items-center gap-2">
                  <ShieldAlert className={`w-4 h-4 ${sc.active ? 'text-amber-400' : 'text-slate-500'}`} />
                  {sc.id}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                    sc.active ? "bg-amber-950 text-amber-400 border border-amber-800" : "bg-slate-900 text-slate-500"
                  }`}
                >
                  {sc.active ? "ACTIVE INJECTION" : "INACTIVE"}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-slate-200">{sc.name}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{sc.description}</p>
            </div>

            <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between">
              <span className="text-[11px] text-slate-500 font-mono">Simulate failure</span>
              <button
                onClick={() => handleToggle(sc.id, sc.active)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  sc.active
                    ? "bg-amber-500 hover:bg-amber-600 text-black shadow-md shadow-amber-500/20"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                }`}
              >
                {sc.active ? "Deactivate" : "Inject Failure"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
