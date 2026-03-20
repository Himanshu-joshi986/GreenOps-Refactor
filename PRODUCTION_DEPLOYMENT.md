# GreenOps Refactor - Production Configuration

This guide covers production deployment of the GreenOps Flask application.

## Environment Setup

Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
FLASK_DEBUG=0

# Security
SECRET_KEY=your-very-secure-random-key-here
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Server
WORKERS=4
PORT=5000
HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/greenops.log

# Performance
MAX_CONTENT_LENGTH=16777216
PROPAGATE_EXCEPTIONS=True
```

## Generate Secret Key

```python
import secrets
print(secrets.token_hex(32))
```

## Gunicorn Deployment

### Install Gunicorn
```bash
pip install gunicorn
```

### Run with Gunicorn
```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 4 --worker-class sync --timeout 120
```

### Gunicorn Configuration File (gunicorn.conf.py)
```python
import multiprocessing

# Server
bind = "0.0.0.0:5000"
backlog = 2048
timeout = 120
keepalive = 5

# Worker Processes
workers = multiprocessing.cpu_count()
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# SSL (if needed)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
```

Run with config:
```bash
gunicorn -c gunicorn.conf.py app:app
```

## Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000')"

# Run Gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
```

### Build and Run Docker Image
```bash
# Build
docker build -t greenops-refactor:latest .

# Run
docker run -d \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))') \
  --name greenops \
  greenops-refactor:latest

# View logs
docker logs -f greenops

# Stop
docker stop greenops
```

## Nginx Configuration

### Reverse Proxy Setup (nginx.conf)
```nginx
upstream greenops {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    listen 80;
    server_name greenops.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name greenops.example.com;

    # SSL Certificates
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_vary on;
    gzip_min_length 1000;

    # Proxy Settings
    location / {
        proxy_pass http://greenops;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static Files Caching
    location /static/ {
        alias /var/www/greenops/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Systemd Service (Linux)

Create `/etc/systemd/system/greenops.service`:

```ini
[Unit]
Description=GreenOps Refactor Flask Application
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/greenops
Environment="PATH=/var/www/greenops/venv/bin"
ExecStart=/var/www/greenops/venv/bin/gunicorn \
    -c /var/www/greenops/gunicorn.conf.py \
    app:app

# Restart
Restart=always
RestartSec=5s

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable greenops
sudo systemctl start greenops
```

## Monitoring & Logging

### Application Logging
```python
# In app.py
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/greenops.log', 
                                      maxBytes=10240000, 
                                      backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Monitoring Tools
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **ELK Stack**: Centralized logging
- **New Relic**: Performance monitoring
- **Datadog**: Infrastructure monitoring

### Example Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, start_http_server
import time

request_count = Counter('greenops_requests_total', 'Total requests')
request_duration = Histogram('greenops_request_duration_seconds', 'Request latency')

@app.route('/metrics')
def metrics():
    start_http_server(8000)
    return "Metrics running on port 8000"
```

## AWS Deployment

### Using AWS Elastic Beanstalk

1. Install EB CLI:
```bash
pip install awsebcli --upgrade --user
```

2. Initialize:
```bash
eb init -p python-3.11 greenops-refactor
```

3. Create environment:
```bash
eb create production
```

4. Deploy:
```bash
eb deploy
```

### Using AWS AppRunner

1. Push to ECR:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker build -t greenops-refactor .
docker tag greenops-refactor:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/greenops-refactor:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/greenops-refactor:latest
```

2. Create AppRunner service through AWS Console

## Security Checklist

- [ ] Enable HTTPS/SSL
- [ ] Set secure SECRET_KEY
- [ ] Configure CSRF protection
- [ ] Add security headers (HSTS, CSP, X-Frame-Options)
- [ ] Enable rate limiting
- [ ] Setup Web Application Firewall (WAF)
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Backup sensitive data
- [ ] Use environment variables for secrets
- [ ] Disable debug mode in production
- [ ] Regular penetration testing

## Performance Tuning

### Database Query Optimization (if added)
```python
# Use indexed queries
# Implement caching
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

@app.route('/expensive')
@cache.cached(timeout=300)
def expensive_operation():
    return result
```

### Response Compression
```python
from flask_compress import Compress
Compress(app)
```

### Load Balancing
- Use round-robin across multiple Gunicorn workers
- Configure sticky sessions if needed
- Monitor worker health

## Backup Strategy

### Application Files
```bash
# Backup to S3
aws s3 sync /var/www/greenops s3://backup-bucket/greenops/
```

### Database (if added)
```bash
# Regular backups
0 2 * * * /usr/bin/mysqldump -uuser -ppass db_name | gzip > /backup/db_$(date +\%Y\%m\%d).sql.gz
```

### Log Retention
```bash
# Keep 30 days of logs
find /var/log/greenops -name "*.log" -mtime +30 -delete
```

## Disaster Recovery

1. **Automated Backups**: Daily to S3
2. **Log Aggregation**: Centralized logging
3. **Database Replication**: Multi-region
4. **Health Checks**: Automated monitoring
5. **Failover**: Automatic instance replacement

## Cost Optimization

- Use spot instances for non-critical workloads
- Auto-scaling groups based on load
- CDN for static assets
- Database connection pooling
- Request caching strategies

## Maintenance windows

Schedule during low-traffic periods:
- Database optimization
- Security patches
- Dependency updates
- Performance tuning

---

**Last Updated:** March 2026
**Version:** 2.0
