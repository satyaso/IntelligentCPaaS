# AWS Amplify Staging Deployment Guide

## Overview

This guide explains how to deploy the AI-CPaaS Demo application to AWS Amplify as a staging environment while keeping the local development server unchanged.

## Architecture

### Environment Separation

- **Local Environment**: Uses local JSON files, no AWS services, runs on `localhost:5000`
- **AWS Staging**: Uses DynamoDB, AWS End User Messaging, AWS SES, deployed on Amplify with public URL

### Environment Detection

The application uses the `FLASK_ENV` environment variable to detect the environment:

```python
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production'
```

- Local: `FLASK_ENV` is not set or set to `development`
- AWS Staging: `FLASK_ENV=production`

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **GitLab Repository** with code pushed
3. **AWS Infrastructure** deployed (DynamoDB tables, IAM roles)
4. **AWS End User Messaging** configured (Phone Pool, WhatsApp Business Account)
5. **AWS SES** configured (Verified sender email)

## Deployment Steps

### 1. Prepare Infrastructure

Ensure the following AWS resources are created:

- **DynamoDB Tables**:
  - `ai-cpaas-demo-rate-limits-staging`
  - `ai-cpaas-demo-delivery-tracking-staging`

- **IAM Role**: `ai-cpaas-demo-messaging-app-staging` with permissions:
  - DynamoDB read/write
  - AWS End User Messaging send
  - AWS SES send
  - CloudWatch logs

- **AWS End User Messaging**:
  - Phone Pool ID for SMS
  - WhatsApp Business Account ID

- **AWS SES**:
  - Verified sender email address

### 2. Connect Amplify to GitLab

1. Go to AWS Amplify Console
2. Click "New app" → "Host web app"
3. Select "GitLab" as the repository service
4. Authorize AWS Amplify to access your GitLab account
5. Select your repository and branch (e.g., `main` or `staging`)

### 3. Configure Build Settings

Amplify will auto-detect the `amplify.yml` file. Verify the configuration:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - pip install -r requirements.txt
    build:
      commands:
        - python -c "from src.ai_cpaas_demo.data.data_seeder import DataSeeder; seeder = DataSeeder(); seeder.seed_all_data()"
  artifacts:
    baseDirectory: /
    files:
      - '**/*'
```

### 4. Configure Environment Variables

In Amplify Console → App Settings → Environment Variables, add:

```
FLASK_ENV=production
AWS_REGION=us-east-1
PHONE_POOL_ID=<your-phone-pool-id>
WHATSAPP_BUSINESS_ACCOUNT_ID=<your-whatsapp-business-account-id>
SENDER_EMAIL=noreply@yourdomain.com
RATE_LIMITS_TABLE=ai-cpaas-demo-rate-limits-staging
DELIVERY_TRACKING_TABLE=ai-cpaas-demo-delivery-tracking-staging
```

### 5. Configure Start Command

In Amplify Console → App Settings → Build settings → Start command:

```bash
bash start.sh
```

Or directly:

```bash
gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 "src.ai_cpaas_demo.web.app:app"
```

### 6. Deploy

1. Click "Save and deploy"
2. Amplify will:
   - Clone the repository
   - Install dependencies
   - Seed demo data
   - Start the Flask application
3. Wait for deployment to complete (5-10 minutes)
4. Access your application at the Amplify URL (e.g., `https://main.d1234567890.amplifyapp.com`)

## Features

### Local Development (Unchanged)

```bash
python run_demo_ui.py
```

- Runs on `localhost:5000`
- Uses local JSON files
- No AWS services required
- "Send Campaign" button is hidden

### AWS Staging

- Public URL provided by Amplify
- Uses DynamoDB for data storage
- Uses AWS End User Messaging for SMS/WhatsApp
- Uses AWS SES for email
- "Send Campaign" button is visible
- Rate limiting with custom TPS
- Delivery tracking

## Send Campaign Feature

### Endpoint

```
POST /api/send-campaign
```

### Request Body

