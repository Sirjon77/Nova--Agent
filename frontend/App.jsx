import React, { useState } from 'react';
import { useChatSocket } from './hooks/useChatSocket';
import { DataProvider } from './DataContext';
import ModelControlPanel from './ModelControlPanel';

function ChatPanel() {
  const [messages, setMessages] = useState([]);

  const { send } = useChatSocket((data)=> setMessages(prev=>[...prev, data]));
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;
    send({ message: input });
    /* fallback HTTP call */
    const res = await fetch("/chat", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input })
    });
    const data = await res.json();
    setMessages([...messages, { user: input, nova: data.response }]);
    setInput("");
  };

  return (
  <DataProvider>
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-scroll space-y-2 p-2">
        {messages.map((m,i)=>(
          <div key={i} className="bg-gray-800 p-2 rounded-md">
            <p className="text-blue-400">You:</p>
            <p>{m.user}</p>
            <p className="text-green-400 mt-2">Nova:</p>
            <p>{m.nova}</p>
          </div>
        ))}
      </div>
      <div className="flex p-2 bg-gray-800">
        <input className="flex-1 bg-gray-700 p-2 rounded-l-md"
               value={input} onChange={e=>setInput(e.target.value)}
               placeholder="Ask Nova..." />
        <button onClick={sendMessage} className="bg-blue-600 hover:bg-blue-500 transition-colors duration-200 px-4 rounded-r-md">Send</button>
      </div>
    </div>
  </DataProvider>
);
}

export default function App() {
  const [tab, setTab] = useState("chat");

  const TabButton = ({id, label}) => (
    <button onClick={()=>setTab(id)}
            className={`px-3 py-2 ${tab===id?'bg-blue-600':'bg-gray-800'} rounded-md text-sm font-medium`}>
      {label}
    </button>
  );

  return (
  <DataProvider>
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      <header className="p-3 flex space-x-2">
        <TabButton id="chat" label="Chat" />
        <TabButton id="models" label="Model Routing" />
      </header>
      <main className="flex-1">
        {tab==="chat" && <ChatPanel />}
        {tab==="models" && <ModelControlPanel />}
      </main>
    </div>
  </DataProvider>
);
}