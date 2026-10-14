const mongoose = require('mongoose');
const { app } = require('./app');

const PORT = process.env.PORT || 3000;

mongoose.connect(process.env.MONGODB_URI).catch((err) => {
  // Crash and let Kubernetes restart us; readiness stays false meanwhile.
  console.error('mongodb connection failed:', err.message);
  process.exit(1);
});

const server = app.listen(PORT, () => console.log(`user-service listening on ${PORT}`));

process.on('SIGTERM', () => server.close(() => mongoose.disconnect().then(() => process.exit(0))));
