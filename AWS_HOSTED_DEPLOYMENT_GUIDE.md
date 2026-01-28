# AWS Hosted Deployment Guide - AI-CPaaS Demo

**Goal**: Deploy and showcase the AI-CPaaS demo on AWS with a public URL

---

## Deployment Options

### Option 1: AWS Amplify (Recommended - Easiest) ⭐
**Best for**: Quick deployment, automatic CI/CD, managed hosting  
**Cost**: ~$15-30/month  
**Time**: 15 minutes

### Option 2: AWS App Runner (Containerized)
**Best for**: Production-ready, auto-scaling, managed containers  
**Cost**: ~$25-50/month  
**Time**: 30 minutes

### Option 3: ECS Fargate + ALB (Full Production)
**Best for**: Enterprise deployment, full control, high availability  
**Cost**: ~$50-100/month  
**Time**: 1-2 hours

### Option 4: EC2 + Nginx (Traditional)
**Best for**: Maximum control, custom configuration  
**Cost**: ~$20-40/month  
**Time**: 45 minutes

---

## Option 1: AWS Amplify Deployment (Recommended)

### Why Amplify?
- ✅ Automatic HTTPS with custom domain
- ✅ CI/CD from GitLab
- ✅ Auto-scaling and CDN
- ✅ Easy rollbacks
- ✅ Preview environments

### Prerequisites
- GitLab repository (push your code first)
- AWS account with Amplify access

### Step 1: Prepare Application for Amplify

Create Amplify build configuration:

```bash
cat > amplify.yml << 'EOF'
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - pip3 install -r requirements.txt
    build:
      commands:
        - echo "Build complete"
  artifacts:
    baseDirectory: /
    files:
      - '**/*'
  cache:
    paths:
      - '.venv/**/*'
backend:
  phases:
    build:
      commands:
        - echo "Backend build"
EOF
```

Create startup script:

```bash
cat > start.sh << 'EOF'
#!/bin/bash
# Amplify startup script
export FLASK_APP=src/ai_cpaas_demo/web/app.py
export FLASK_ENV=production
python3 -m flask run --host=0.0.0.0 --port=8080
EOF
chmod +x start.sh
```

### Step 2: Deploy to Amplify

#### Via AWS Console:

1. **Go to AWS Amplify Console**:
   - https://console.aws.amazon.com/amplify/

2. **Create New App**:
   - Click "New app" → "Host web app"
   - Choose "GitLab" as source
   - Authorize AWS to access your GitLab

3. **Connect Repository**:
   - Select your GitLab repository: `satyaso/appliedai-cpaas`
   - Branch: `main`
   - Click "Next"

4. **Configure Build Settings**:
   - App name: `ai-cpaas-demo`
   - Environment: `production`
   - Build command: Auto-detected from `amplify.yml`
   - Click "Next"

5. **Review and Deploy**:
   - Review settings
   - Click "Save and deploy"

#### Via AWS CLI:

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize Amplify
amplify init

# Add hosting
amplify add hosting

# Publish
amplify publish
```

### Step 3: Configure Environment Variables

In Amplify Console:
1. Go to "App settings" → "Environment variables"
2. Add variables from `.env.aws`:
   ```
   AWS_REGION=us-east-1
   RATE_LIMITS_TABLE=ai-cpaas-demo-rate-limits-dev
   DELIVERY_TRACKING_TABLE=ai-cpaas-demo-delivery-tracking-dev
   FLASK_ENV=production
   ```

### Step 4: Access Your Demo

After deployment (5-10 minutes):
- **URL**: `https://main.d1234abcd.amplifyapp.com`
- **Custom Domain** (optional): Configure in Amplify Console

---

## Option 2: AWS App Runner Deployment

### Why App Runner?
- ✅ Fully managed containers
- ✅ Auto-scaling
- ✅ Built-in load balancing
- ✅ HTTPS included

### Step 1: Create Dockerfile

```bash
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Set environment
ENV FLASK_APP=src/ai_cpaas_demo/web/app.py
ENV FLASK_ENV=production

# Run application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080"]
EOF
```

### Step 2: Build and Push to ECR

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name ai-cpaas-demo \
  --region us-east-1

# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  378318846552.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t ai-cpaas-demo .

# Tag image
docker tag ai-cpaas-demo:latest \
  378318846552.dkr.ecr.us-east-1.amazonaws.com/ai-cpaas-demo:latest

# Push image
docker push 378318846552.dkr.ecr.us-east-1.amazonaws.com/ai-cpaas-demo:latest
```

### Step 3: Create App Runner Service

```bash
# Create service
aws apprunner create-service \
  --service-name ai-cpaas-demo \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "378318846552.dkr.ecr.us-east-1.amazonaws.com/ai-cpaas-demo:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8080",
        "RuntimeEnvironmentVariables": {
          "AWS_REGION": "us-east-1",
          "RATE_LIMITS_TABLE": "ai-cpaas-demo-rate-limits-dev",
          "DELIVERY_TRACKING_TABLE": "ai-cpaas-demo-delivery-tracking-dev"
        }
      }
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }' \
  --region us-east-1
