# AI-CPaaS Demo - EC2 Deployment Guide

**Target**: EC2 Instance with Public Access  
**Deployment Time**: 30-45 minutes  
**Result**: Public URL for demo access  
**Cost**: ~$20-40/month

---

## Overview

This guide deploys the AI-CPaaS demo on an EC2 instance with:
- ✅ Public URL access (HTTP/HTTPS)
- ✅ Nginx reverse proxy
- ✅ Systemd service for auto-restart
- ✅ SSL certificate (optional)
- ✅ Full AWS integration

---

## Architecture

```
Internet → [Route 53/Domain] → [EC2 Public IP] → [Nginx:80/443] → [Flask:5000] → [AWS Services]
                                      ↓
                              [Security Group]
                                      ↓
                          [DynamoDB, End User Messaging]
```

---

## Prerequisites

### 1. AWS Account Access
- AWS Console access
- Permissions to create EC2 instances
- Existing VPC and subnet

### 2. Local Requirements
- AWS CLI configured
- SSH key pair for EC2 access

---

## Part 1: Launch EC2 Instance

### Step 1: Create EC2 Instance

**Via AWS Console**:

1. Go to **EC2 Dashboard** → **Launch Instance**

2. **Configure Instance**:
   - **Name**: `ai-cpaas-demo`
   - **AMI**: Amazon Linux 2023 (or Ubuntu 22.04)
   - **Instance Type**: `t3.medium` (2 vCPU, 4 GB RAM)
   - **Key Pair**: Select or create new key pair
   - **Network**: Default VPC (or your VPC)
   - **Auto-assign Public IP**: **Enable**

3. **Configure Storage**:
   - **Size**: 20 GB gp3
   - **Delete on termination**: Yes

4. **Security Group** (Create new):
   - **Name**: `ai-cpaas-demo-sg`
   - **Rules**:
     ```
     SSH (22)     - Your IP only
     HTTP (80)    - 0.0.0.0/0 (anywhere)
     HTTPS (443)  - 0.0.0.0/0 (anywhere)
     Custom (5000) - Your IP only (for testing)
     ```

5. **IAM Role** (Important!):
   - Create or attach IAM role with these policies:
     - `AmazonDynamoDBFullAccess`
     - `AmazonSESFullAccess` (for End User Messaging)
     - Custom policy for End User Messaging:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "sms-voice:*",
             "social-messaging:*"
           ],
           "Resource": "*"
         }
       ]
     }
     ```

6. **Launch Instance**

### Step 2: Note Instance Details

```bash
# Note these values:
EC2_PUBLIC_IP=<your-instance-public-ip>
EC2_INSTANCE_ID=<your-instance-id>
KEY_PAIR_PATH=<path-to-your-key.pem>
```

---

## Part 2: Connect and Setup EC2

### Step 1: Connect to EC2

```bash
# Set key permissions
chmod 400 $KEY_PAIR_PATH

# Connect via SSH
ssh -i $KEY_PAIR_PATH ec2-user@$EC2_PUBLIC_IP

# For Ubuntu, use:
# ssh -i $KEY_PAIR_PATH ubuntu@$EC2_PUBLIC_IP
```

### Step 2: Install System Dependencies

```bash
# Update system
sudo yum update -y  # Amazon Linux
# sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python 3.11
sudo yum install -y python3.11 python3.11-pip  # Amazon Linux
# sudo apt install -y python3.11 python3.11-pip python3.11-venv  # Ubuntu

# Install Git
sudo yum install -y git  # Amazon Linux
# sudo apt install -y git  # Ubuntu

# Install Nginx
sudo yum install -y nginx  # Amazon Linux
# sudo apt install -y nginx  # Ubuntu

# Install development tools
sudo yum groupinstall -y "Development Tools"  # Amazon Linux
# sudo apt install -y build-essential  # Ubuntu
```

### Step 3: Configure AWS Credentials

```bash
# Configure AWS CLI (use IAM role instead if attached)
aws configure

# Or verify IAM role is working
aws sts get-caller-identity

# Should show your AWS account and role
```

---

## Part 3: Deploy Application

### Step 1: Clone Repository

**Option A: From GitLab (if pushed)**:
```bash
# Clone from GitLab
git clone git@gitlab.aws.dev:satyaso/appliedai-cpaas.git
cd appliedai-cpaas
```

**Option B: Transfer from Local Machine**:
```bash
# On your local machine, create a tarball
cd /Users/satyaso/work/code-dev/appliedai-cpaas
tar -czf ai-cpaas-demo.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  .

# Transfer to EC2
scp -i $KEY_PAIR_PATH ai-cpaas-demo.tar.gz ec2-user@$EC2_PUBLIC_IP:~

