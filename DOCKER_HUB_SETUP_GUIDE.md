# 🚀 GreenOps Refactor — Docker Hub Setup Guide

**For users pulling from Docker Hub to run GreenOps with Home Assistant**

---

## ⚡ Quick Start (Choose Your Setup)

### **Setup 1: Windows/Mac with Docker Desktop + Local Home Assistant**

```powershell
docker run -d `
  --name greenops `
  -p 5000:5000 `
  -e HOME_ASSISTANT_URL="http://host.docker.internal:8123" `
  -e HOME_ASSISTANT_TOKEN="your_token_here" `
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434" `
  -e SECRET_KEY="random-secret-key" `
  himanshujoshi03/greenops-refactor:latest
```

**Key points:**
- Use `host.docker.internal` (not `localhost`)
- Your Home Assistant must be running on your machine (Docker Desktop or native)
- Get your token from Home Assistant → Settings → Developer Tools → Personal access tokens

---

### **Setup 2: Linux Server (Not Docker Desktop)**

```bash
docker run -d \
  --name greenops \
  -p 5000:5000 \
  -e HOME_ASSISTANT_URL="http://192.168.1.100:8123" \
  -e HOME_ASSISTANT_TOKEN="your_token_here" \
  -e OLLAMA_BASE_URL="http://192.168.1.100:11434" \
  -e SECRET_KEY="random-secret-key" \
  himanshujoshi03/greenops-refactor:latest
```

**Key points:**
- Replace `192.168.1.100` with your Home Assistant server IP
- Or use hostname: `http://homeassistant.local:8123`
- Make sure Home Assistant is accessible from the Docker container

---

### **Setup 3: Docker Compose (Recommended for Full Setup)**

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  greenops-app:
    image: himanshujoshi03/greenops-refactor:latest
    container_name: greenops-app
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      HOME_ASSISTANT_URL: http://host.docker.internal:8123
      HOME_ASSISTANT_TOKEN: your_token_here
      OLLAMA_BASE_URL: http://host.docker.internal:11434
      SECRET_KEY: random-secret-key
    networks:
      - greenops-network

  ollama:
    image: ollama/ollama:latest
    container_name: greenops-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    networks:
      - greenops-network
    volumes:
      - ollama-models:/root/.ollama

networks:
  greenops-network:
    driver: bridge

volumes:
  ollama-models:
```

Run:
```bash
docker-compose up -d
```

---

## 🔑 Getting Your Home Assistant Token

1. **Open Home Assistant**: Go to your instance (e.g., http://localhost:8123 or http://homeassistant.local:8123)
2. Click **Profile icon** (bottom left corner)
3. Scroll down to **"Long-Lived Access Tokens"**
4. Click **"Create token"**
5. Name it: `GreenOps`
6. **Copy the full token** (shown only once!)
7. Paste it in the command as `HOME_ASSISTANT_TOKEN=your_token_here`

---

## 🌐 Choosing Your Home Assistant URL

### **Docker Desktop (Windows/Mac)**
```
http://host.docker.internal:8123
```
Special Docker Desktop feature to access your host machine.

### **Linux / Standalone Docker**
Option A - Using local IP:
```
http://192.168.1.X:8123
# Find your IP: hostname -I (Linux) or ipconfig (Windows)
```

Option B - Using hostname:
```
http://homeassistant.local:8123
```

Option C - Using container hostname (if on same Docker network):
```
http://homeassistant:8123
```

---

## ✅ Verify It's Working

Check the logs:
```bash
docker logs greenops -f
```

You should see:
```
✅ Home Assistant: OK
Grid carbon HTTP API: OK
```

If you see:
```
⚠️ No grid carbon source available — using Maharashtra fallback
```

Then Home Assistant connection failed. Check:
1. Is Home Assistant running?
2. Is the URL correct?
3. Is the token valid and not expired?

---

## 🛑 Troubleshooting

### "Connection refused"
- **Windows/Mac**: Make sure Docker Desktop is running
- **Linux**: Make sure Home Assistant is accessible at the URL you provided
- Test: `curl http://YOUR_HOME_ASSISTANT_URL:8123`

