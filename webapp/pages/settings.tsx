"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Layout from "../components/Layout";

/**
 * Settings and controls page. At this stage the backend exposes few
 * mutable settings, so this page focuses on manual triggers and
 * displaying configuration values that are relevant to operators.
 */
export default function SettingsPage() {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("nova_token") : null;
    if (!token) {
      router.replace("/login");
    }
  }, [router]);

  /**
   * Trigger a manual governance run via the API. Useful for debugging or
   * when an immediate evaluation is needed between scheduled cycles.
   */
  const handleRunGovernance = async () => {
    const token = localStorage.getItem("nova_token");
    if (!token) return;
    try {
      const res = await fetch("/api/governance/run", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Governance run scheduled (task id: ${data.id || data.task_id || "unknown"})`);
        setError(null);
      } else {
        const text = await res.text();
        setError(`Failed to schedule governance: ${text}`);
      }
    } catch (err: any) {
      setError(err.message || "Error scheduling governance");
    }
  };

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">Settings & Controls</h1>
      {message && <div className="text-green-600 mb-4">{message}</div>}
      {error && <div className="text-red-600 mb-4">{error}</div>}
      <div className="space-y-6">
        <section>
          <h2 className="text-xl font-semibold mb-2">Manual Actions</h2>
          <button
            onClick={handleRunGovernance}
            className="bg-purple-600 text-white px-4 py-2 rounded shadow hover:bg-purple-700"
          >
            Run Governance Now
          </button>
        </section>
        <section>
          <h2 className="text-xl font-semibold mb-2">Notification Settings</h2>
          <p>
            Notification settings (Slack webhook, email) are currently
            configured via environment variables on the backend. Changes
            require updating your server configuration.
          </p>
        </section>
        <section>
          <h2 className="text-xl font-semibold mb-2">Automation Toggles</h2>
          <p>
            Feature toggles such as auto‑publishing or disabling
            governance actions will be exposed here once supported by the
            backend. For now, governance actions are always enabled.
          </p>
        </section>
      </div>
    </Layout>
  );
}