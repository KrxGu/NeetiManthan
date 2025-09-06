# NeetiManthan Deployment Guide

This guide covers deploying NeetiManthan from development to production.

## 🚀 Quick Deployment Checklist

### Pre-deployment
- [ ] Docker and Docker Compose installed
- [ ] Minimum 8GB RAM, 10GB disk space
- [ ] Network ports 8000-8004, 5432, 6379, 9000-9001 available
- [ ] Environment variables configured

### Deployment Steps
- [ ] Clone repository
- [ ] Configure environment (`.env` file)
- [ ] Start infrastructure services (DB, Redis, MinIO)
- [ ] Run database migrations
- [ ] Start application services
- [ ] Verify health checks
- [ ] Run demo to validate functionality

### Post-deployment
- [ ] Monitor service logs
- [ ] Verify API endpoints
- [ ] Test comment processing pipeline
- [ ] Set up monitoring and alerts
- [ ] Configure backups

## 🏗️ Development Environment

### Prerequisites
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Quick Start
```bash
# Clone and setup
git clone <repository-url>
cd NeetiManthan_C
cp env.example .env

# Start all services
./scripts/start.sh

# Verify deployment
python3 scripts/demo.py
```

## 🏭 Production Deployment

### Infrastructure Requirements

#### Minimum Specs
- **CPU**: 4 cores
- **RAM**: 8GB (16GB recommended)
- **Storage**: 50GB SSD
- **Network**: 1Gbps

#### Recommended Specs (High Load)
- **CPU**: 8+ cores
- **RAM**: 32GB+
- **Storage**: 200GB+ SSD
- **Network**: 10Gbps
- **Load Balancer**: NGINX/HAProxy

### Production Configuration

1. **Create production environment file**
```bash
cp env.example .env.production
```

2. **Update production settings**
```bash
# Security
SECRET_KEY=your-super-secret-production-key-here
DEBUG=false
ENVIRONMENT=production

# Database (use managed service in production)
DATABASE_URL=postgresql://user:pass@prod-db:5432/neetimanthan

# Redis (use managed service)
REDIS_URL=redis://prod-redis:6379/0

# AI Models (consider model optimization)
SENTIMENT_MODEL=cardiffnlp/twitter-xlm-roberta-base-sentiment
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Processing (tune based on load)
CONFIDENCE_THRESHOLD=0.75
MAX_CLAUSE_CANDIDATES=3
```

3. **Deploy with production compose**
```bash
# Create production docker-compose file
cp docker-compose.yml docker-compose.prod.yml

# Update for production (remove debug volumes, add restart policies)
# Start production deployment
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Security Hardening

1. **Network Security**
```bash
# Use internal networks for service communication
# Expose only necessary ports (8000) to public
# Use TLS/SSL certificates (Let's Encrypt)
```

2. **Database Security**
```bash
# Use strong passwords
# Enable SSL connections
# Regular backups
# Network isolation
```

3. **Application Security**
```bash
# Regular security updates
# Input validation
# Rate limiting
# API authentication
```

## ☸️ Kubernetes Deployment

### Kubernetes Manifests

1. **Namespace**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: neetimanthan
```

2. **ConfigMap**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: neetimanthan-config
  namespace: neetimanthan
data:
  DATABASE_URL: "postgresql://postgres:password@postgres:5432/neetimanthan"
  REDIS_URL: "redis://redis:6379/0"
  CONFIDENCE_THRESHOLD: "0.75"
```

3. **Deployments**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: neetimanthan
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: neetimanthan/api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: neetimanthan-config
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### Deployment Commands
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n neetimanthan

# View logs
kubectl logs -f deployment/api-gateway -n neetimanthan

# Scale services
kubectl scale deployment api-gateway --replicas=5 -n neetimanthan
```

## 📊 Monitoring & Observability

### Health Checks
```bash
# API Health
curl http://localhost:8000/api/v1/health

# Service Health
curl http://localhost:8001/health  # Ingest Tool
curl http://localhost:8002/health  # Classify Tool
curl http://localhost:8003/health  # Clause Linker
```

