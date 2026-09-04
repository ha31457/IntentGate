"use client";

import React from "react";
import { Shield, Activity, Zap, Layers, RefreshCw, Terminal } from "lucide-react";

interface NavigationProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "firewall", label: "Intent Firewall", icon: Shield },
    { id: "replay", label: "Transaction Replay", icon: Terminal },
    { id: "chaos", label: "Chaos Lab", icon: Zap },
    { id: "passports", label: "Passports & Policy", icon: Layers },
  ];

  return (
    <header className="border-b border-slate-800/80 bg-[#0b1426]/95 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-wider text-white">INTENTGATE</span>
              <span className="text-[10px] uppercase tracking-widest font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Razorpay Buildathon
              </span>
            </div>
            <p className="text-xs text-slate-400">Runtime Trust Layer for Autonomous Commerce Agents</p>
          </div>
        </div>

        {/* Center Tabs */}
        <nav className="flex items-center gap-1 bg-[#0f172a] p-1 rounded-xl border border-slate-800/80">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-[#1463ff] text-white shadow-md shadow-blue-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Live Status Indicators */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-300 font-mono text-[11px]">Razorpay Test Mode</span>
          </div>
        </div>
      </div>
    </header>
  );
};
