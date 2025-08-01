"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Layout from "../components/Layout";

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
}

/**
 * Dashboard page showing channel performance, trends and tool health.
 *
 * This component fetches the latest governance report and the channel list
 * when it mounts. If no token is present in localStorage, the user is
 * redirected to the login page.
 */
export default function DashboardPage() {
  const [report, setReport] = useState<GovernanceReport | null>(null);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("nova_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    async function fetchData() {
      try {
        const headers = { Authorization: `Bearer ${token}` } as any;
        // Fetch channel list
        const resChannels = await fetch("/api/channels", { headers });
        if (resChannels.ok) {
          const data = await resChannels.json();
          setChannels(data);
        }
        // Fetch latest governance report
        const resReport = await fetch("/api/governance/report", { headers });
        if (resReport.ok) {
          const data = await resReport.json();
          setReport(data);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load data");
      }
    }
    fetchData();
  }, [router]);

  if (error) {
    return (
      <Layout>
        <div className="text-red-600">Error: {error}</div>
      </Layout>
    );
  }
  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">Nova Dashboard</h1>
      {/* Summary section */}
      <section>
        <h2 className="text-xl font-semibold mb-2">Summary</h2>
        {report ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded shadow">
              <div className="text-gray-500 text-sm">Total Channels</div>
              <div className="text-2xl font-bold">{report.channels.length}</div>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <div className="text-gray-500 text-sm">Promoted</div>
              <div className="text-2xl font-bold">
                {report.channels.filter((c) => c.flag === "promote").length}
              </div>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <div className="text-gray-500 text-sm">Watched</div>
              <div className="text-2xl font-bold">
                {report.channels.filter((c) => c.flag === "watch").length}
              </div>
            </div>
            <div className="bg-white p-4 rounded shadow">
              <div className="text-gray-500 text-sm">Retired</div>
              <div className="text-2xl font-bold">
                {report.channels.filter((c) => c.flag === "retire").length}
              </div>
            </div>
          </div>
        ) : (
          <p>Loading...</p>
        )}
      </section>
      {/* Channels table */}
      <section>
        <h2 className="text-xl font-semibold mb-2">Channels</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white rounded shadow">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left">Channel ID</th>
                <th className="px-4 py-2 text-left">Score</th>
                <th className="px-4 py-2 text-left">Flag</th>
                <th className="px-4 py-2 text-left">Action</th>
              </tr>
            </thead>
            <tbody>
              {channels.map((c) => (
                <tr key={c.channel_id} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-2">
                    <a
                      href={`/channels/${c.channel_id}`}
                      className="text-blue-600 hover:underline"
                    >
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
                  <td className="px-4 py-2">{c.action || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {/* Trends section */}
      <section>
        <h2 className="text-xl font-semibold mb-2">Top Trends</h2>
        {report && report.trends.length > 0 ? (
          <ul className="list-disc ml-6">
            {report.trends.slice(0, 10).map((t, idx) => (
              <li key={idx}>
                {t.keyword} ({t.source} – {t.interest})
              </li>
            ))}
          </ul>
        ) : (
          <p>No trends available.</p>
        )}
      </section>
      {/* Tools health section */}
      <section>
        <h2 className="text-xl font-semibold mb-2">Tool Health</h2>
        {report && report.tools.length > 0 ? (
          <table className="min-w-full bg-white rounded shadow">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left">Tool</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-left">Latency (ms)</th>
                <th className="px-4 py-2 text-left">Score</th>
              </tr>
            </thead>
            <tbody>
              {report.tools.map((tool) => (
                <tr key={tool.tool} className="border-t">
                  <td className="px-4 py-2">{tool.tool}</td>
                  <td className="px-4 py-2">
                    <span
                      className={
                        tool.status === "ok" ? "text-green-600" : "text-red-600"
                      }
                    >
                      {tool.status}
                    </span>
                  </td>
                  <td className="px-4 py-2">{tool.latency_ms}</td>
                  <td className="px-4 py-2">{tool.score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No tools data available.</p>
        )}
      </section>
    </Layout>
  );
}