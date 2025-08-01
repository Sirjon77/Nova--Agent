
import { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

export default function FunnelAnalytics() {
  const [data, setData] = useState([]);
  useEffect(() => {
    fetch('/prompt_funnel_metrics.json')
      .then(res => res.json())
      .then(setData)
  }, []);
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-2">Prompt Funnel & Evolution Metrics</h2>
      <BarChart width={500} height={300} data={data}>
        <XAxis dataKey="prompt_id" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="rpm" fill="#82ca9d" />
      </BarChart>
    </div>
  );
}
