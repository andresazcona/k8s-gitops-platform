// Covers the paths that do not need MongoDB: write auth and readiness.
const { test, before, after } = require('node:test');
const assert = require('node:assert');

process.env.JWT_SECRET = 'test-secret';
const { app } = require('../src/app');
let server, base;

before(() => {
  server = app.listen(0);
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => server.close());

test('writes require a token', async () => {
  for (const [method, path] of [['POST', ''], ['PUT', '/1'], ['DELETE', '/1']]) {
    assert.strictEqual((await fetch(`${base}/api/products${path}`, { method })).status, 401);
  }
});

test('is not ready without a database connection', async () => {
  assert.strictEqual((await fetch(`${base}/readyz`)).status, 503);
});
