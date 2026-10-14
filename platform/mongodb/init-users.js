// Runs once, when the data volume is empty (docker-entrypoint-initdb.d, as root).
// Database-per-service: each service gets its own database and a readWrite-only user.
const services = { 'user-service': 'users', 'product-service': 'products', 'order-service': 'orders' };

for (const [user, dbName] of Object.entries(services)) {
  const pwd = process.env[`${user.toUpperCase().replace('-', '_')}_PASSWORD`];
  db.getSiblingDB(dbName).createUser({ user, pwd, roles: [{ role: 'readWrite', db: dbName }] });
}