# On EC2, extract
ssh -i $KEY_PAIR_PATH ec2-user@$EC2_PUBLIC_IP
mkdir -p ~/appliedai-cpaas
cd ~/appliedai-cpaas
tar -xzf ../ai-cpaas-demo.tar.gz
```

### Step 2: Install Python Dependencies

```bash
cd ~/appliedai-cpaas

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install production server
pip install gunicorn
```

### Step 3: Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit with your AWS configuration
nano .env

# Add/update these values:
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=378318846552
DYNAMODB_RATE_LIMITS_TABLE=ai-cpaas-rate-limits
DYNAMODB_DELIVERY_TRACKING_TABLE=ai-cpaas-delivery-tracking
FLASK_ENV=production
```

### Step 4: Seed Demo Data

```bash
# Activate virtual environment
source ~/appliedai-cpaas/venv/bin/activate

# Seed data
python3 -c "
from src.ai_cpaas_demo.data.data_seeder import DataSeeder
seeder = DataSeeder()
seeder.seed_all()
print('✅ Demo data seeded successfully!')
"
```

### Step 5: Test Application

```bash
# Test run (should work)
python3 run_demo_ui.py

# Press Ctrl+C to stop
```

---

## Part 4: Configure Production Server

### Step 1: Create Gunicorn Configuration

```bash
# Create Gunicorn config
cat > ~/appliedai-cpaas/gunicorn_config.py << 'EOF'
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/ai-cpaas/access.log"
errorlog = "/var/log/ai-cpaas/error.log"
loglevel = "info"

# Process naming
proc_name = "ai-cpaas-demo"

# Server mechanics
daemon = False
pidfile = "/var/run/ai-cpaas/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
EOF
```

### Step 2: Create Systemd Service

```bash
# Create log directory
sudo mkdir -p /var/log/ai-cpaas
sudo mkdir -p /var/run/ai-cpaas
sudo chown -R ec2-user:ec2-user /var/log/ai-cpaas /var/run/ai-cpaas

# Create systemd service
sudo tee /etc/systemd/system/ai-cpaas.service > /dev/null << EOF
[Unit]
Description=AI-CPaaS Demo Application
After=network.target

[Service]
Type=notify
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/appliedai-cpaas
Environment="PATH=/home/ec2-user/appliedai-cpaas/venv/bin"
ExecStart=/home/ec2-user/appliedai-cpaas/venv/bin/gunicorn \
    --config /home/ec2-user/appliedai-cpaas/gunicorn_config.py \
    src.ai_cpaas_demo.web.app:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable ai-cpaas
sudo systemctl start ai-cpaas

# Check status
sudo systemctl status ai-cpaas
```

### Step 3: Configure Nginx

```bash
# Create Nginx configuration
sudo tee /etc/nginx/conf.d/ai-cpaas.conf > /dev/null << 'EOF'
upstream ai_cpaas {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name _;  # Replace with your domain if you have one

    # Increase timeouts for long-running requests
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

    # Increase buffer sizes
    client_max_body_size 10M;
    client_body_buffer_size 128k;

    # Logging
    access_log /var/log/nginx/ai-cpaas-access.log;
    error_log /var/log/nginx/ai-cpaas-error.log;

    location / {
        proxy_pass http://ai_cpaas;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files (if any)
    location /static {
        alias /home/ec2-user/appliedai-cpaas/src/ai_cpaas_demo/web/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## Part 5: Access Your Demo

### Get Your Public URL

```bash
# Get your EC2 public IP
EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "Your demo is available at: http://$EC2_PUBLIC_IP"
```

### Test Access

Open your browser and navigate to:
```
http://<your-ec2-public-ip>
```

You should see the AI-CPaaS Demo UI!

---

## Part 6: Optional - Add Custom Domain & SSL

### Step 1: Configure Route 53 (Optional)

If you have a domain:

1. **Go to Route 53** → **Hosted Zones**
2. **Create Record**:
   - **Name**: `demo.yourdomain.com`
   - **Type**: A
   - **Value**: Your EC2 public IP
   - **TTL**: 300

### Step 2: Install SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo yum install -y certbot python3-certbot-nginx  # Amazon Linux
# sudo apt install -y certbot python3-certbot-nginx  # Ubuntu

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d demo.yourdomain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose redirect HTTP to HTTPS

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 3: Update Nginx for SSL

Certbot automatically updates Nginx config. Verify:

```bash
# Check Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

Now access via HTTPS:
```
https://demo.yourdomain.com
```

---

## Part 7: Monitoring and Maintenance

### View Application Logs

```bash
# Application logs
sudo journalctl -u ai-cpaas -f

# Nginx access logs
sudo tail -f /var/log/nginx/ai-cpaas-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/ai-cpaas-error.log

# Gunicorn logs
sudo tail -f /var/log/ai-cpaas/error.log
```

