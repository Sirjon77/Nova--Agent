
import React, { useEffect, useState } from 'react';

export function MemoryViewer() {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch('/memory_crawled_summaries.json')
      .then(res => res.json())
      .then(data => {setSummaries(data||[]); setLoading(false);})
      .catch((err) => {console.error(err); setError(true); setLoading(false);});
  }, []);

  
  if (loading) return <p className="text-sm text-gray-400">Loading summaries...</p>;
  if (error) return <p className="text-sm text-red-500">Failed to load summaries.</p>;
return (
    <div className="bg-gray-800 p-4 rounded shadow mt-4">
      <h2 className="text-lg font-bold mb-2">🧠 Crawled Memory Summaries</h2>
      <div className="overflow-y-scroll h-48 bg-black text-sm p-2 rounded">
        {summaries.map((item, i) => (
          <div key={item.url || i} className="mb-2">
            <div className="text-blue-400 font-mono">{item.url}</div>
            <div>{item.summary}</div>
            <hr className="my-2 border-gray-700"/>
          </div>
        ))}
      </div>
    </div>
  );
}
