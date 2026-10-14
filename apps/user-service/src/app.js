const crypto = require('node:crypto');
const { promisify } = require('node:util');
const express = require('express');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');

const scrypt = promisify(crypto.scrypt);

const User = mongoose.model('User', new mongoose.Schema({
  email: { type: String, required: true, unique: true, lowercase: true, trim: true },
  password: { type: String, required: true },
  name: { type: String, trim: true },
}, { timestamps: true }));

async function hashPassword(password) {
  const salt = crypto.randomBytes(16);
  const key = await scrypt(password, salt, 64);
  return `${salt.toString('hex')}:${key.toString('hex')}`;
}

async function verifyPassword(password, stored) {
  const [salt, key] = stored.split(':');
  const candidate = await scrypt(password, Buffer.from(salt, 'hex'), 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(key, 'hex'));
}

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

app.post('/api/users/register', async (req, res) => {
  const { email, password, name } = req.body ?? {};
  if (!email || !password) return res.status(400).json({ message: 'email and password are required' });
  try {
    const user = await User.create({ email, password: await hashPassword(password), name });
    res.status(201).json({ id: user.id, email: user.email, name: user.name });
  } catch (err) {
    if (err.code === 11000) return res.status(409).json({ message: 'email already registered' });
    throw err;
  }
});

app.post('/api/users/login', async (req, res) => {
  const { email, password } = req.body ?? {};
  if (!email || !password) return res.status(400).json({ message: 'email and password are required' });
  const user = await User.findOne({ email: String(email).toLowerCase() });
  if (!user || !(await verifyPassword(password, user.password))) {
    return res.status(401).json({ message: 'invalid credentials' });
  }
  const token = jwt.sign({ sub: user.id, email: user.email }, process.env.JWT_SECRET, { expiresIn: '1h' });
  res.json({ token });
});

app.get('/api/users/profile', requireAuth, async (req, res) => {
  const user = await User.findById(req.user.sub).select('-password');
  if (!user) return res.status(404).json({ message: 'user not found' });
  res.json(user);
});

// Express 5 forwards rejected promises here.
app.use((err, req, res, next) => {
  const status = ['ValidationError', 'CastError'].includes(err.name) ? 400 : 500;
  if (status === 500) console.error(err);
  res.status(status).json({ message: status === 500 ? 'internal error' : err.message });
});

module.exports = { app, hashPassword, verifyPassword };
