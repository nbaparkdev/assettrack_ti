# Build stage
FROM golang:alpine AS builder

RUN apk add --no-cache gcc musl-dev

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /server ./cmd/server

# Runtime stage
FROM alpine:3.20

RUN apk add --no-cache ca-certificates tzdata postgresql16-client bash nodejs npm openjdk17-jdk python3
ENV TZ=America/Sao_Paulo

WORKDIR /app
COPY --from=builder /server /app/server

RUN mkdir -p /app/uploads
RUN mkdir -p /workspace

EXPOSE 8080

CMD ["/app/server"]
