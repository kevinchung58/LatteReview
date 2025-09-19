# Stage 1: Build the React app
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
# The VITE_API_BASE_URL will be crucial here if it's set at build time.
# If it's a runtime config via Nginx, this build arg might not be needed in this exact way.
# For now, assuming it might be used by the build process or baked in if not proxied.
ARG VITE_API_BASE_URL=/api # Default if not provided, or can be set during docker build
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# Stage 2: Serve the static files with Nginx
FROM nginx:alpine

# Copy the Nginx configuration file
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built static assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
