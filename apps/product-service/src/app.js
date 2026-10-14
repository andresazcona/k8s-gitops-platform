const express = require('express');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');

const Product = mongoose.model('Product', new mongoose.Schema({
  name: { type: String, required: true, trim: true },
  price: { type: Number, required: true, min: 0 },
  description: { type: String, required: true },
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

const app = express();
app.use(express.json());

app.get('/healthz', (req, res) => res.send('ok'));
app.get('/readyz', (req, res) => res.sendStatus(mongoose.connection.readyState === 1 ? 200 : 503));

// Reads are public, writes need a token issued by user-service.
app.get('/api/products', async (req, res) => {
  res.json(await Product.find().sort({ createdAt: -1 }).limit(100));
});

app.get('/api/products/:id', async (req, res) => {
  const product = await Product.findById(req.params.id);
  if (!product) return res.status(404).json({ message: 'product not found' });
  res.json(product);
});

app.post('/api/products', requireAuth, async (req, res) => {
  const { name, price, description } = req.body ?? {};
  res.status(201).json(await Product.create({ name, price, description }));
});

app.put('/api/products/:id', requireAuth, async (req, res) => {
  const { name, price, description } = req.body ?? {};
  const product = await Product.findByIdAndUpdate(req.params.id, { name, price, description },
    { new: true, runValidators: true });
  if (!product) return res.status(404).json({ message: 'product not found' });
  res.json(product);
});

app.delete('/api/products/:id', requireAuth, async (req, res) => {
  await Product.findByIdAndDelete(req.params.id);
  res.sendStatus(204);
});

// Express 5 forwards rejected promises here.
app.use((err, req, res, next) => {
  const status = ['ValidationError', 'CastError'].includes(err.name) ? 400 : 500;
  if (status === 500) console.error(err);
  res.status(status).json({ message: status === 500 ? 'internal error' : err.message });
});

module.exports = { app };
