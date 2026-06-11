# ── Stage: Node.js + Python base ─────────────────────────────────────────────
FROM python:3.11-slim

# Install Node.js (for mongodb-mcp-server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    openssl \
    nodejs \
    npm \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# Install MongoDB MCP server globally
RUN npm install -g mongodb-mcp-server

# ── Python dependencies ───────────────────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy app source ───────────────────────────────────────────────────────────
COPY . .

# ── Streamlit config ──────────────────────────────────────────────────────────
EXPOSE 8080
ENV PORT=8080

CMD ["python", "-m", "streamlit", "run", "app.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
