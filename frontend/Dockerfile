# CodeLens AI — Frontend Dockerfile
FROM node:20-slim AS base

WORKDIR /app

# Install dependencies
COPY --chmod=444 package.json package-lock.json ./
RUN npm ci

# Copy only build-required files — avoids pulling in .env*, logs, or other
# sensitive files that are not excluded by .dockerignore.
COPY --chmod=444 src/ ./src/
COPY --chmod=444 next.config.ts ./
COPY --chmod=444 tsconfig.json ./
COPY --chmod=444 postcss.config.mjs ./
COPY --chmod=444 components.json ./

# ── Development stage (used by docker-compose dev) ────────────────────────────
FROM base AS dev
ENV NODE_ENV=development
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
USER nextjs
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ── Production build ──────────────────────────────────────────────────────────
FROM base AS builder
RUN npm run build

# ── Production runner ─────────────────────────────────────────────────────────
FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Directories need execute bit to be traversable; files need only read.
# No write bit anywhere — standalone output is immutable at runtime.
RUN find /app -type d -exec chmod 555 {} + \
 && find /app -type f -exec chmod 444 {} +

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