### "Unauthorized (401)"
- Your token is invalid or expired
- Get a fresh token from Home Assistant settings
- Make sure it's a "Long-Lived Access Token" (not a session token)

### "Host not found"
- Hostname/IP is wrong
- For Docker Desktop use: `host.docker.internal`
- For Linux use: actual IP address or hostname

### "Ollama not responding"
- Make sure Ollama is running (or start it separately)
- For Docker Desktop: `ollama serve` in a terminal
- For Linux: check if ollama process is running

---

## 🐳 Using with Home Assistant Container

If Home Assistant is also in Docker:

```bash
docker run -d \
  --name greenops \
  -p 5000:5000 \
  --network homeassistant \
  -e HOME_ASSISTANT_URL="http://homeassistant:8123" \
  -e HOME_ASSISTANT_TOKEN="your_token_here" \
  -e SECRET_KEY="random-secret-key" \
  himanshujoshi03/greenops-refactor:latest
```

**Key**: Use `--network homeassistant` and `http://homeassistant:8123` (service name instead of IP)

---

## 📋 Environment Variables Reference

| Variable | Required | Default | Example |
|----------|----------|---------|---------|
| `HOME_ASSISTANT_URL` | ✅ | None | `http://localhost:8123` |
| `HOME_ASSISTANT_TOKEN` | ✅ | None | `eyJhbGc...` |
| `OLLAMA_BASE_URL` | ❌ | `http://localhost:11434` | `http://ollama:11434` |
| `SECRET_KEY` | ✅ | None | `random-key-here` |
| `HOME_ASSISTANT_CO2_SENSOR` | ❌ | Auto-detect | `sensor.co2_intensity` |
| `HOME_ASSISTANT_FOSSIL_SENSOR` | ❌ | Auto-detect | `sensor.fossil_fuel` |
| `ELECTRICITY_MAPS_API_KEY` | ❌ | None | For fallback only |
| `ELECTRICITY_MAPS_ZONE` | ❌ | `IN-WE` | Grid zone |

---

## 🚀 Example: Full Setup on Linux

```bash
# 1. Create .env file
cat > .env << EOF
HOME_ASSISTANT_URL=http://192.168.1.50:8123
HOME_ASSISTANT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
OLLAMA_BASE_URL=http://localhost:11434
EOF

# 2. Start Ollama (if not running)
ollama serve &

# 3. Start GreenOps from Docker Hub
docker run -d \
  --name greenops \
  -p 5000:5000 \
  --env-file .env \
  himanshujoshi03/greenops-refactor:latest

# 4. Check status
docker logs greenops -f
```

---

## 💡 Pro Tips

1. **Generate SECRET_KEY safely**:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Save your token securely** (not in git):
   ```bash
   # Create .env locally (not committed)
   cat > .env << EOF
   HOME_ASSISTANT_TOKEN=your_secret_token
   SECRET_KEY=your_secret_key
   EOF
   
   # Use with docker-compose
   docker-compose up -d
   ```

3. **Test Home Assistant connection**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://YOUR_HOME_ASSISTANT_URL:8123/api/
   ```

4. **View energy metrics** from Home Assistant directly:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://YOUR_HOME_ASSISTANT_URL:8123/api/states | grep -i carbon
   ```

---

## 📞 Still Having Issues?

**Check logs in detail**:
```bash
docker logs greenops -f | grep -i "home.assistant\|carbon\|error"
```

**Common issues**:
- ❌ "No grid carbon source available" → Home Assistant not connected
- ❌ "Unauthorized (401)" → Bad token
- ❌ "Connection refused" → Wrong URL or service not running
- ✅ "Home Assistant: OK" → Everything working!

---

**Your GreenOps service is now ready to analyze code with real carbon data! 🌱**
