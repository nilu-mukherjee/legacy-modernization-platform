# CodeLens AI — Frontend Dockerfile
FROM node:20-slim AS base

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --production=false

# Copy source code
COPY . .

# Build production bundle
RUN npm run build

# Production runner
FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production

# Copy built application
COPY --from=base /app/.next/standalone ./
COPY --from=base /app/.next/static ./.next/static
COPY --from=base /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
