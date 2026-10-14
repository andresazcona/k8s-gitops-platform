// Functional smoke test through the ingress: register -> login -> create product -> order it -> read it back.
// CI runs it against a kind cluster; the thresholds make k6 exit non-zero on any failure.
import http from 'k6/http';
import { check, fail } from 'k6';

const BASE = __ENV.BASE_URL || 'http://localhost';
const json = { headers: { 'Content-Type': 'application/json' } };

export const options = {
  vus: 2,
  iterations: 10,
  thresholds: {
    checks: ['rate==1'],
    http_req_failed: ['rate==0'],
    http_req_duration: ['p(95)<1500'],
  },
};

export default function () {
  const email = `smoke-${__VU}-${__ITER}-${Date.now()}@example.test`;
  const password = 'correct horse battery staple';

  const reg = http.post(`${BASE}/api/users/register`, JSON.stringify({ email, password, name: 'Smoke' }), json);
  if (!check(reg, { 'register 201': (r) => r.status === 201 })) fail('register failed');

  const login = http.post(`${BASE}/api/users/login`, JSON.stringify({ email, password }), json);
  if (!check(login, { 'login 200 with token': (r) => r.status === 200 && !!r.json('token') })) fail('login failed');
  const auth = { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${login.json('token')}` } };

  const product = http.post(`${BASE}/api/products`, JSON.stringify({ name: 'Widget', price: 12.5, description: 'smoke' }), auth);
  if (!check(product, { 'product 201': (r) => r.status === 201 })) fail('product failed');
  const productId = product.json('_id');

  // order-service prices the order by calling product-service: this crosses three services and MongoDB.
  const order = http.post(`${BASE}/api/orders`, JSON.stringify({ items: [{ productId, quantity: 2 }] }), auth);
  check(order, {
    'order 201': (r) => r.status === 201,
    'order priced from catalog': (r) => r.json('total') === 25,
  });

  const orders = http.get(`${BASE}/api/orders`, auth);
  check(orders, { 'order listed': (r) => r.status === 200 && r.json().length >= 1 });

  // A 401 is the expected answer here, so tell k6 not to count it as a failed request.
  const anon = http.get(`${BASE}/api/orders`, { responseCallback: http.expectedStatuses(401) });
  check(anon, { 'orders without token is 401': (r) => r.status === 401 });
}
