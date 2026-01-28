# AWS Deployment Plan - Complete Guide

## Current Status

✅ **Code**: All code is complete and tested locally
✅ **Infrastructure**: CloudFormation templates ready
✅ **Documentation**: Comprehensive guides available
✅ **UI Fix**: JavaScript function ordering fixed
⬜ **AWS Deployment**: Ready to execute

## Deployment Options

You have two deployment paths:

### Option 1: AWS Amplify (Recommended for Demo)
- **Pros**: Easiest, automatic CI/CD, managed hosting
- **Cons**: Requires GitLab push, takes 10-15 minutes
- **Best for**: Quick demo deployment, staging environment

### Option 2: AWS EC2 / Workspace
- **Pros**: Full control, can test immediately
- **Cons**: Manual setup, need to manage server
- **Best for**: Testing, development, custom configurations

## Step-by-Step Deployment

### Phase 1: Deploy Infrastructure (Required for Both Options)

#### 1.1 Deploy CloudFormation Stack

```bash
cd infrastructure
./deploy.sh
```

**What this creates**:
- 2 DynamoDB tables (rate limits, delivery tracking)
- 1 Lambda function (delivery processor)
- 2 EventBridge rules (SMS/WhatsApp events)
- 2 IAM roles (Lambda, Application)
- 4 CloudWatch alarms
- 1 SNS topic

**Time**: 5-7 minutes
**Cost**: ~$11/month

#### 1.2 Verify Infrastructure

```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name ai-cpaas-messaging-infrastructure \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus'

# List created resources
aws cloudformation list-stack-resources \
  --stack-name ai-cpaas-messaging-infrastructure \
  --region us-east-1
```

#### 1.3 Get Stack Outputs

```bash
# Get all outputs
aws cloudformation describe-stacks \
  --stack-name ai-cpaas-messaging-infrastructure \
  --region us-east-1 \
  --query 'Stacks[0].Outputs'
```

**Save these values**:
- `RateLimitsTableName`
- `DeliveryTrackingTableName`
- `MessagingAppRoleArn`
- `DeliveryProcessorFunctionArn`

### Phase 2: Configure AWS End User Messaging

#### 2.1 Create Phone Pool (for SMS)

```bash
# Via AWS Console:
# 1. Go to AWS End User Messaging Console
# 2. Click "Phone pools" → "Create phone pool"
# 3. Select country (e.g., US)
# 4. Choose phone number type (Toll-free or 10DLC)
# 5. Request phone number
# 6. Note the Phone Pool ID

# Or via CLI:
aws pinpoint-sms-voice-v2 create-pool \
  --origination-identity <phone-number> \
  --iso-country-code US \
  --message-type TRANSACTIONAL \
  --region us-east-1
```

**Save**: `PHONE_POOL_ID`

#### 2.2 Set Up WhatsApp Business Account

```bash
# Via AWS Console:
# 1. Go to AWS End User Messaging Console
# 2. Click "WhatsApp" → "Register Business Account"
# 3. Follow Meta Business verification process
# 4. Create WhatsApp Business Account
# 5. Note the WhatsApp Business Account ID

# This process takes 1-3 business days for Meta approval
```

**Save**: `WHATSAPP_BUSINESS_ACCOUNT_ID`

#### 2.3 Create WhatsApp Templates

```bash
# Via AWS Console:
# 1. Go to WhatsApp Business Account
# 2. Click "Message templates" → "Create template"
# 3. Create templates for your campaigns

# Example template:
# Name: promotion_template
# Category: MARKETING
# Language: English
# Body: "Hi {{1}}, get {{2}} off on {{3}}! Shop now."
# Variables: name, discount, product
```

#### 2.4 Verify SES Email

```bash
# Verify sender email
aws ses verify-email-identity \
  --email-address noreply@yourdomain.com \
  --region us-east-1

# Check verification status
aws ses get-identity-verification-attributes \
  --identities noreply@yourdomain.com \
  --region us-east-1
```

**Save**: `SENDER_EMAIL`

### Phase 3A: Deploy to AWS Amplify (Recommended)

#### 3A.1 Push Code to GitLab

```bash
# Ensure all changes are committed
git add .
git commit -m "Fix: JavaScript function ordering for onclick handlers"
git push origin main
```

#### 3A.2 Create Amplify App

