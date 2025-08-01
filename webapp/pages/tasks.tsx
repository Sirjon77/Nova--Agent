"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Layout from "../components/Layout";

interface Task {
  id: string;
  type: string;
  params: Record<string, any>;
  status: string;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  result?: any;
}

/**
 * Tasks page displays all tasks tracked by the Nova Agent and listens
 * for real‑time updates via the WebSocket event channel. The list
 * automatically updates when tasks are created or change status.
 */
export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("nova_token") : null;
    if (!token) {
      router.replace("/login");
      return;
    }
    const headers: any = { Authorization: `Bearer ${token}` };
    // Fetch current list of tasks on mount
    const fetchTasks = async () => {
      try {
        const res = await fetch("/api/tasks", { headers });
        if (res.ok) {
          const data = await res.json();
          // The API returns an array or object keyed by task IDs. Normalise to array.
          const arr: Task[] = Array.isArray(data)
            ? data
            : Object.values(data as Record<string, Task>);
          setTasks(arr);
        } else {
          throw new Error(`Error ${res.status}`);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load tasks");
      }
    };
    fetchTasks();
    // Open WebSocket for real‑time task updates
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${wsProtocol}://${window.location.host}/ws/events`;
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event === "task_update" && msg.task) {
          const updated: Task = msg.task;
          setTasks((prev) => {
            const index = prev.findIndex((t) => t.id === updated.id);
            if (index >= 0) {
              const newList = [...prev];
              newList[index] = updated;
              return newList;
            }
            return [...prev, updated];
          });
        }
      } catch {
        // Ignore malformed messages
      }
    };
    ws.onerror = () => {
      // Ignore websocket errors for now
    };
    return () => {
      ws.close();
    };
  }, [router]);

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">Tasks</h1>
      {error && <div className="text-red-600 mb-4">{error}</div>}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white rounded shadow">
          <thead>
            <tr>
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Type</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Created</th>
              <th className="px-4 py-2 text-left">Result</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id} className="border-t">
                <td className="px-4 py-2 font-mono text-xs">
                  {task.id.slice(0, 8)}
                </td>
                <td className="px-4 py-2 capitalize">{task.type.replace(/_/g, " ")}</td>
                <td className="px-4 py-2">
                  <span
                    className={
                      task.status === "completed"
                        ? "text-green-600"
                        : task.status === "failed"
                        ? "text-red-600"
                        : task.status === "running"
                        ? "text-blue-600"
                        : "text-gray-700"
                    }
                  >
                    {task.status}
                  </span>
                </td>
                <td className="px-4 py-2">
                  {task.created_at ? new Date(task.created_at).toLocaleString() : ""}
                </td>
                <td className="px-4 py-2 truncate max-w-xs">
                  {task.result
                    ? typeof task.result === "string"
                      ? task.result
                      : JSON.stringify(task.result)
                    : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}