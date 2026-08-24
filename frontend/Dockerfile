# Build stage
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
ARG VITE_API_URL=http://localhost:8080/api/v1
ARG VITE_APP_VERSION_CODE=2
ARG VITE_APP_VERSION_NAME=1.2.0
ARG VITE_APP_BUILD_TIMESTAMP=
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_VERSION_CODE=$VITE_APP_VERSION_CODE
ENV VITE_APP_VERSION_NAME=$VITE_APP_VERSION_NAME
ENV VITE_APP_BUILD_TIMESTAMP=$VITE_APP_BUILD_TIMESTAMP
RUN npm run build

# Production stage
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
