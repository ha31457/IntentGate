"use client";

import React, { useState } from "react";
import { fetchReplay, TransactionReplayResponse } from "../lib/api";
import { Terminal, CheckCircle2, XCircle, Clock, Shield, Layers } from "lucide-react";

export const TransactionReplayView: React.FC = () => {
  const [txId, setTxId] = useState("tx_seed_001");
  const [loading, setLoading] = useState(false);
  const [replayData, setReplayData] = useState<TransactionReplayResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [recentTxList, setRecentTxList] = useState<any[]>([]);

  React.useEffect(() => {
    // Auto-fetch seed transaction on load
    handleFetchReplay("tx_seed_001");
    // Fetch recent transactions from overview
    import("../lib/api").then(m => m.fetchOverview()).then(data => {
      if (data && data.recent_transactions) {
        setRecentTxList(data.recent_transactions);
      }
    }).catch(console.error);
  }, []);

  const handleFetchReplay = async (targetId?: string) => {
    const idToFetch = targetId || txId;
    setLoading(true);
    setErrorMsg("");
    try {
      const data = await fetchReplay(idToFetch);
      setReplayData(data);
      setTxId(idToFetch);
    } catch (e: any) {
      setErrorMsg(e.message || "Replay fetch failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Terminal className="w-7 h-7 text-cyan-400" />
            Immutable Transaction Replay Timeline
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Complete audit trail proving exact step-by-step execution boundaries and decisions.
          </p>
        </div>
      </div>

      {/* Quick Select Preset Buttons */}
      {recentTxList.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-400 font-medium mr-1">Quick Select Recent ID:</span>
          {recentTxList.map((tx) => (
            <button
              key={tx.id}
              onClick={() => handleFetchReplay(tx.id)}
              className={`px-3 py-1 text-[11px] font-mono rounded-lg border transition ${
                txId === tx.id
                  ? "bg-cyan-950 border-cyan-500 text-cyan-300 font-bold"
                  : "bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-400"
              }`}
            >
              {tx.id.substring(0, 14)}... ({tx.decision})
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 flex gap-4 items-center">
        <input
          type="text"
          value={txId}
          onChange={(e) => setTxId(e.target.value)}
          placeholder="Enter Transaction UUID (e.g. tx_seed_001)..."
          className="flex-1 bg-[#0b1426] border border-slate-700 rounded-xl p-3 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
        />
        <button
          onClick={() => handleFetchReplay(txId)}
          disabled={loading}
          className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-cyan-600/20 transition disabled:opacity-50"
        >
          {loading ? "Loading Replay..." : "Replay Transaction Timeline"}
        </button>
      </div>

      {/* Timeline Replay */}
      {replayData && (
        <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs text-slate-400">Transaction ID:</span>{" "}
              <span className="font-mono text-xs text-cyan-300 font-bold">{replayData.transaction_id}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400">Idempotency Key:</span>{" "}
              <span className="font-mono text-xs text-slate-300">{replayData.idempotency_key}</span>
              <span
                className={`text-xs font-bold px-3 py-1 rounded-full uppercase ${
                  replayData.decision === "ALLOW"
                    ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                    : "bg-red-950 text-red-400 border border-red-800"
                }`}
              >
                {replayData.decision} ({replayData.status})
              </span>
            </div>
          </div>

          <div className="relative border-l-2 border-slate-800 ml-4 space-y-8 pl-6 py-2">
            {replayData.events.map((ev, idx) => (
              <div key={ev.id || idx} className="relative group">
                {/* Timeline Dot */}
                <div
                  className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full border-2 bg-[#0b1426] flex items-center justify-center ${
                    ev.decision === "PASS"
                      ? "border-emerald-500 text-emerald-400"
                      : ev.decision === "BLOCK" || ev.decision === "FAIL"
                      ? "border-red-500 text-red-400"
                      : "border-cyan-500 text-cyan-400"
                  }`}
                />

                <div className="bg-[#0b1426] rounded-xl p-4 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-white uppercase">{ev.stage}</span>
                      <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
                        Actor: {ev.actor}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300">{ev.reason}</p>

                  {ev.event_metadata && Object.keys(ev.event_metadata).length > 0 && (
                    <pre className="bg-[#070c18] p-2.5 rounded-lg border border-slate-800/80 font-mono text-[10px] text-slate-400 overflow-x-auto">
                      {JSON.stringify(ev.event_metadata, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="bg-red-950/60 border border-red-800 text-red-200 p-4 rounded-xl text-xs font-mono">
          Error: {errorMsg}
        </div>
      )}
    </div>
  );
};
