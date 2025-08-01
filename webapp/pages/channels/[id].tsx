"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Layout from "../../components/Layout";

interface Channel {
  channel_id: string;
  score: number;
  flag?: string | null;
  rpm?: number;
  avg_watch_minutes?: number;
  ctr?: number;
  subs_gained?: number;
  action?: string | null;
}

interface GovernanceReport {
  timestamp: string;
  channels: Channel[];
  trends: any[];
  tools: any[];
  changelogs: any[];
}

/**
 * Detailed channel page. Displays information about a single channel
 * pulled from the list of channels and the most recent governance
 * report. Provides buttons to trigger various actions such as
 * generating extra content or running governance manually. Some
 * actions may be placeholders if the backend does not support them.
 */
export default function ChannelDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [channel, setChannel] = useState<Channel | null>(null);
  const [report, setReport] = useState<GovernanceReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [override, setOverride] = useState<string | null>(null);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("nova_token") : null;
    if (!token) {
      router.replace("/login");
      return;
    }
    if (!id) return;
    const headers: any = { Authorization: `Bearer ${token}` };
    async function fetchDetails() {
      try {
        // Fetch all channels then find the one matching the route param
        const resChannels = await fetch("/api/channels", { headers });
        if (resChannels.ok) {
          const data = await resChannels.json();
          const list: Channel[] = Array.isArray(data)
            ? data
            : Object.values(data as Record<string, Channel>);
          const found = list.find((c) => c.channel_id === id);
          setChannel(found || null);
        }
        // Fetch latest report for additional metrics
        const resReport = await fetch("/api/governance/report", { headers });
        if (resReport.ok) {
          const rep = await resReport.json();
          setReport(rep);
        }
        // Fetch current override for this channel (admin only; if unauthorized, ignore)
        try {
          const resOverride = await fetch(`/api/channels/${id}/override`, { headers });
          if (resOverride.ok) {
            const odata = await resOverride.json();
            setOverride(odata.override || null);
          }
        } catch (_) {
          // ignore
        }
      } catch (err: any) {
        setError(err.message || "Failed to load channel");
      }
    }
    fetchDetails();
  }, [id, router]);

  /**
   * Helper to trigger a dummy content generation task for this channel.
   */
  const handleGenerateContent = async () => {
    const token = localStorage.getItem("nova_token");
    if (!token || !id) return;
    try {
      const res = await fetch("/api/tasks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ type: "generate_content", params: { channel_id: id } }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Content generation task started (task id: ${data.id || data.task_id || "unknown"})`);
      } else {
        const t = await res.text();
        setError(`Failed to create task: ${t}`);
      }
    } catch (err: any) {
      setError(err.message || "Failed to call task API");
    }
  };

  /**
   * Trigger a manual governance run via the API. This action is only
   * available to admin users and will enqueue a governance task.
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
        setMessage(`Governance run started (task id: ${data.id || data.task_id || "unknown"})`);
      } else {
        const text = await res.text();
        setError(`Failed to start governance: ${text}`);
      }
    } catch (err: any) {
      setError(err.message || "Error starting governance");
    }
  };

  /**
   * Set or clear an override directive for this channel. Passing a null action
   * will clear the override (DELETE request); otherwise a POST request is
   * issued with the given action.
   */
  const handleOverrideChange = async (action: string | null) => {
    const token = localStorage.getItem("nova_token");
    if (!token || !id) return;
    try {
      if (action === null || action === "") {
        // Clear override
        const res = await fetch(`/api/channels/${id}/override`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          setOverride(null);
          setMessage("Override cleared");
        } else {
          const txt = await res.text();
          setError(`Failed to clear override: ${txt}`);
        }
      } else {
        // Set override
        const res = await fetch(`/api/channels/${id}/override`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ action }),
        });
        if (res.ok) {
          const data = await res.json();
          setOverride(data.override || action);
          setMessage(`Override set to ${action}`);
        } else {
          const txt = await res.text();
          setError(`Failed to set override: ${txt}`);
        }
      }
    } catch (err: any) {
      setError(err.message || "Error updating override");
    }
  };

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">Channel Details</h1>
      {error && <div className="text-red-600 mb-4">{error}</div>}
      {message && <div className="text-green-600 mb-4">{message}</div>}
      {!channel ? (
        <p>Loading channel details...</p>
      ) : (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">{channel.channel_id}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded shadow">
              <h3 className="font-semibold mb-1">Score</h3>
              <p>{channel.score?.toFixed(2)}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h3 className="font-semibold mb-1">Flag</h3>
              <p>
                {channel.flag ? (
                  <span
                    className={
                      channel.flag === "promote"
                        ? "text-green-600"
                        : channel.flag === "retire"
                        ? "text-red-600"
                        : "text-yellow-600"
                    }
                  >
                    {channel.flag}
                  </span>
                ) : (
                  "None"
                )}
              </p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h3 className="font-semibold mb-1">RPM</h3>
              <p>{channel.rpm !== undefined ? channel.rpm.toFixed(2) : "N/A"}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h3 className="font-semibold mb-1">Avg Watch Minutes</h3>
              <p>
                {channel.avg_watch_minutes !== undefined
                  ? channel.avg_watch_minutes.toFixed(2)
                  : "N/A"}
              </p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h3 className="font-semibold mb-1">CTR</h3>
              <p>{channel.ctr !== undefined ? channel.ctr.toFixed(2) : "N/A"}</p>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <h3 className="font-semibold mb-1">Subs Gained</h3>
              <p>{channel.subs_gained !== undefined ? channel.subs_gained : "N/A"}</p>
            </div>
          </div>
          {/* Override control */}
          <div className="bg-white p-4 rounded shadow">
            <h3 className="font-semibold mb-1">Override</h3>
            <p className="mb-2">
              {override ? <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">{override}</span> : "None"}
            </p>
            <label htmlFor="override-select" className="mr-2">Set override:</label>
            <select
              id="override-select"
              value={override || ""}
              onChange={(e) => {
                const val = e.target.value;
                handleOverrideChange(val === "" ? null : val);
              }}
              className="border border-gray-300 rounded px-2 py-1"
            >
              <option value="">-- none --</option>
              <option value="force_retire">force_retire</option>
              <option value="force_promote">force_promote</option>
              <option value="ignore_retire">ignore_retire</option>
              <option value="ignore_promote">ignore_promote</option>
            </select>
          </div>
          <div className="space-x-4 mt-4">
            <button
              onClick={handleGenerateContent}
              className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700"
            >
              Generate Content
            </button>
            <button
              onClick={handleRunGovernance}
              className="bg-purple-600 text-white px-4 py-2 rounded shadow hover:bg-purple-700"
            >
              Run Governance Now
            </button>
          </div>
        </div>
      )}
    </Layout>
  );
}