```bash
# Via AWS Console:
# 1. Go to AWS Amplify Console
# 2. Click "New app" → "Host web app"
# 3. Select "GitLab"
# 4. Authorize AWS Amplify
# 5. Select repository and branch
# 6. Amplify auto-detects amplify.yml
```

#### 3A.3 Configure Environment Variables

In Amplify Console → App Settings → Environment Variables:

```bash
FLASK_ENV=production
AWS_REGION=us-east-1
PHONE_POOL_ID=<from-step-2.1>
WHATSAPP_BUSINESS_ACCOUNT_ID=<from-step-2.2>
SENDER_EMAIL=<from-step-2.4>
RATE_LIMITS_TABLE=<from-stack-outputs>
DELIVERY_TRACKING_TABLE=<from-stack-outputs>
```

#### 3A.4 Configure IAM Role

```bash
# In Amplify Console → App Settings → General:
# 1. Edit "Service role"
# 2. Select the MessagingAppRole created by CloudFormation
# 3. Or create new role with policies:
#    - DynamoDB read/write
#    - AWS End User Messaging send
#    - AWS SES send
#    - CloudWatch logs
```

#### 3A.5 Deploy

```bash
# In Amplify Console:
# 1. Click "Save and deploy"
# 2. Wait 10-15 minutes
# 3. Access app at: https://main.d1234567890.amplifyapp.com
```

### Phase 3B: Deploy to EC2 / Workspace (Alternative)

#### 3B.1 Launch EC2 Instance

```bash
# Via AWS Console or CLI:
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxx \
  --iam-instance-profile Name=MessagingAppRole \
  --region us-east-1
```

#### 3B.2 Install Dependencies

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@<instance-ip>

# Install Python and dependencies
sudo yum update -y
sudo yum install python3 python3-pip git -y
git clone <your-repo-url>
cd appliedai-cpaas
pip3 install -r requirements.txt
```

#### 3B.3 Configure Environment

```bash
# Create .env.aws file
cat > .env.aws << EOF
FLASK_ENV=production
AWS_REGION=us-east-1
PHONE_POOL_ID=<from-step-2.1>
WHATSAPP_BUSINESS_ACCOUNT_ID=<from-step-2.2>
SENDER_EMAIL=<from-step-2.4>
RATE_LIMITS_TABLE=<from-stack-outputs>
DELIVERY_TRACKING_TABLE=<from-stack-outputs>
EOF

# Source environment
source .env.aws
```

#### 3B.4 Start Application

```bash
# Using gunicorn
gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 \
  "src.ai_cpaas_demo.web.app:app"

# Or using the start script
bash start.sh
```

### Phase 4: Test Deployment

#### 4.1 Test Environment Detection

```bash
# Get environment info
curl https://your-app-url.com/api/environment

# Expected response:
{
  "is_production": true,
  "environment": "production",
  "aws_enabled": true
}
```

#### 4.2 Test Campaign Query

```bash
# Run a campaign query
curl -X POST https://your-app-url.com/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Bangalore",
    "sku": "SKU-LAPTOP-001"
  }'

# Should return eligible users with selected channels
```

#### 4.3 Test Send Campaign (Small Batch)

```bash
# Send to 5 test users
curl -X POST https://your-app-url.com/api/send-campaign \
  -H "Content-Type: application/json" \
  -d '{
    "eligible_users": [...],
    "throughput_tps": 1,
    "campaign_id": "test-campaign-001"
  }'

# Expected response:
{
  "success": true,
  "results": {
    "total_sent": 5,
    "total_failed": 0,
    "by_channel": {...}
  }
}
```

#### 4.4 Verify Delivery Tracking

```bash
# Check DynamoDB for delivery records
aws dynamodb scan \
  --table-name ai-cpaas-demo-delivery-tracking-dev \
  --region us-east-1 \
  --max-items 10

# Check CloudWatch logs
aws logs tail /aws/lambda/ai-cpaas-demo-delivery-processor-dev \
  --follow \
  --region us-east-1
```

### Phase 5: Monitor and Optimize

#### 5.1 Set Up CloudWatch Dashboard

```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ai-cpaas-demo \
  --dashboard-body file://dashboard-config.json \
  --region us-east-1
```

#### 5.2 Configure Alarms

```bash
# List existing alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix ai-cpaas \
  --region us-east-1

