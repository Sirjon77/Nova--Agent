"""Watch tool changelogs for new versions (stub implementation)."""
import datetime
import httpx
import logging
from typing import Dict, List

log = logging.getLogger("ChangelogWatcher")

class ChangelogWatcher:
    def __init__(self, cfg: Dict):
        self.cfg = cfg

    async def fetch_version(self, url: str) -> str:
        """Fetch latest version string from a JSON endpoint {"version": "1.2.3"}."""
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(url)
            if r.status_code != 200:
                raise RuntimeError(f"Failed to fetch changelog: {url}")
            return r.json().get('version', '0.0.0')

    async def scan(self, tools: List[Dict]) -> List[Dict]:
        out = []
        now = datetime.datetime.utcnow().isoformat(timespec='seconds')
        for t in tools:
            try:
                latest = await self.fetch_version(t['changelog_url'])
                if latest != t.get('current_version'):
                    out.append({'tool': t['name'], 'new_version': latest, 'seen_at': now})
            except Exception as e:
                log.warning("Changelog check failed for %s: %s", t['name'], e)
        return out
