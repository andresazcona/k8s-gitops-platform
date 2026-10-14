// HPA demo. Login hashes with scrypt, so every request burns real CPU in user-service and pushes it past
// the HPA target; product reads add a cheap second path. Watch it scale with:
//   kubectl get hpa -n shop -w
// Run: k6 run k6/load.js        (BASE_URL defaults to http://localhost, the kind ingress)
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'http://localhost';
const json = { headers: { 'Content-Type': 'application/json' } };

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // warm up
    { duration: '3m', target: 40 },   // sustained load: HPA should add replicas within ~1-2 minutes
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.02'],      // errors stay under 2% even while pods are being added
    http_req_duration: ['p(95)<3000'],   // generous: latency spikes until the new replicas are ready
  },
};

export function setup() {
  const creds = { email: `load-${Date.now()}@example.test`, password: 'correct horse battery staple' };
  const res = http.post(`${BASE}/api/users/register`, JSON.stringify(creds), json);
  if (res.status !== 201) throw new Error(`register failed: ${res.status}`);
  return creds;
}

export default function (creds) {
  check(http.post(`${BASE}/api/users/login`, JSON.stringify(creds), json), { 'login 200': (r) => r.status === 200 });
  check(http.get(`${BASE}/api/products`), { 'products 200': (r) => r.status === 200 });
  sleep(0.2);
}
