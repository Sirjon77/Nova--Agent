
from dataclasses import dataclass
from statistics import mean, stdev
from typing import List, Union

@dataclass
class ChannelMetrics:
    channel_id: str
    rpm: float
    avg_watch_minutes: float
    ctr: float
    subs_gained: int
    rpm_history: List[float]

@dataclass
class ScoredChannel:
    channel_id: str
    score: float
    flag: Union[str, None]

class NicheManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.w_rpm   = cfg['weights']['rpm']
        self.w_watch = cfg['weights']['watch']
        self.w_ctr   = cfg['weights']['ctr']
        self.w_subs  = cfg['weights']['subs']
        self.consistency_bonus = cfg.get('consistency_bonus', 5)

    def _z(self, x: float, population: List[float]) -> float:
        if len(population) < 2:
            return 0.0
        return (x - mean(population)) / (stdev(population) or 1)

    def score_channels(self, sample: List[ChannelMetrics]) -> List[ScoredChannel]:
        rpms  = [c.rpm for c in sample]
        watch = [c.avg_watch_minutes for c in sample]
        ctrs  = [c.ctr for c in sample]
        subs  = [c.subs_gained for c in sample]
        scored = []
        for ch in sample:
            s = (
                self.w_rpm   * self._z(ch.rpm, rpms) +
                self.w_watch * self._z(ch.avg_watch_minutes, watch) +
                self.w_ctr   * self._z(ch.ctr, ctrs) +
                self.w_subs  * self._z(ch.subs_gained, subs)
            )
            if len(ch.rpm_history) >= 7 and all(r > 0 for r in ch.rpm_history[-7:]):
                s += self.consistency_bonus
            flag = None
            if s < self.cfg['thresholds']['retire']:
                flag = 'retire'
            elif s < self.cfg['thresholds']['watch']:
                flag = 'watch'
            elif s > self.cfg['thresholds']['promote']:
                flag = 'promote'
            scored.append(ScoredChannel(ch.channel_id, round(s,2), flag))
        return scored