# Subscribe to SNS topic for notifications
aws sns subscribe \
  --topic-arn <alarm-topic-arn> \
  --protocol email \
  --notification-endpoint your-email@example.com \
  --region us-east-1
```

#### 5.3 Monitor Costs

```bash
# Check DynamoDB usage
aws dynamodb describe-table \
  --table-name ai-cpaas-demo-rate-limits-dev \
  --region us-east-1 \
  --query 'Table.BillingModeSummary'

# Check messaging costs in Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://cost-filter.json
```

## Quick Start Commands

### Deploy Everything (Amplify)

```bash
# 1. Deploy infrastructure
cd infrastructure && ./deploy.sh

# 2. Configure AWS End User Messaging (manual in console)
# - Create phone pool
# - Set up WhatsApp Business Account
# - Verify SES email

# 3. Push to GitLab
git add . && git commit -m "Ready for deployment" && git push

# 4. Create Amplify app (manual in console)
# - Connect to GitLab
# - Configure environment variables
# - Deploy

# 5. Test
curl https://your-app-url.com/api/environment
```

### Deploy Everything (EC2)

```bash
# 1. Deploy infrastructure
cd infrastructure && ./deploy.sh

# 2. Launch EC2 instance
aws ec2 run-instances --image-id ami-xxx --instance-type t3.medium ...

# 3. SSH and setup
ssh ec2-user@<ip>
git clone <repo> && cd appliedai-cpaas
pip3 install -r requirements.txt

# 4. Configure environment
source .env.aws

# 5. Start application
bash start.sh

# 6. Test
curl http://<instance-ip>:8080/api/environment
```

## Troubleshooting

### Issue: CloudFormation stack fails

```bash
# Check stack events
aws cloudformation describe-stack-events \
  --stack-name ai-cpaas-messaging-infrastructure \
  --region us-east-1 \
  --max-items 20

# Delete and retry
aws cloudformation delete-stack \
  --stack-name ai-cpaas-messaging-infrastructure \
  --region us-east-1
```

### Issue: Amplify build fails

```bash
# Check build logs in Amplify Console
# Common issues:
# - Missing environment variables
# - Python version mismatch
# - Dependency installation failure

# Fix: Update amplify.yml with correct Python version
```

### Issue: Messages not sending

```bash
# Check IAM permissions
aws iam get-role-policy \
  --role-name ai-cpaas-demo-messaging-app-dev \
  --policy-name MessagingPolicy \
  --region us-east-1

# Check CloudWatch logs
aws logs tail /aws/lambda/ai-cpaas-demo-delivery-processor-dev \
  --follow \
  --region us-east-1

# Verify phone pool and WhatsApp account
aws pinpoint-sms-voice-v2 describe-pools --region us-east-1
```

## Cost Estimates

### Infrastructure (Monthly)
- DynamoDB: $5
- Lambda: $2
- CloudWatch: $3
- EventBridge: $1
- **Total**: ~$11/month

### Per Campaign (10,000 messages)
- WhatsApp (6,000): $30-54
- SMS (4,000): $26
- Infrastructure: $0.37
- **Total**: $56-80 per campaign

### Amplify Hosting
- Build minutes: $0.01/minute
- Hosting: $0.15/GB stored + $0.15/GB served
- **Estimate**: $5-10/month for demo

## Next Steps

1. ✅ Fix JavaScript issues (DONE)
2. ⬜ Deploy CloudFormation infrastructure
3. ⬜ Configure AWS End User Messaging
4. ⬜ Choose deployment option (Amplify or EC2)
5. ⬜ Deploy application
6. ⬜ Test with small batch
7. ⬜ Monitor and optimize

## Documentation References

- `AMPLIFY_STAGING_DEPLOYMENT.md` - Amplify deployment guide
- `TASK_17_4_1_DEPLOYMENT_GUIDE.md` - Infrastructure deployment
- `AWS_MESSAGING_IMPLEMENTATION_COMPLETE.md` - Messaging integration
- `EC2_DEPLOYMENT_GUIDE.md` - EC2 deployment guide
- `WORKSPACE_DEPLOYMENT_GUIDE.md` - Workspace deployment

## Ready to Deploy! 🚀

Choose your deployment path and follow the steps above. The infrastructure is ready, code is tested, and documentation is complete.

**Recommended**: Start with Amplify for easiest deployment and automatic CI/CD.
