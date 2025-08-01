
import React, { useState } from 'react';

export function CrawlerPanel() {
  const [url, setUrl] = useState('');
  const [depth, setDepth] = useState(2);
  const [usePlaywright, setUsePlaywright] = useState(true);
  const [logs, setLogs] = useState([]);

  const runCrawl = async () => {
    const res = await fetch('/crawl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, depth, usePlaywright })
    });
    const data = await res.json();
    setLogs(data.logs || []);
  };

  return (
    <div className="bg-gray-800 p-4 rounded shadow mt-4">
      <h2 className="text-lg font-bold mb-2">🕸️ Crawler Control Panel</h2>
      <input
        className="p-2 rounded w-full mb-2 bg-gray-700"
        placeholder="Enter URL to crawl"
        value={url}
        onChange={e => setUrl(e.target.value)}
      />
      <div className="flex items-center justify-between mb-2">
        <label>Depth:</label>
        <select value={depth} onChange={e => setDepth(parseInt(e.target.value))} className="bg-gray-700 p-2 rounded">
          {[1, 2, 3].map(d => <option key={d}>{d}</option>)}
        </select>
        <label>Playwright:</label>
        <input type="checkbox" checked={usePlaywright} onChange={() => setUsePlaywright(!usePlaywright)} />
      </div>
      <button onClick={runCrawl} className="p-2 bg-blue-600 rounded text-white w-full">Start Crawl</button>
      <div className="mt-4 text-sm bg-black p-2 rounded h-40 overflow-y-scroll">
        {logs.map((log, i) => <div key={i}>{log}</div>)}
      </div>
    </div>
  );
}
