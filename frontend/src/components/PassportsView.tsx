"use client";

import React from "react";
import { Layers, ShieldCheck, Activity, Award, CheckCircle2, Lock, Flame } from "lucide-react";

export const PassportsView: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Layers className="w-7 h-7 text-indigo-400" />
            Agent Capability Passports & Reputation
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Every transaction is bound by the agent's permission passport and real-time operational trust score.
          </p>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Agent Alpha Passport Card */}
        <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold">
                α
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Shopping Agent Alpha</h3>
                <p className="text-xs text-slate-400">ID: agent_shopping_alpha | Status: ACTIVE</p>
              </div>
            </div>
            <span className="text-xs font-semibold px-3 py-1 rounded-full bg-blue-950 text-blue-400 border border-blue-800">
              Level 3 — Controlled Buyer
            </span>
          </div>

          {/* Limits */}
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="bg-[#0b1426] p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block mb-1">Single Transaction Cap:</span>
              <span className="text-sm font-bold text-emerald-400 font-mono">₹70,000.00</span>
            </div>
            <div className="bg-[#0b1426] p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block mb-1">Daily Spend Limit:</span>
              <span className="text-sm font-bold text-cyan-400 font-mono">₹100,000.00</span>
            </div>
          </div>

          {/* Capabilities */}
          <div className="space-y-2 text-xs">
            <h4 className="font-semibold text-slate-300">Enforced Capability Matrix:</h4>
            <div className="grid grid-cols-2 gap-2 text-slate-300">
              <div className="flex items-center gap-2 bg-[#0b1426] p-2 rounded-lg border border-slate-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Search & Recommend
              </div>
              <div className="flex items-center gap-2 bg-[#0b1426] p-2 rounded-lg border border-slate-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Single Tx ≤ ₹70,000
              </div>
              <div className="flex items-center gap-2 bg-[#0b1426] p-2 rounded-lg border border-slate-800 opacity-60">
                <Lock className="w-4 h-4 text-red-400" />
                Recurring Subscriptions (DISABLED)
              </div>
              <div className="flex items-center gap-2 bg-[#0b1426] p-2 rounded-lg border border-slate-800 opacity-60">
                <Lock className="w-4 h-4 text-red-400" />
                Category Modification (DISABLED)
              </div>
            </div>
          </div>

          {/* Allowlists */}
          <div className="space-y-2 text-xs">
            <h4 className="font-semibold text-slate-300">Allowed Categories & Merchants:</h4>
            <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
              <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded">laptop</span>
              <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded">programming_laptop</span>
              <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded">accessories</span>
              <span className="bg-blue-950 text-blue-300 px-2 py-0.5 rounded">TechWorld</span>
              <span className="bg-blue-950 text-blue-300 px-2 py-0.5 rounded">DevStore</span>
            </div>
          </div>
        </div>

        {/* Blast Radius Simulator Card */}
        <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-600/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <Flame className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Blast Radius Financial Exposure</h3>
                <p className="text-xs text-slate-400">Financial damage calculation if agent behaves maliciously</p>
              </div>
            </div>
          </div>

          {/* Comparison */}
          <div className="space-y-4">
            <div className="bg-red-950/30 border border-red-900/60 p-4 rounded-xl space-y-1">
              <span className="text-xs text-red-300 font-semibold uppercase tracking-wider block">
                Without Guardrails (Unmitigated Potential Daily Damage):
              </span>
              <span className="text-xl font-bold text-red-400 font-mono">₹350,000.00</span>
              <p className="text-[11px] text-red-300/80">Calculated as 5 unconstrained ₹70,000+ purchases</p>
            </div>

            <div className="bg-emerald-950/30 border border-emerald-900/60 p-4 rounded-xl space-y-1">
              <span className="text-xs text-emerald-300 font-semibold uppercase tracking-wider block">
                With IntentGate Protection (Strict Daily Exposure Cap):
              </span>
              <span className="text-xl font-bold text-emerald-400 font-mono">₹100,000.00</span>
              <p className="text-[11px] text-emerald-300/80">Hard limit enforced by Agent Passport</p>
            </div>

            <div className="bg-[#0b1426] p-4 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400 block">Financial Exposure Capped By:</span>
                <span className="text-lg font-bold text-cyan-400 font-mono">71.4% Risk Reduction</span>
              </div>
              <span className="text-xs font-bold px-3 py-1 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                Protected
              </span>
            </div>
          </div>

          {/* Trust Breakdown */}
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Operational Trust Score: 94 / 100</h4>
            <div className="space-y-2 text-xs">
              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Intent Adherence:</span>
                  <span className="text-slate-200 font-mono">98%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: "98%" }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Policy Compliance:</span>
                  <span className="text-slate-200 font-mono">95%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: "95%" }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
