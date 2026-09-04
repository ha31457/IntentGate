"use client";

import React, { useState } from "react";
import { extractIntent, authorizeTransaction, IntentExtractResponse, TransactionAuthorizeResponse } from "../lib/api";
import { Shield, Sparkles, CheckCircle2, XCircle, ArrowRight, Lock, Key, Cpu, AlertTriangle, CreditCard, ExternalLink } from "lucide-react";

export const IntentFirewallView: React.FC = () => {
  const [prompt, setPrompt] = useState("Find me a good laptop for programming under ₹70,000. Buy it if you find one that meets my requirements.");
  const [loadingExtract, setLoadingExtract] = useState(false);
  const [loadingAuthorize, setLoadingAuthorize] = useState(false);
  
  const [intentData, setIntentData] = useState<IntentExtractResponse | null>(null);
  const [proposedPrice, setProposedPrice] = useState(68999);
  const [proposedQty, setProposedQty] = useState(1);
  const [selectedProduct, setSelectedProduct] = useState("prod_devbook_pro");
  const [authResponse, setAuthResponse] = useState<TransactionAuthorizeResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const openRazorpayCheckout = () => {
    if (!authResponse?.razorpay_order_id) return;
    const keyId = authResponse.razorpay_key_id || "rzp_test_TWjbM7MSFSBznv";

    const loadScript = (src: string): Promise<boolean> => {
      return new Promise((resolve) => {
        if ((window as any).Razorpay) return resolve(true);
        const script = document.createElement("script");
        script.src = src;
        script.onload = () => resolve(true);
        script.onerror = () => resolve(false);
        document.body.appendChild(script);
      });
    };

    loadScript("https://checkout.razorpay.com/v1/checkout.js").then((success) => {
      if (!success) {
        alert("Failed to load Razorpay Checkout SDK. Please check your internet connection.");
        return;
      }
      const options = {
        key: keyId,
        amount: Math.round(proposedPrice * 100),
        currency: "INR",
        name: "IntentGate",
        description: `Authorization & Settlement for ${selectedProduct}`,
        order_id: authResponse.razorpay_order_id,
        handler: function (response: any) {
          alert(`Razorpay Payment Success!\nPayment ID: ${response.razorpay_payment_id}\nOrder ID: ${response.razorpay_order_id}`);
        },
        prefill: {
          name: "Shopping Agent Alpha",
          email: "agent@intentgate.dev",
          contact: "9999999999",
        },
        theme: {
          color: "#1463ff",
        },
      };
      const rzp = new (window as any).Razorpay(options);
      rzp.open();
    });
  };

  const handleExtract = async () => {
    setLoadingExtract(true);
    setErrorMsg("");
    setAuthResponse(null);
    try {
      const data = await extractIntent(prompt);
      setIntentData(data);
      setProposedPrice(data.max_budget > 70000 ? data.max_budget : 68999);
    } catch (e: any) {
      setErrorMsg(e.message || "Intent extraction failed");
    } finally {
      setLoadingExtract(false);
    }
  };

  const handleAuthorize = async () => {
    if (!intentData) return;
    setLoadingAuthorize(true);
    setErrorMsg("");
    try {
      const idempKey = `idemp_live_${Date.now()}`;
      const res = await authorizeTransaction({
        agent_id: intentData.agent_id,
        intent_id: intentData.intent_id,
        intent_fingerprint: intentData.fingerprint,
        product_id: selectedProduct,
        proposed_price: Number(proposedPrice),
        proposed_quantity: Number(proposedQty),
        idempotency_key: idempKey
      });
      setAuthResponse(res);
    } catch (e: any) {
      setErrorMsg(e.message || "Transaction authorization failed");
    } finally {
      setLoadingAuthorize(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Title Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Shield className="w-7 h-7 text-blue-400" />
            Intent Firewall Pipeline
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            "LLMs propose. Policies constrain. APIs execute. Verification proves. Audit remembers."
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setPrompt("Find me a good laptop for programming under ₹70,000. Buy it if you find one that meets my requirements.")}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            Sample: ₹70k Laptop
          </button>
          <button
            onClick={() => {
              setPrompt("Find me a gaming laptop under ₹70,000.");
              setProposedPrice(72999);
            }}
            className="px-3 py-1.5 text-xs bg-red-950/40 hover:bg-red-900/40 text-red-300 rounded-lg border border-red-800/40 transition"
          >
            Sample: Budget Drift (+₹2,999)
          </button>
        </div>
      </div>

      {/* Step 1: Natural Language Prompt Input */}
      <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            Step 1 — Natural Language User Prompt (Probabilistic Input)
          </label>
          <span className="text-xs text-slate-400">Agent: Shopping Agent Alpha (Trust Level 3)</span>
        </div>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
          className="w-full bg-[#0b1426] border border-slate-700 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition font-mono"
        />
        <button
          onClick={handleExtract}
          disabled={loadingExtract}
          className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-blue-600/20 transition disabled:opacity-50"
        >
          {loadingExtract ? "Extracting Intent..." : "Extract Intent & Generate HMAC Fingerprint"}
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Step 2: Intent Fingerprint & Assumption Ledger */}
      {intentData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Fingerprint Card */}
          <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Key className="w-4 h-4 text-cyan-400" />
                HMAC-SHA256 Intent Fingerprint
              </h3>
              <span className="text-[10px] bg-cyan-950 text-cyan-400 px-2 py-0.5 rounded border border-cyan-800">
                Salted HMAC
              </span>
            </div>
            <div className="space-y-2">
              <p className="text-xs text-slate-400">Canonical Identity Hash:</p>
              <div className="bg-[#0b1426] p-3 rounded-lg border border-slate-800 font-mono text-[11px] text-cyan-300 break-all select-all">
                {intentData.fingerprint}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs text-slate-300 pt-2">
              <div>
                <span className="text-slate-500">Category:</span>{" "}
                <span className="font-semibold text-slate-200">{intentData.category}</span>
              </div>
              <div>
                <span className="text-slate-500">Max Budget:</span>{" "}
                <span className="font-semibold text-emerald-400">₹{intentData.max_budget.toLocaleString("en-IN")}</span>
              </div>
              <div>
                <span className="text-slate-500">Max Quantity:</span>{" "}
                <span className="font-semibold text-slate-200">{intentData.quantity}</span>
              </div>
              <div>
                <span className="text-slate-500">Purpose:</span>{" "}
                <span className="font-semibold text-slate-200">{intentData.purpose}</span>
              </div>
            </div>
          </div>

          {/* Assumption Ledger Card */}
          <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-400" />
                Assumption Ledger
              </h3>
              <span className="text-[10px] bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800">
                Boundaries vs Inferences
              </span>
            </div>
            <div className="space-y-3 text-xs">
              <div>
                <span className="text-emerald-400 font-semibold uppercase tracking-wider text-[10px]">
                  Explicit Constraints (Authorization Boundaries):
                </span>
                <div className="bg-[#0b1426] p-2.5 rounded-lg border border-slate-800 mt-1 font-mono text-slate-300">
                  {JSON.stringify(intentData.explicit_constraints)}
                </div>
              </div>
              <div>
                <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                  AI-Inferred Assumptions (Metadata Only):
                </span>
                <div className="bg-[#0b1426] p-2.5 rounded-lg border border-slate-800 mt-1 font-mono text-slate-400">
                  {JSON.stringify(intentData.inferred_assumptions)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Agent Proposal Execution */}
      {intentData && (
        <div className="bg-[#0f172a] rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-blue-400" />
            Step 2 — Submit Agent Purchase Proposal for Deterministic Evaluation
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Select Product</label>
              <select
                value={selectedProduct}
                onChange={(e) => {
                  setSelectedProduct(e.target.value);
                  if (e.target.value === "prod_ultradev_x") setProposedPrice(74999);
                  else if (e.target.value === "prod_codemax_14") setProposedPrice(64999);
                  else setProposedPrice(68999);
                }}
                className="w-full bg-[#0b1426] border border-slate-700 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="prod_devbook_pro">DevBook Pro 15 (₹68,999)</option>
                <option value="prod_codemax_14">CodeMax 14 (₹64,999)</option>
                <option value="prod_ultradev_x">UltraDev X 16 (₹74,999)</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Proposed Price (₹)</label>
              <input
                type="number"
                value={proposedPrice}
                onChange={(e) => setProposedPrice(Number(e.target.value))}
                className="w-full bg-[#0b1426] border border-slate-700 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Proposed Quantity</label>
              <input
                type="number"
                value={proposedQty}
                onChange={(e) => setProposedQty(Number(e.target.value))}
                className="w-full bg-[#0b1426] border border-slate-700 rounded-xl p-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>
          </div>

          <button
            onClick={handleAuthorize}
            disabled={loadingAuthorize}
            className="w-full py-3 bg-[#1463ff] hover:bg-blue-600 text-white font-semibold rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-blue-600/30 transition disabled:opacity-50"
          >
            {loadingAuthorize ? "Evaluating Policies..." : "Evaluate IntentGate Policy Engine & Execute Transaction"}
          </button>
        </div>
      )}

      {/* Step 4: Policy Engine Decision Visual Output */}
      {authResponse && (
        <div
          className={`rounded-2xl p-6 border transition-all ${
            authResponse.decision === "ALLOW"
              ? "bg-emerald-950/30 border-emerald-500/50 glow-green"
              : "bg-red-950/30 border-red-500/50 glow-red"
          }`}
        >
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4 mb-4">
            <div className="flex items-center gap-3">
              {authResponse.decision === "ALLOW" ? (
                <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
              ) : (
                <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/30 flex items-center justify-center text-red-400">
                  <XCircle className="w-6 h-6" />
                </div>
              )}
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  POLICY DECISION:{" "}
                  <span className={authResponse.decision === "ALLOW" ? "text-emerald-400" : "text-red-400"}>
                    {authResponse.decision}
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  Payment Status: <span className="font-mono text-slate-200">{authResponse.status}</span>
                  {authResponse.razorpay_order_id && (
                    <span className="ml-3 text-blue-400 font-mono">Order ID: {authResponse.razorpay_order_id}</span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {authResponse.price_variance > 0 && (
                <div className="bg-red-900/50 text-red-300 border border-red-700/50 px-3 py-1.5 rounded-lg text-xs font-mono">
                  Variance: +₹{authResponse.price_variance.toLocaleString("en-IN")}
                </div>
              )}
              {authResponse.decision === "ALLOW" && authResponse.razorpay_order_id && (
                <button
                  onClick={openRazorpayCheckout}
                  className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl flex items-center gap-2 shadow-lg shadow-blue-600/30 transition animate-pulse"
                >
                  <CreditCard className="w-4 h-4" />
                  Open Razorpay Payment UI
                  <ExternalLink className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          {/* Block Reason Highlight */}
          {authResponse.block_reason && (
            <div className="bg-red-900/30 border border-red-800/50 rounded-xl p-4 text-xs text-red-200 font-mono mb-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-red-300 uppercase tracking-wider mb-1">Transaction Block Rationale:</div>
                <div>{authResponse.block_reason}</div>
              </div>
            </div>
          )}

          {/* Detailed Policy Checks Grid */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Deterministic Policy Checks:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {authResponse.evaluations.map((ev, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-xl border text-xs flex items-start justify-between ${
                    ev.status === "PASS"
                      ? "bg-[#0b1426]/60 border-slate-800 text-slate-300"
                      : "bg-red-950/40 border-red-800/50 text-red-200"
                  }`}
                >
                  <div>
                    <div className="font-mono font-semibold text-[11px] text-slate-200">{ev.check_name}</div>
                    <div className="text-[11px] text-slate-400 mt-1">{ev.message}</div>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                      ev.status === "PASS" ? "bg-emerald-950 text-emerald-400" : "bg-red-900 text-red-300"
                    }`}
                  >
                    {ev.status}
                  </span>
                </div>
              ))}
            </div>
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
