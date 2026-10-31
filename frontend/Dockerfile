# Stage 1: Build production static bundle
FROM node:22-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./

# Install dependencies using clean install
RUN npm ci

# Copy frontend source files
COPY index.html tsconfig*.json vite.config.ts eslint.config.js ./
COPY public ./public
COPY src ./src

# Compile TypeScript and bundle with Vite
RUN npm run build

# Stage 2: Serve static bundle with hardened Nginx
FROM nginx:1.27-alpine AS runner

# Remove default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Health check probe against Nginx server
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
