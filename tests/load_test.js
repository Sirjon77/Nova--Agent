import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 25,
  duration: '2m',
};

export default function () {
  let res = http.get('http://localhost:8000/health');
  check(res, { 'status was 200': (r) => r.status === 200 });
  sleep(1);
}
