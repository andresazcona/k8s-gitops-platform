// Covers the paths that do not need MongoDB: password hashing, auth and validation.
const { test, before, after } = require('node:test');
const assert = require('node:assert');

process.env.JWT_SECRET = 'test-secret';
const { app, hashPassword, verifyPassword } = require('../src/app');
let server, base;

before(() => {
  server = app.listen(0);
  base = `http://127.0.0.1:${server.address().port}`;
});

after(() => server.close());

test('hashes are salted and verifiable', async () => {
  const a = await hashPassword('s3cret');
  assert.notStrictEqual(a, await hashPassword('s3cret'));
  assert.ok(await verifyPassword('s3cret', a));
  assert.ok(!(await verifyPassword('wrong', a)));
});

test('register validates input', async () => {
  const res = await fetch(`${base}/api/users/register`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: '{"email":"a@b.c"}',
  });
  assert.strictEqual(res.status, 400);
});

test('profile requires a token', async () => {
  assert.strictEqual((await fetch(`${base}/api/users/profile`)).status, 401);
});
