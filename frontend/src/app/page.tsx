"use client";

import React, { useState } from "react";
import { Navigation } from "../components/Navigation";
import { OverviewView } from "../components/OverviewView";
import { IntentFirewallView } from "../components/IntentFirewallView";
import { TransactionReplayView } from "../components/TransactionReplayView";
import { ChaosLabView } from "../components/ChaosLabView";
import { PassportsView } from "../components/PassportsView";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("firewall");

  return (
    <div className="min-h-screen bg-[#0b1426] text-slate-100 flex flex-col font-sans">
      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        {activeTab === "overview" && <OverviewView />}
        {activeTab === "firewall" && <IntentFirewallView />}
        {activeTab === "replay" && <TransactionReplayView />}
        {activeTab === "chaos" && <ChaosLabView />}
        {activeTab === "passports" && <PassportsView />}
      </main>

      <footer className="border-t border-slate-800/80 bg-[#070c18] py-4 text-center text-xs text-slate-500 font-mono">
        INTENTGATE v1.0.0 — Runtime Trust Layer for Autonomous Commerce Agents | Razorpay Buildathon Demo Mode
      </footer>
    </div>
  );
}
