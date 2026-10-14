const express = require('express');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');

const Order = mongoose.model('Order', new mongoose.Schema({
  userId: { type: String, required: true, index: true },
  items: [{
    productId: { type: String, required: true },
    quantity: { type: Number, required: true, min: 1 },
    unitPrice: { type: Number, required: true },
  }],
  total: { type: Number, required: true },
  status: { type: String, default: 'created' },
}, { timestamps: true }));

function requireAuth(req, res, next) {
  const [scheme, token] = (req.headers.authorization || '').split(' ');
  try {
    if (scheme !== 'Bearer') throw new Error('missing bearer token');
    req.user = jwt.verify(token, process.env.JWT_SECRET, { algorithms: ['HS256'] });
    next();
  } catch {
    res.status(401).json({ message: 'invalid or missing token' });
  }
}

// Synchronous call to product-service: prices come from the catalog, never from the client.
async function fetchProduct(id) {
  const res = await fetch(`${process.env.PRODUCT_SERVICE_URL}/api/products/${encodeURIComponent(id)}`,
    { signal: AbortSignal.timeout(2000) });
  if (res.status === 404 || res.status === 400) return null;
  if (!res.ok) throw new Error(`product-service responded ${res.status}`);
  return res.json();
}

const app = express();
app.use(express.json());

app.get('/healthz', (req, res) => res.send('ok'));
app.get('/readyz', (req, res) => res.sendStatus(mongoose.connection.readyState === 1 ? 200 : 503));

app.use('/api/orders', requireAuth);

app.post('/api/orders', async (req, res) => {
  const items = req.body?.items;
  if (!Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ message: 'items must be a non-empty array' });
  }
  let products;
  try {
    products = await Promise.all(items.map((i) => fetchProduct(i.productId)));
  } catch (err) {
    console.error('product lookup failed:', err.message);
    return res.status(503).json({ message: 'product catalog unavailable' });
  }
  const missing = items.filter((_, n) => !products[n]).map((i) => i.productId);
  if (missing.length) return res.status(400).json({ message: 'unknown products', missing });

  const lines = items.map((i, n) => ({ productId: i.productId, quantity: i.quantity, unitPrice: products[n].price }));
  const total = lines.reduce((sum, l) => sum + l.unitPrice * l.quantity, 0);
  res.status(201).json(await Order.create({ userId: req.user.sub, items: lines, total }));
});

app.get('/api/orders', async (req, res) => {
  res.json(await Order.find({ userId: req.user.sub }).sort({ createdAt: -1 }).limit(50));
});

app.get('/api/orders/:id', async (req, res) => {
  const order = await Order.findOne({ _id: req.params.id, userId: req.user.sub });
  if (!order) return res.status(404).json({ message: 'order not found' });
  res.json(order);
});

// Express 5 forwards rejected promises here.
app.use((err, req, res, next) => {
  const status = ['ValidationError', 'CastError'].includes(err.name) ? 400 : 500;
  if (status === 500) console.error(err);
  res.status(status).json({ message: status === 500 ? 'internal error' : err.message });
});

module.exports = { app };
