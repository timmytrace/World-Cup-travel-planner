# ── Stage: Node.js + Python base ─────────────────────────────────────────────
FROM python:3.11-slim

# Install Node.js (for mongodb-mcp-server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

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
