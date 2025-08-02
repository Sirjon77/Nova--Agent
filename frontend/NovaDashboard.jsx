import React, { useState, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function NovaDashboard() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState({});
  const [rpmData, setRpmData] = useState([]);
  const [memoryData, setMemoryData] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch system status
  const fetchStatus = async () => {
    try {
      const res = await fetch("/status");
      const data = await res.json();
      setStatus(data);
    } catch (error) {
      console.error("Failed to fetch status:", error);
    }
  };

  // Fetch RPM data
  const fetchRpmData = async () => {
    try {
      const res = await fetch("/api/rpm/leaderboard");
      const data = await res.json();
      setRpmData(data.leaderboard || []);
    } catch (error) {
      console.error("Failed to fetch RPM data:", error);
    }
  };

  // Fetch memory data
  const fetchMemoryData = async () => {
    try {
      const res = await fetch("/api/memory/recent");
      const data = await res.json();
      setMemoryData(data.memories || []);
    } catch (error) {
      console.error("Failed to fetch memory data:", error);
    }
  };

  // Fetch logs
  const fetchLogs = async () => {
    try {
      const res = await fetch("/observability/logs");
      const data = await res.json();
      setLogs(data.logs || []);
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    }
  };

  // Rotate avatar
  const rotateAvatar = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/avatar/rotate", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        fetchStatus(); // Refresh status
      }
    } catch (error) {
      console.error("Failed to rotate avatar:", error);
    }
    setLoading(false);
  };

  // Show RPM
  const showRpm = async () => {
    setLoading(true);
    try {
      await fetchRpmData();
    } catch (error) {
      console.error("Failed to show RPM:", error);
    }
    setLoading(false);
  };

  // Enable A/B test
  const enableAbTest = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/ab-test/enable", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        console.log("A/B test enabled");
      }
    } catch (error) {
      console.error("Failed to enable A/B test:", error);
    }
    setLoading(false);
  };

  // View A/B test results
  const viewAbResults = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/ab-test/results");
      const data = await res.json();
      console.log("A/B test results:", data);
    } catch (error) {
      console.error("Failed to fetch A/B test results:", error);
    }
    setLoading(false);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    setLoading(true);
    try {
      const res = await fetch("/interface/chat", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });
      const data = await res.json();
      setMessages([...messages, { user: input, nova: data.reply }]);
      setInput("");
    } catch (error) {
      console.error("Failed to send message:", error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchStatus();
    fetchRpmData();
    fetchLogs();
    
    const interval = setInterval(() => {
      fetchStatus();
      fetchLogs();
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
            <Button 
              className="w-full mb-2" 
              onClick={fetchMemoryData}
              disabled={loading}
            >
              🧠 Memory Viewer
            </Button>
            <Button 
              className="w-full mb-2" 
              onClick={rotateAvatar}
              disabled={loading}
            >
              🔁 Rotate Avatar
            </Button>
            <Button 
              className="w-full mb-2" 
              onClick={showRpm}
              disabled={loading}
            >
              📊 Show RPM
            </Button>
          </CardContent>
        </Card>

        <Card className="bg-gray-800">
          <CardContent>
            <h2 className="font-bold mb-2">Avatar Dashboard</h2>
            <p>Status: <strong>{status.status || 'Loading...'}</strong></p>
            <p>Version: <strong>{status.version || 'N/A'}</strong></p>
            <Button 
              className="mt-2" 
              onClick={rotateAvatar}
              disabled={loading}
            >
              Switch Avatar
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Center Columns: Chat + Log Viewer */}
      <div className="col-span-2 space-y-4">
        <Card className="bg-gray-800">
          <CardContent className="h-[400px] overflow-y-scroll">
            <h2 className="font-bold mb-2">Nova Chat</h2>
            {messages.map((msg, i) => (
              <div key={i} className="mb-2 p-2 bg-gray-700 rounded">
                <div><strong>You:</strong> {msg.user}</div>
                <div><strong>Nova:</strong> {msg.nova}</div>
              </div>
            ))}
          </CardContent>
          <div className="flex p-4 bg-gray-900">
            <input 
              className="flex-1 p-2 rounded bg-gray-700" 
              value={input} 
              onChange={e => setInput(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && sendMessage()}
              placeholder="Type your message..."
              disabled={loading}
            />
            <Button 
              onClick={sendMessage} 
              className="ml-2"
              disabled={loading || !input.trim()}
            >
              {loading ? 'Sending...' : 'Send'}
            </Button>
          </div>
        </Card>

        <Card className="bg-gray-800">
          <CardContent className="h-[200px] overflow-y-scroll">
            <h2 className="font-bold mb-2">System Logs</h2>
            {logs.length > 0 ? (
              logs.slice(-10).map((log, i) => (
                <p key={i} className="text-sm">
                  [{log.timestamp}] {log.message}
                </p>
              ))
            ) : (
              <p className="text-gray-400">No recent logs</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Right Column: RPM Chart + A/B Testing */}
      <div className="space-y-4">
        <Card className="bg-gray-800">
          <CardContent>
            <h2 className="font-bold mb-2">RPM Leaderboard</h2>
            {rpmData.length > 0 ? (
              rpmData.map((item, i) => (
                <div key={i} className="flex justify-between">
                  <span>{item.name}:</span>
                  <span className="font-bold">{item.rpm}</span>
                </div>
              ))
            ) : (
              <p className="text-gray-400">No RPM data available</p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gray-800">
          <CardContent>
            <h2 className="font-bold mb-2">A/B Test Panel</h2>
            <Button 
              className="w-full mb-2" 
              onClick={enableAbTest}
              disabled={loading}
            >
              Enable Test
            </Button>
            <Button 
              className="w-full" 
              onClick={viewAbResults}
              disabled={loading}
            >
              View Results
            </Button>
          </CardContent>
        </Card>

        <Card className="bg-gray-800">
          <CardContent>
            <h2 className="font-bold mb-2">Memory Viewer</h2>
            {memoryData.length > 0 ? (
              memoryData.slice(-5).map((memory, i) => (
                <div key={i} className="mb-2 p-2 bg-gray-700 rounded text-sm">
                  <div><strong>{memory.key}:</strong></div>
                  <div className="text-gray-300">{memory.content.substring(0, 100)}...</div>
                </div>
              ))
            ) : (
              <p className="text-gray-400">No recent memories</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}