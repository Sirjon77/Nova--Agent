/* Minimal example to ensure a stable session ID via localStorage */
(function () {
  const ENDPOINT = "/api/chat";
  let sessionId = localStorage.getItem("nova_sid");
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem("nova_sid", sessionId);
  }

  async function sendMessage(message) {
    const res = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message })
    });
    if (!res.ok) throw new Error("Chat failed");
    const data = await res.json();
    sessionId = data.session_id; // in case backend generates it
    return data.response;
  }

  window.NovaChatWidget = { sendMessage };
})();
