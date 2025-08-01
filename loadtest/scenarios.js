import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: __ENV.LOADTEST_USERS || 50,
  duration: '1m',
};

export default function () {
  ['/', '/chat', '/ws', '/api/modules'].forEach((path) => {
    const res = http.get(`http://localhost:3000${path}`);
    check(res, { 'status was 200': (r) => r.status === 200 });
  });
  sleep(1);
}
