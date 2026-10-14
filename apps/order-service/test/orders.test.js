// Covers the paths that do not need MongoDB: auth, validation and the product-service call.
const { test, before, after } = require('node:test');
const assert = require('node:assert');
const http = require('node:http');
const jwt = require('jsonwebtoken');

process.env.JWT_SECRET = 'test-secret';
let catalog, server, base;
const token = jwt.sign({ sub: 'u1' }, 'test-secret');
const post = (body, auth = `Bearer ${token}`) => fetch(`${base}/api/orders`, {
  method: 'POST',
  headers: { authorization: auth, 'content-type': 'application/json' },
  body: JSON.stringify(body),
});

before(async () => {
  // Fake product-service that knows nothing: every lookup is a 404.
  catalog = http.createServer((req, res) => { res.writeHead(404); res.end(); }).listen(0);
  process.env.PRODUCT_SERVICE_URL = `http://127.0.0.1:${catalog.address().port}`;
  const { app } = require('../src/app');
  server = app.listen(0);
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => { catalog.close(); server.close(); });

test('rejects requests without a valid token', async () => {
  assert.strictEqual((await post({ items: [] }, '')).status, 401);
  assert.strictEqual((await post({ items: [] }, 'Bearer forged')).status, 401);
});

test('rejects empty orders', async () => {
  assert.strictEqual((await post({ items: [] })).status, 400);
});

test('rejects products unknown to the catalog', async () => {
  const res = await post({ items: [{ productId: 'p1', quantity: 1 }] });
  assert.strictEqual(res.status, 400);
  assert.deepStrictEqual((await res.json()).missing, ['p1']);
});

test('returns 503 when the catalog is unreachable', async () => {
  process.env.PRODUCT_SERVICE_URL = 'http://127.0.0.1:1';
  const res = await post({ items: [{ productId: 'p1', quantity: 1 }] });
  assert.strictEqual(res.status, 503);
});

test('is not ready without a database connection', async () => {
  assert.strictEqual((await fetch(`${base}/readyz`)).status, 503);
});
