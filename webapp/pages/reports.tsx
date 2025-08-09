"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Layout from "../components/Layout";

interface Channel {
  channel_id: string;
  score: number;
  flag?: string | null;
  action?: string | null;
  rpm?: number;
  avg_watch_minutes?: number;
  ctr?: number;
  subs_gained?: number;
}

interface Trend {
  keyword: string;
  interest: number;
  projected_rpm: number;
  source: string;
  scanned_on: string;
}

interface ToolHealth {
  tool: string;
  latency_ms: number;
  status: string;
  score: number;
}

interface GovernanceReport {
  timestamp: string;
  channels: Channel[];
  trends: Trend[];
  tools: ToolHealth[];
  changelogs: any[];
  insight_summaries?: string[];
  new_niche_suggestions?: { niche: string; source: string; rationale: string }[];
}

/**
 * Reports page lists available governance reports and allows viewing
 * specific historical reports as well as the latest. The page fetches
 * available report filenames (dates) on mount and loads the selected
 * report when the user chooses a date. Report details are displayed
 * in sections similar to the dashboard but for the chosen date.
 */
export default function ReportsPage() {
  const [history, setHistory] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [report, setReport] = useState<GovernanceReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // Fetch report history on mount
  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("nova_token") : null;
    if (!token) {
      router.replace("/login");
      return;
    }
    const headers: any = { Authorization: `Bearer ${token}` };
    async function fetchHistory() {
      try {
        const res = await fetch("/api/governance/history", { headers });
        if (res.ok) {
          const list = await res.json();
          if (Array.isArray(list)) {
            setHistory(list);
          }
        }
      } catch {
        // history may be unavailable if reports directory is empty
      }
    }
    // always fetch the latest report too
    async function fetchLatest() {
      try {
        const res = await fetch("/api/governance/report", { headers });
        if (res.ok) {
          const rep = await res.json();
          setReport(rep);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load report");
      }
    }
    fetchHistory();
    fetchLatest();
  }, [router]);

  // Fetch a specific report by date
  const fetchReport = async (date?: string) => {
    const token = localStorage.getItem("nova_token");
    if (!token) return;
    const headers: any = { Authorization: `Bearer ${token}` };
    try {
      const url = date ? `/api/governance/report?date=${encodeURIComponent(date)}` : "/api/governance/report";
      const res = await fetch(url, { headers });
      if (res.ok) {
        const rep = await res.json();
        setReport(rep);
        setSelectedDate(date || "");
      } else {
        const txt = await res.text();
        setError(`Failed to fetch report: ${txt}`);
      }
    } catch (err: any) {
      setError(err.message || "Error fetching report");
    }
  };

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">Governance Reports</h1>
      {error && <div className="text-red-600 mb-4">{error}</div>}
      {/* Report selector */}
      {history.length > 0 && (
        <div className="mb-4">
          <label className="mr-2 font-medium">Historical Reports:</label>
          <select
            value={selectedDate}
            onChange={(e) => fetchReport(e.target.value || undefined)}
            className="border rounded px-2 py-1"
          >
            <option value="">Latest</option>
            {history.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
      )}
      {/* Report display */}
      {report ? (
        <div className="space-y-8">
          <section>
            <h2 className="text-xl font-semibold mb-2">Channels (Report {report.timestamp})</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white rounded shadow">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left">Channel ID</th>
                    <th className="px-4 py-2 text-left">Score</th>
                    <th className="px-4 py-2 text-left">Flag</th>
                  </tr>
                </thead>
                <tbody>
                  {report.channels.map((c) => (
                    <tr key={c.channel_id} className="border-t">
                      <td className="px-4 py-2">
                        <a href={`/channels/${c.channel_id}`} className="text-blue-600 hover:underline">
                          {c.channel_id}
                        </a>
                      </td>
                      <td className="px-4 py-2">{c.score?.toFixed(2)}</td>
                      <td className="px-4 py-2">
                        {c.flag ? (
                          <span
                            className={
                              c.flag === "promote"
                                ? "text-green-600"
                                : c.flag === "retire"
                                ? "text-red-600"
                                : "text-yellow-600"
                            }
                          >
                            {c.flag}
                          </span>
                        ) : (
                          ""
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <section>
            <h2 className="text-xl font-semibold mb-2">Trends</h2>
            {report.trends && report.trends.length > 0 ? (
              <ul className="list-disc ml-6 space-y-1">
                {report.trends.map((t, idx) => (
                  <li key={idx}>
                    {t.keyword} ({t.source} – {t.interest})
                  </li>
                ))}
              </ul>
            ) : (
              <p>No trends available.</p>
            )}
          </section>
          {report.insight_summaries && report.insight_summaries.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold mb-2">Insight Summaries</h2>
              <ul className="list-disc ml-6 space-y-1">
                {report.insight_summaries.map((s, idx) => (
                  <li key={idx}>{s}</li>
                ))}
              </ul>
            </section>
          )}
          {report.new_niche_suggestions && report.new_niche_suggestions.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold mb-2">New Niche Suggestions</h2>
              <ul className="list-disc ml-6 space-y-1">
                {report.new_niche_suggestions.map((n, idx) => (
                  <li key={idx}>
                    <span className="font-medium">{n.niche}</span> ({n.source}) — {n.rationale}
                  </li>
                ))}
              </ul>
            </section>
          )}
          <section>
            <h2 className="text-xl font-semibold mb-2">Tool Health</h2>
            {report.tools && report.tools.length > 0 ? (
              <table className="min-w-full bg-white rounded shadow">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left">Tool</th>
                    <th className="px-4 py-2 text-left">Status</th>
                    <th className="px-4 py-2 text-left">Latency (ms)</th>
                  </tr>
                </thead>
                <tbody>
                  {report.tools.map((tool) => (
                    <tr key={tool.tool} className="border-t">
                      <td className="px-4 py-2">{tool.tool}</td>
                      <td className="px-4 py-2">
                        <span
                          className={tool.status === "ok" ? "text-green-600" : "text-red-600"}
                        >
                          {tool.status}
                        </span>
                      </td>
                      <td className="px-4 py-2">{tool.latency_ms}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No tool data available.</p>
            )}
          </section>
          {report.changelogs && report.changelogs.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold mb-2">Changelog Alerts</h2>
              <ul className="list-disc ml-6 space-y-1">
                {report.changelogs.map((log: any, idx: number) => (
                  <li key={idx}>{JSON.stringify(log)}</li>
                ))}
              </ul>
            </section>
          )}
        </div>
      ) : (
        <p>Loading report...</p>
      )}
    </Layout>
  );
}