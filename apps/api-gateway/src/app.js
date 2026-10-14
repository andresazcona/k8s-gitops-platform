const http = require('node:http');
const express = require('express');

// Path prefix -> upstream base URL. Upstreams keep the full path (/api/users/...).
const routes = {
  '/api/users': process.env.USER_SERVICE_URL,
  '/api/products': process.env.PRODUCT_SERVICE_URL,
  '/api/orders': process.env.ORDER_SERVICE_URL,
};

// Hop-by-hop headers must not be forwarded by a proxy (RFC 9110 7.6.1).
const HOP_BY_HOP = ['connection', 'keep-alive', 'proxy-connection', 'upgrade', 'te', 'trailer', 'host'];

function strip(headers) {
  const out = { ...headers };
  for (const h of HOP_BY_HOP) delete out[h];
  return out;
}

function proxyTo(base) {
  return (req, res) => {
    const upstream = http.request(new URL(req.originalUrl, base), {
      method: req.method,
      headers: strip(req.headers),
      timeout: 5000,
    }, (up) => {
      res.writeHead(up.statusCode, strip(up.headers));
      up.pipe(res);
    });
    upstream.on('timeout', () => upstream.destroy(new Error('upstream timeout')));
    upstream.on('error', (err) => {
      console.error(`upstream ${base} failed: ${err.message}`);
      if (res.headersSent) return res.destroy();
      res.status(err.message === 'upstream timeout' ? 504 : 502).json({ message: 'upstream unavailable' });
    });
    req.pipe(upstream);
  };
}

const app = express();

app.get('/healthz', (req, res) => res.send('ok'));
app.get('/readyz', (req, res) => res.send('ok'));

for (const [prefix, base] of Object.entries(routes)) app.use(prefix, proxyTo(base));

app.use((req, res) => res.status(404).json({ message: 'route not found' }));

module.exports = { app };