### Metrics to Monitor
- **API Response Times**: p50, p95, p99
- **Processing Queue Depth**: Redis queue length
- **Database Connections**: Active connections
- **Memory Usage**: Per service memory consumption
- **Error Rates**: 4xx, 5xx response rates
- **AI Model Performance**: Inference latency, accuracy

### Logging
```bash
# View service logs
docker-compose logs -f api
docker-compose logs -f classify-tool
docker-compose logs -f worker

# Structured logging format
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "classify-tool",
  "message": "Classification completed",
  "comment_id": "uuid",
  "confidence": 0.85,
  "processing_time_ms": 120
}
```

## 🔄 Backup & Recovery

### Database Backup
```bash
# Daily backup
docker-compose exec db pg_dump -U postgres neetimanthan > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T db psql -U postgres neetimanthan < backup_20240101.sql
```

### Object Storage Backup
```bash
# Backup MinIO data
docker run --rm -v neetimanthan_minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz /data
```

### Configuration Backup
```bash
# Backup configurations
tar czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml k8s/
```

## 🔧 Troubleshooting

### Common Issues

1. **Services not starting**
```bash
# Check Docker resources
docker system df
docker system prune

# Check port conflicts
netstat -tulpn | grep :8000

# View detailed logs
docker-compose logs --tail=100 service-name
```

2. **Database connection issues**
```bash
# Check PostgreSQL status
docker-compose exec db pg_isready -U postgres

# Test connection from API
docker-compose exec api python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

3. **AI Model loading issues**
```bash
# Check disk space for model downloads
df -h

# Manually download models
docker-compose exec classify-tool python -c "from transformers import AutoModel; AutoModel.from_pretrained('cardiffnlp/twitter-xlm-roberta-base-sentiment')"
```

4. **Performance issues**
```bash
# Check resource usage
docker stats

# Monitor queue depth
docker-compose exec redis redis-cli llen celery

# Check database performance
docker-compose exec db psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### Performance Tuning

1. **Database Optimization**
```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_comments_draft_id ON comments_raw(draft_id);
CREATE INDEX CONCURRENTLY idx_predictions_confidence ON predictions(confidence);

-- Update table statistics
ANALYZE;
```

2. **Redis Configuration**
```bash
# Increase memory limit
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

3. **Application Scaling**
```bash
# Scale worker processes
docker-compose up -d --scale worker=4

# Scale tool services
docker-compose up -d --scale classify-tool=2
```

## 📈 Capacity Planning

### Load Testing
```bash
# Install k6 for load testing
brew install k6

# Run load test
k6 run scripts/load_test.js
```

### Scaling Guidelines
- **1,000 comments/hour**: Single instance deployment
- **10,000 comments/hour**: 2-3 API replicas, 4-6 workers
- **100,000 comments/hour**: Kubernetes cluster, horizontal scaling
- **1M+ comments/hour**: Distributed deployment, message queues

### Resource Requirements by Scale
| Scale | CPU Cores | RAM | Storage | Network |
|-------|-----------|-----|---------|---------|
| Small (1K/hr) | 4 | 8GB | 50GB | 1Gbps |
| Medium (10K/hr) | 8 | 16GB | 200GB | 10Gbps |
| Large (100K/hr) | 16+ | 32GB+ | 1TB+ | 10Gbps+ |

## 🚨 Incident Response

### Monitoring Alerts
- API response time > 5s
- Error rate > 5%
- Queue depth > 1000
- Disk usage > 80%
- Memory usage > 90%

### Response Procedures
1. **Check service health**
2. **Review recent logs**
3. **Scale affected services**
4. **Investigate root cause**
5. **Apply fixes**
6. **Monitor recovery**

## 📞 Support

For deployment issues:
1. Check this deployment guide
2. Review service logs
3. Consult API documentation
4. Create GitHub issue with logs and configuration

---

**Happy deploying! 🚀**
