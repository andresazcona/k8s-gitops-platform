const { test, before, after } = require('node:test');
const assert = require('node:assert');
const http = require('node:http');

let upstream, gateway, base;

before(async () => {
  // Fake domain service that echoes what it received.
  upstream = http.createServer((req, res) => {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      res.writeHead(201, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ method: req.method, url: req.url, auth: req.headers.authorization, body }));
    });
  }).listen(0);
  const up = `http://127.0.0.1:${upstream.address().port}`;
  process.env.USER_SERVICE_URL = up;
  process.env.PRODUCT_SERVICE_URL = up;
  process.env.ORDER_SERVICE_URL = 'http://127.0.0.1:1'; // nothing listens here
  const { app } = require('../src/app');
  gateway = app.listen(0);
  base = `http://127.0.0.1:${gateway.address().port}`;
});

after(() => { upstream.close(); gateway.close(); });

test('forwards method, full path, query, auth header and body', async () => {
  const res = await fetch(`${base}/api/products/42?x=1`, {
    method: 'PUT',
    headers: { authorization: 'Bearer t', 'content-type': 'application/json' },
    body: JSON.stringify({ price: 3 }),
  });
  assert.strictEqual(res.status, 201);
  assert.deepStrictEqual(await res.json(),
    { method: 'PUT', url: '/api/products/42?x=1', auth: 'Bearer t', body: '{"price":3}' });
});

test('returns 502 when the upstream is down', async () => {
  const res = await fetch(`${base}/api/orders`);
  assert.strictEqual(res.status, 502);
});

test('returns 404 for unknown routes', async () => {
  assert.strictEqual((await fetch(`${base}/nope`)).status, 404);
});
