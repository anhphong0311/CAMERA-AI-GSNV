# Frontend Dockerfile — build Vite static + serve bằng Nginx

# --- Stage 1: Build ---
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8080/api/v1
ARG VITE_WS_URL=ws://localhost:8080/api/v1/ws
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_URL=$VITE_WS_URL
RUN npm run build

# --- Stage 2: Serve ---
FROM nginx:alpine AS runner
COPY docker/nginx/frontend.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
