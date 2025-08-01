import React, { useEffect, useState } from 'react';

export default function ModelControlPanel() {
  const [tiers, setTiers] = useState({});
  const [error, setError] = useState(null);

  const fetchTiers = async () => {
    try {
      const res = await fetch("/api/current-model-tiers");
      const data = await res.json();
      setTiers(data);
    } catch (e) {
      setError("Unable to load model tiers");
    }
  };

  useEffect(() => { fetchTiers(); }, []);

  
  if (loading) return <p className="text-sm text-gray-400">Loading model tiers...</p>;
  if (error) return <p className="text-sm text-red-500">Failed to load model tiers.</p>;
return (
    <div className="p-4 text-white">
      <h2 className="text-lg font-bold mb-2">Model Routing Settings</h2>
      {error && <div className="text-red-400">{error}</div>}
      <pre className="bg-gray-800 p-3 rounded-lg overflow-x-auto text-sm">
        {JSON.stringify(tiers, null, 2)}
      </pre>
      <p className="text-xs mt-2 opacity-75">Edit config/model_tiers.json to change routing.</p>
    </div>
  );
}