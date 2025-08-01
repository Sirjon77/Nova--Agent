import { useState, useEffect, useRef } from 'react';

export default function App() {
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState('');
  const wsRef = useRef(null);

  useEffect(() => {
    const token = import.meta.env.VITE_WS_SECRET;
    wsRef.current = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
    wsRef.current.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.type === 'final') {
        setHistory((h) => [...h, { role: 'nova', text: msg.data }]);
      }
    };
    return () => wsRef.current.close();
  }, []);

  const send = (e) => {
    e.preventDefault();
    if (!input) return;
    wsRef.current.send(input);
    setHistory((h) => [...h, { role: 'user', text: input }]);
    setInput('');
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-200 p-4">
      <div className="flex-1 overflow-y-auto space-y-2">
        {history.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-blue-300' : 'text-green-300'}>
            {m.text}
          </div>
        ))}
      </div>
      <form onSubmit={send} className="flex gap-2 mt-2">
        <input
          aria-label="Chat message input"
          className="flex-1 p-2 rounded bg-gray-800"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Nova…"
        />
        <button type="submit" aria-label="Send message" className="px-4 py-2 bg-blue-600 rounded">
          Send
        </button>
      </form>
    </div>
  );
}