```

### Step 4: Get Service URL

```bash
aws apprunner describe-service \
  --service-arn <service-arn> \
  --query 'Service.ServiceUrl' \
  --output text
```

---

## Option 3: ECS Fargate + ALB (Production)

### Architecture
```
Internet → ALB → ECS Fargate → DynamoDB
                    ↓
                CloudWatch
```

### Step 1: Create ECS Infrastructure

Create CloudFormation template:

```bash
cat > infrastructure/cloudformation/ecs-deployment.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Description: 'AI-CPaaS Demo - ECS Fargate Deployment'

Parameters:
  Environment:
    Type: String
    Default: prod
  
  ImageUri:
    Type: String
    Description: ECR image URI

Resources:
  # VPC and Networking
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true

  InternetGateway:
    Type: AWS::EC2::InternetGateway

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # Application Load Balancer
  ALB:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: ai-cpaas-demo-alb
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroup

  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref ALB
      Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: ai-cpaas-demo-tg
      Port: 8080
      Protocol: HTTP
      VpcId: !Ref VPC
      TargetType: ip
      HealthCheckPath: /
      HealthCheckIntervalSeconds: 30

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: ai-cpaas-demo-cluster

  # ECS Task Definition
  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: ai-cpaas-demo
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: '512'
      Memory: '1024'
      ExecutionRoleArn: !GetAtt ExecutionRole.Arn
      TaskRoleArn: !GetAtt TaskRole.Arn
      ContainerDefinitions:
        - Name: ai-cpaas-demo
          Image: !Ref ImageUri
          PortMappings:
            - ContainerPort: 8080
          Environment:
            - Name: AWS_REGION
              Value: !Ref AWS::Region
            - Name: RATE_LIMITS_TABLE
              Value: ai-cpaas-demo-rate-limits-dev
            - Name: DELIVERY_TRACKING_TABLE
              Value: ai-cpaas-demo-delivery-tracking-dev
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: /ecs/ai-cpaas-demo
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs

  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    DependsOn: ALBListener
    Properties:
      ServiceName: ai-cpaas-demo-service
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          AssignPublicIp: ENABLED
          Subnets:
            - !Ref PublicSubnet1
            - !Ref PublicSubnet2
          SecurityGroups:
            - !Ref ECSSecurityGroup
      LoadBalancers:
        - ContainerName: ai-cpaas-demo
          ContainerPort: 8080
          TargetGroupArn: !Ref TargetGroup

  # Security Groups
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: ALB Security Group
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0

  ECSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: ECS Security Group
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8080
          ToPort: 8080
          SourceSecurityGroupId: !Ref ALBSecurityGroup

  # IAM Roles
  ExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

  TaskRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: ecs-tasks.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: DynamoDBAccess
          PolicyDocument:
            Statement:
              - Effect: Allow
                Action:
                  - dynamodb:*
                Resource: '*'

Outputs:
  LoadBalancerURL:
    Description: Load Balancer URL
    Value: !GetAtt ALB.DNSName
EOF
```

### Step 2: Deploy ECS Stack

```bash
# Deploy
aws cloudformation create-stack \
  --stack-name ai-cpaas-demo-ecs \
  --template-body file://infrastructure/cloudformation/ecs-deployment.yaml \
  --parameters \
    ParameterKey=ImageUri,ParameterValue=378318846552.dkr.ecr.us-east-1.amazonaws.com/ai-cpaas-demo:latest \
  --capabilities CAPABILITY_IAM \
  --region us-east-1

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name ai-cpaas-demo-ecs \
  --region us-east-1

# Get ALB URL
aws cloudformation describe-stacks \
  --stack-name ai-cpaas-demo-ecs \
  --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
  --output text
```

---

## Option 4: EC2 + Nginx

### Step 1: Launch EC2 Instance

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name ai-cpaas-demo-key \
  --query 'KeyMaterial' \
  --output text > ai-cpaas-demo-key.pem
chmod 400 ai-cpaas-demo-key.pem

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name ai-cpaas-demo-key \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ai-cpaas-demo}]'
```

### Step 2: Install and Configure