### Restart Services

```bash
# Restart application
sudo systemctl restart ai-cpaas

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status ai-cpaas
sudo systemctl status nginx
```

### Update Application

```bash
# Pull latest changes (if using Git)
cd ~/appliedai-cpaas
git pull origin main

# Or transfer new files via SCP

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart application
sudo systemctl restart ai-cpaas
```

### Monitor Resources

```bash
# Check CPU and memory
htop

# Check disk space
df -h

# Check network
netstat -tulpn | grep -E '(80|443|5000)'
```

---

## Part 8: Security Hardening

### 1. Update Security Group

```bash
# Remove port 5000 from security group (only allow 80/443)
# Keep SSH (22) restricted to your IP only
```

### 2. Enable Firewall

```bash
# Amazon Linux
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Ubuntu
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### 3. Set Up Automatic Updates

```bash
# Amazon Linux
sudo yum install -y yum-cron
sudo systemctl enable yum-cron
sudo systemctl start yum-cron

# Ubuntu
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 4. Configure CloudWatch Monitoring

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Configure and start
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c default
```

---

## Part 9: Backup and Disaster Recovery

### Backup Strategy

```bash
# Create backup script
cat > ~/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ec2-user/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup application
tar -czf $BACKUP_DIR/app_$DATE.tar.gz ~/appliedai-cpaas

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /var/log/ai-cpaas /var/log/nginx

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x ~/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ec2-user/backup.sh") | crontab -
```

### Create AMI Snapshot

```bash
# Via AWS CLI
aws ec2 create-image \
  --instance-id $EC2_INSTANCE_ID \
  --name "ai-cpaas-demo-$(date +%Y%m%d)" \
  --description "AI-CPaaS Demo backup"
```

---

## Troubleshooting

### Issue 1: Can't Access via Public IP

**Check**:
```bash
# Verify Nginx is running
sudo systemctl status nginx

# Verify application is running
sudo systemctl status ai-cpaas

# Check if port 80 is listening
sudo netstat -tulpn | grep :80

# Check security group allows port 80/443
```

### Issue 2: Application Not Starting

**Check logs**:
```bash
# Application logs
sudo journalctl -u ai-cpaas -n 50

# Check for Python errors
source ~/appliedai-cpaas/venv/bin/activate
cd ~/appliedai-cpaas
python3 run_demo_ui.py
```

### Issue 3: 502 Bad Gateway

**Cause**: Gunicorn not running or Nginx can't connect

**Fix**:
```bash
# Restart application
sudo systemctl restart ai-cpaas

# Check Gunicorn is listening
sudo netstat -tulpn | grep :5000

# Check Nginx error logs
sudo tail -f /var/log/nginx/ai-cpaas-error.log
```

### Issue 4: AWS Permissions Error

**Cause**: IAM role missing permissions

**Fix**:
```bash
# Verify IAM role
aws sts get-caller-identity

# Test DynamoDB access
aws dynamodb list-tables

# If fails, attach proper IAM role to EC2 instance
```

---

## Cost Optimization

### Current Setup Cost (Monthly)

- **EC2 t3.medium**: ~$30/month
- **EBS 20GB gp3**: ~$2/month
- **Data Transfer**: ~$5-10/month
- **Total**: ~$37-42/month

### Reduce Costs

1. **Use t3.small** (if traffic is low): ~$15/month
2. **Stop instance when not demoing**: $0 when stopped
3. **Use Reserved Instance**: Save 30-40%
4. **Use Spot Instance**: Save up to 70% (less reliable)

---

## Quick Reference

### Essential Commands

```bash
# Check application status
sudo systemctl status ai-cpaas

# Restart application
sudo systemctl restart ai-cpaas

# View logs
sudo journalctl -u ai-cpaas -f

# Check Nginx
sudo systemctl status nginx
sudo nginx -t

# Update application
cd ~/appliedai-cpaas
git pull
sudo systemctl restart ai-cpaas
```

### Access URLs

```bash
# HTTP
http://<your-ec2-public-ip>

# HTTPS (if configured)
https://demo.yourdomain.com

# Health check
http://<your-ec2-public-ip>/health
```

---

## Summary

Your AI-CPaaS demo is now running on EC2 with:

✅ **Public URL access** - Anyone can access via browser  
✅ **Production-ready** - Gunicorn + Nginx + Systemd  
✅ **Auto-restart** - Survives crashes and reboots  
✅ **SSL ready** - Easy to add HTTPS  
✅ **Monitored** - Logs and health checks  
✅ **Scalable** - Can upgrade instance size anytime  

**Your demo URL**: `http://<your-ec2-public-ip>`

🚀 **Ready to showcase your AI-CPaaS demo to the world!**
