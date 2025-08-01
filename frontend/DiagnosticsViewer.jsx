
import React, { useEffect, useState } from 'react';

const DiagnosticsViewer = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/diagnostics/loop_health_report.json')
      .then(response => response.json())
      .then(data => {
        setLogs(data.logs || []);
        setLoading(false);
      })
      .catch(error => {
        console.error("Failed to load diagnostics:", error);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-4">Loading diagnostics...</div>;

  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">🩺 Nova Diagnostics Viewer</h2>
      <ul className="space-y-2 max-h-[60vh] overflow-y-scroll">
        {logs.map((log, index) => (
          <li key={entry.id || index} className="bg-gray-100 p-2 rounded">
            {log.timestamp} — {log.message}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DiagnosticsViewer;