```bash
# SSH to instance
ssh -i ai-cpaas-demo-key.pem ec2-user@<public-ip>

# Install dependencies
sudo yum update -y
sudo yum install python3 python3-pip nginx git -y

# Clone repository
git clone https://gitlab.aws.dev/satyaso/appliedai-cpaas.git
cd appliedai-cpaas

# Install Python dependencies
pip3 install -r requirements.txt

# Configure environment
cp .env.aws .env
source .env

# Create systemd service
sudo cat > /etc/systemd/system/ai-cpaas-demo.service << 'EOF'
[Unit]
Description=AI-CPaaS Demo
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/appliedai-cpaas
Environment="FLASK_APP=src/ai_cpaas_demo/web/app.py"
Environment="FLASK_ENV=production"
ExecStart=/usr/bin/python3 -m flask run --host=0.0.0.0 --port=8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable ai-cpaas-demo
sudo systemctl start ai-cpaas-demo

# Configure Nginx
sudo cat > /etc/nginx/conf.d/ai-cpaas-demo.conf << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Post-Deployment Configuration

### 1. Configure Custom Domain (Optional)

#### Route 53 Setup:
```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name demo.yourdomain.com \
  --caller-reference $(date +%s)

# Create A record pointing to ALB/Amplify
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://dns-record.json
```

### 2. Enable HTTPS

#### For ALB (Option 3):
```bash
# Request certificate
aws acm request-certificate \
  --domain-name demo.yourdomain.com \
  --validation-method DNS \
  --region us-east-1

# Add HTTPS listener to ALB
aws elbv2 create-listener \
  --load-balancer-arn <alb-arn> \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=<cert-arn> \
  --default-actions Type=forward,TargetGroupArn=<tg-arn>
```

### 3. Set Up Monitoring

Create CloudWatch dashboard:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name ai-cpaas-demo \
  --dashboard-body file://infrastructure/cloudwatch-dashboard.json
```

---

## Demo Showcase Checklist

### Before Presenting:

- [ ] **Test the demo URL** - Ensure it loads
- [ ] **Verify data is seeded** - Run `python regenerate_customer_data.py`
- [ ] **Check AWS infrastructure** - DynamoDB tables accessible
- [ ] **Test campaign queries** - Try different locations/SKUs
- [ ] **Verify WhatsApp templates** - Templates loaded correctly
- [ ] **Check cost calculator** - ROI numbers displaying
- [ ] **Test all AI engines** - Prediction, adaptation, guardrail working
- [ ] **Review suppression reasons** - Detailed explanations showing
- [ ] **Check mobile responsiveness** - UI works on phone/tablet
- [ ] **Prepare backup** - Have local version ready

### Demo Flow:

1. **Introduction** (2 min)
   - Show architecture diagram
   - Explain AI-powered campaign orchestration

2. **Live Demo** (5 min)
   - Select location and SKU
   - Show AI decision-making process
   - Highlight cost savings (81% reduction)
   - Show suppression reasons (tone-deaf prevention)

3. **Technical Deep Dive** (3 min)
   - Show AWS infrastructure (CloudFormation)
   - Explain rate limiting and delivery tracking
   - Show CloudWatch metrics

4. **ROI Analysis** (2 min)
   - Present $122K annual savings for 1M users
   - Show 3x engagement improvement
   - Discuss 4.9 month payback period

---

## Troubleshooting

### Issue: Application won't start
```bash
# Check logs
aws logs tail /aws/apprunner/ai-cpaas-demo --follow

# Or for ECS
aws logs tail /ecs/ai-cpaas-demo --follow
```

### Issue: DynamoDB access denied
- Verify IAM role has DynamoDB permissions
- Check environment variables are set correctly

### Issue: Slow performance
- Increase instance size (t3.medium → t3.large)
- Enable caching
- Use CloudFront CDN

---

## Cost Optimization

### Monthly Cost Breakdown:

| Service | Cost |
|---------|------|
| **Amplify** | $15-30 |
| **App Runner** | $25-50 |
| **ECS Fargate** | $50-100 |
| **EC2 t3.medium** | $30-40 |
| **DynamoDB** | $5 |
| **CloudWatch** | $3 |
| **Data Transfer** | $5-10 |

### Cost Saving Tips:
- Use Amplify for demos (cheapest)
- Stop ECS tasks when not presenting
- Use t3.micro for testing ($8/month)
- Enable auto-scaling to scale to zero

---

## Next Steps

1. **Choose deployment option** (Amplify recommended)
2. **Deploy infrastructure**
3. **Configure custom domain** (optional)
4. **Test thoroughly**
5. **Prepare demo script**
6. **Share URL with stakeholders**

---

## Quick Start Commands

```bash
# Option 1: Amplify (after pushing to GitLab)
# Just use AWS Console - easiest!

# Option 2: App Runner
docker build -t ai-cpaas-demo .
# Push to ECR and create App Runner service

# Option 3: ECS
aws cloudformation create-stack --stack-name ai-cpaas-demo-ecs ...

# Option 4: EC2
# Launch instance and run setup script
```

---

**Recommendation**: Start with **AWS Amplify** for quick showcase, then migrate to **ECS Fargate** for production if needed.

**Demo URL Format**: `https://main.d1234abcd.amplifyapp.com` or custom domain

🚀 **Ready to showcase your AI-CPaaS demo on AWS!**
