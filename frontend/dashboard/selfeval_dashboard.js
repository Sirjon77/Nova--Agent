
import { useEffect, useState } from 'react';
export default function SelfEvalPanel() {
  const [data, setData] = useState({});
  useEffect(() => {
    fetch('/loop_health_report.json').then(res => res.json()).then(setData);
  }, []);
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-2">Nova Self-Eval Dashboard</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