```json
{
  "eligible_users": [
    {
      "customer_id": "CUST-001",
      "selected_channel": "sms",
      "phone": "+1234567890",
      "message": "Hello! Special offer for you..."
    },
    {
      "customer_id": "CUST-002",
      "selected_channel": "whatsapp",
      "phone": "+1234567891",
      "template_name": "promotion_template",
      "template_parameters": {"name": "John", "discount": "20%"}
    },
    {
      "customer_id": "CUST-003",
      "selected_channel": "email",
      "email": "customer@example.com",
      "subject": "Special Offer",
      "message": "Hello! Check out our special offer..."
    }
  ],
  "throughput_tps": 10,
  "campaign_id": "campaign-2026-01-22"
}
```

### Response

```json
{
  "success": true,
  "results": {
    "total_sent": 150,
    "total_failed": 0,
    "campaign_id": "campaign-2026-01-22",
    "by_channel": {
      "sms": {"sent": 50, "failed": 0, "total": 50},
      "whatsapp": {"sent": 75, "failed": 0, "total": 75},
      "email": {"sent": 25, "failed": 0, "total": 25}
    }
  }
}
```

## Rate Limiting

- Custom throughput (TPS) provided by user
- Single TPS value applies to all channels
- Token bucket algorithm with burst capacity
- Automatic retry with backoff

## Delivery Tracking

All sent messages are tracked in DynamoDB:

- Message ID
- Customer ID
- Channel (SMS/WhatsApp/Email)
- Destination (phone/email)
- Status (sent/delivered/failed)
- Timestamps
- Campaign ID

## Monitoring

### CloudWatch Logs

- Application logs: `/aws/amplify/<app-id>`
- Gunicorn access logs
- Error logs

### Metrics

- Total messages sent
- Success/failure rates
- Rate limiting events
- Delivery status updates

## Troubleshooting

### Issue: "Campaign sending is only available in production environment"

**Solution**: Ensure `FLASK_ENV=production` is set in Amplify environment variables.

### Issue: AWS clients not initialized

**Solution**: Check that all required environment variables are set:
- `PHONE_POOL_ID`
- `WHATSAPP_BUSINESS_ACCOUNT_ID`
- `SENDER_EMAIL`
- `AWS_REGION`

### Issue: Permission denied errors

**Solution**: Verify IAM role has correct permissions for:
- DynamoDB tables
- AWS End User Messaging
- AWS SES
- CloudWatch Logs

### Issue: Rate limiting errors

**Solution**: 
- Check throughput TPS is between 1-100
- Verify rate limiter configuration
- Check DynamoDB table exists

### Issue: Local server affected by changes

**Solution**: The local server should NOT be affected. Verify:
- `FLASK_ENV` is not set locally
- AWS clients are only initialized when `IS_PRODUCTION=True`
- Local server still uses JSON files

## Testing

### Test Local Server

```bash
python run_demo_ui.py
```

- Verify it runs on `localhost:5000`
- Verify "Send Campaign" button is hidden
- Verify campaign queries work with local data

### Test Staging Server

1. Access Amplify URL
2. Run a campaign query
3. Verify "Send Campaign" button is visible
4. Click "Send Campaign"
5. Verify messages are sent via AWS services
6. Check DynamoDB for delivery records

## Rollback

If deployment fails:

1. Go to Amplify Console
2. Click on the app
3. Go to "Deployments"
4. Find the last successful deployment
5. Click "Redeploy this version"

## Cost Optimization

- Use AWS Free Tier where possible
- Set up CloudWatch alarms for cost monitoring
- Use rate limiting to control message volume
- Monitor DynamoDB read/write capacity

## Security

- Never commit AWS credentials to Git
- Use IAM roles for AWS service access
- Rotate credentials regularly
- Enable CloudTrail for audit logging
- Use VPC for additional security (optional)

## Next Steps

1. Set up custom domain in Amplify
2. Configure SSL certificate
3. Set up CI/CD pipeline
4. Add monitoring dashboards
5. Configure auto-scaling
6. Set up staging → production promotion workflow
