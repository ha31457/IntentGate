"use client";

import React, { useEffect, useState } from "react";
import { fetchOverview, DashboardOverview } from "../lib/api";
import { Activity, ShieldCheck, ShieldAlert, Zap, Lock, DollarSign, Award, Clock } from "lucide-react";

export const OverviewView: React.FC = () => {
  const [data, setData] = useState<DashboardOverview | null>(null);

  useEffect(() => {
    fetchOverview().then(setData).catch(console.error);
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Activity className="w-7 h-7 text-blue-400" />
          Security & Trust Overview Command Center
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Real-time deterministic monitoring for autonomous commerce agent execution.
        </p>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-[#0f172a] p-5 rounded-2xl border border-slate-800/80 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Evaluations</span>
          <div className="text-2xl font-bold text-white font-mono">{data?.total_transactions_evaluated ?? 0}</div>
          <span className="text-[10px] text-blue-400">Total Evaluated</span>
        </div>

        <div className="bg-[#0f172a] p-5 rounded-2xl border border-slate-800/80 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Allowed</span>
          <div className="text-2xl font-bold text-emerald-400 font-mono">{data?.allowed_count ?? 0}</div>
          <span className="text-[10px] text-emerald-400">Passed Policies</span>
        </div>

        <div className="bg-[#0f172a] p-5 rounded-2xl border border-slate-800/80 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Blocked</span>
          <div className="text-2xl font-bold text-red-400 font-mono">{data?.blocked_count ?? 0}</div>
          <span className="text-[10px] text-red-400">Security Violations</span>
        </div>

        <div className="bg-[#0f172a] p-5 rounded-2xl border border-slate-800/80 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Intent Drift</span>
          <div className="text-2xl font-bold text-amber-400 font-mono">{data?.intent_drift_count ?? 0}</div>
          <span className="text-[10px] text-amber-400">Boundary Violations</span>
        </div>

        <div className="bg-[#0f172a] p-5 rounded-2xl border border-slate-800/80 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Protected Exposure</span>
          <div className="text-xl font-bold text-cyan-400 font-mono">₹250,000</div>
          <span className="text-[10px] text-cyan-400">Risk Mitigation</span>
        </div>

        <div className="bg-[#0f172a] p-5 rounded-2xl border border-slate-800/80 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Avg Trust Score</span>
          <div className="text-2xl font-bold text-indigo-400 font-mono">{data?.average_agent_trust_score ?? 94}/100</div>
          <span className="text-[10px] text-indigo-400">Agent Reputation</span>
        </div>
      </div>

      {/* Main Grid: Recent Activity Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Transactions */}
        <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-blue-400" />
            Recent Evaluated Transactions
          </h3>
          <div className="space-y-3">
            {data?.recent_transactions && data.recent_transactions.length > 0 ? (
              data.recent_transactions.map((tx: any) => (
                <div
                  key={tx.id}
                  className="p-3 bg-[#0b1426] rounded-xl border border-slate-800 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-semibold text-slate-200">{tx.product_title}</div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      Proposed: ₹{tx.proposed_price?.toLocaleString("en-IN")}
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`font-bold text-[10px] px-2.5 py-0.5 rounded uppercase ${
                        tx.decision === "ALLOW"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-red-950 text-red-400 border border-red-800"
                      }`}
                    >
                      {tx.decision} ({tx.status})
                    </span>
                    <div className="text-[10px] text-slate-500 font-mono mt-1">
                      {new Date(tx.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 font-mono">No transactions evaluated yet.</p>
            )}
          </div>
        </div>

        {/* Live Security Event Logs */}
        <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Live Security Audit Trail
          </h3>
          <div className="space-y-3">
            {data?.recent_events && data.recent_events.length > 0 ? (
              data.recent_events.map((ev: any) => (
                <div
                  key={ev.id}
                  className="p-3 bg-[#0b1426] rounded-xl border border-slate-800 space-y-1 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-blue-400 uppercase">{ev.stage}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-slate-300 text-[11px]">{ev.reason}</p>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 font-mono">No security events logged yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
