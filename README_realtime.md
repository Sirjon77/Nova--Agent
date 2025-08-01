## Real‑time & Design‑System Enhancements (v6.3‑realtime)

**Added**
1. **WebSocket chat** (`/ws/chat`) with React hook `useChatSocket`.
2. **Server‑Sent Events** stream for crawl logs (`/sse/logs`).
3. Tailwind config + shadcn‑style design‑system deps (`@radix-ui/react-slot`, etc.).
4. UI components (`Card`, `Button`) now powered by CVA utilities.

### Running locally
```bash
# backend
python -m uvicorn main:app --reload
# frontend
cd webapp && npm install && npm run dev
```