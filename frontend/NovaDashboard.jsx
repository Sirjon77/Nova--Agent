import React, { useState, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function NovaDashboard() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input })
    });
    const data = await res.json();
    setMessages([...messages, { user: input, nova: data.response }]);
    setInput("");
  };

  useEffect(() => {
    const interval = setInterval(() => {
      fetch("/status").then(res => res.json()).then(console.log);
    }, 30000); // 30s auto-refresh
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-900 text-white min-h-screen">
      {/* Left Column: Quick Commands + Avatar Dashboard */}
      <div className="space-y-4">
        <Card className="bg-gray-800">
          <CardContent>
            <h2 className="font-bold mb-2">Quick Commands</h2>
            <Button className="w-full mb-2">🧠 Memory Viewer</Button>
            <Button className="w-full mb-2">🔁 Rotate Avatar</Button>
            <Button className="w-full mb-2">📊 Show RPM</Button>
          </CardContent>
        </Card>

        <Card className="bg-gray-800">
          <CardContent>
            <h2 className="font-bold mb-2">Avatar Dashboard</h2>
            <p>Current: <strong>Marketing.AI</strong></p>
            <Button className="mt-2">Switch Avatar</Button>
          </CardContent>
        </Card>
      </div>

      {/* Center Columns: Chat + Log Viewer */}
      <div className="col-span-2 space-y-4">
        <Card className="bg-gray-800">
          <CardContent className="h-[400px] overflow-y-scroll">
            <h2 className="font-bold mb-2">Nova Chat</h2>
            {messages.map((msg, i) => (
              <div key={i} className="mb-2">
                <div><strong>You:</strong> {msg.user}</div>
                <div><strong>Nova:</strong> {msg.nova}</div>
              </div>
            ))}
          </CardContent>
          <div className="flex p-4 bg-gray-900">
            <input className="flex-1 p-2 rounded bg-gray-700" value={input} onChange={e => setInput(e.target.value)} />
            <Button onClick={sendMessage} className="ml-2">Send</Button>
          </div>
        </Card>

        <Card className="bg-gray-800">
          <CardContent className="h-[200px] overflow-y-scroll">
            <h2 className="font-bold mb-2">Loop Logs</h2>
            <p>[5AM] Heartbeat active. RPM: 42.1</p>
            <p>[10AM] Fallback agent switched.</p>
            <p>[6PM] A/B test rotation complete.</p>
          </CardContent>
        </Card>
      </div>

      {/* Right Column: RPM Chart + A/B Testing */}
      <div className="space-y-4">
        <Card className="bg-gray-800">
          <CardContent>
            <h2 className="font-bold mb-2">RPM Leaderboard</h2>
            <p>Marketing.AI: 42.1</p>
            <p>WritingBot: 37.9</p>
            <p>SEO_Sniper: 35.4</p>
          </CardContent>
        </Card>

        <Card className="bg-gray-800">
          <CardContent>
            <h2 className="font-bold mb-2">A/B Test Panel</h2>
            <Button className="w-full mb-2">Enable Test</Button>
            <Button className="w-full">View Results</Button>
          </CardContent>
        </Card>

        <Card className="bg-gray-800">
          <CardContent>
            <h2 className="font-bold mb-2">Funnel Console</h2>
            <Button className="w-full">Link Funnel</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}