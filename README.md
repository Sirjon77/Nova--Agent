
# Nova Agent Tier 3+ Deployment

This deployment includes:
- Conversational Web UI (`/frontend`)
- API backend (`interface_handler.py`)
- Async task dispatcher (`nova_dispatcher.py`)
- Updated Render config (`render.yaml`)

## How to Use
1. Deploy both services via Render
2. Visit the web interface at the Render-provided URL
3. Begin sending messages or commands to Nova Agent via chat


---

## 🖥️ Nova Conversational Interface

To run the new live chat interface:

1. Launch the FastAPI server:
```bash
python interface_handler.py
```

2. Open your browser at `http://localhost:7860` or expose the port via Render.

3. The frontend UI (React) is inside `/frontend/` and will be enhanced to support live command, memory logs, avatar and funnel control.



---

## 🧠 Nova GUI Control Dashboard

### How to Launch

1. Start the chat API backend:
```bash
python interface_handler.py
```

2. Visit `http://localhost:7860` to access the Nova command center GUI.

3. Chat interface supports:
- Prompt memory queries
- Resume/pause commands
- Avatar tracking
- RPM leaderboard insights
- Funnel assignments
- Export triggers to Notion/Sheets

4. React frontend lives in `/frontend/`. Future upgrades include dynamic memory logs, leaderboards, and funnel panels.
