# syntax=docker/dockerfile:1
# Shared image for every service: docker build -f apps/Dockerfile apps/<service>

FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund

FROM node:24-alpine
ENV NODE_ENV=production
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY src ./src
# uid 1000 ("node") ships with the base image; the chart enforces runAsNonRoot.
USER 1000:1000
EXPOSE 3000 9464
# OpenTelemetry auto-instrumentation is loaded before the app; it is configured purely via OTEL_* env.
CMD ["node", "--require", "@opentelemetry/auto-instrumentations-node/register", "src/server.js"]
