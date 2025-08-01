
import React, { useEffect, useState } from 'react';

export function LogsPanel() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const evt = new EventSource('/sse/logs');
    evt.onmessage = (e)=>{
      try{
        const parsed = JSON.parse(e.data);
        setLogs(prev=>[...prev, parsed.line]);
      }catch(err){}
    };
    evt.onerror = ()=>evt.close();

    // legacy fetch fallback
    fetch('/startup_crawl_log.json')
      .then(res => res.json())
      .then(data => {setLogs(data||[]); setLoading(false);})
      .catch((err) => {console.error(err); setError(true); setLoading(false);});
    return () => evt.close();
  }, []);

  
  if (loading) return <p className="text-sm text-gray-400">Loading logs...</p>;
  if (error) return <p className="text-sm text-red-500">Failed to load logs.</p>;
return (
    <div className="bg-gray-800 p-4 rounded shadow mt-4">
      <h2 className="text-lg font-bold mb-2">📜 Crawl Logs</h2>
      <div className="overflow-y-scroll h-40 bg-black text-sm p-2 rounded">
        {logs.map((line, i) => <div key={line.slice(0,20)+i}>{line}</div>)}
      </div>
    </div>
  );
}
