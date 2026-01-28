# AI-CPaaS Demo - Amazon Workspace Deployment Guide

**Target Environment**: Amazon Workspace (WS) Instance  
**Deployment Time**: 15-20 minutes  
**Access**: Internal network access via browser

---

## Overview

This guide shows you how to deploy and run the AI-CPaaS demo on your Amazon Workspace instance, making it accessible via your internal network.

---

## Prerequisites

### 1. Check Your Workspace Environment

```bash
# Check Python version (need 3.9+)
python3 --version

# Check if pip is installed
pip3 --version

# Check AWS CLI
aws --version
```

### 2. Verify AWS Credentials

```bash
# Check AWS credentials are configured
aws sts get-caller-identity

# Should show your AWS account and user info
```

### 3. Check Network Access

Your Workspace should have:
- ✅ Access to AWS services (DynamoDB, End User Messaging)
- ✅ Ability to run web servers on localhost
- ✅ Browser access (Chrome, Firefox, or Edge)

---

## Deployment Steps

### Step 1: Navigate to Project Directory

```bash
# You should already be in the project directory
pwd
# Should show: /Users/satyaso/work/code-dev/appliedai-cpaas

# If not, navigate there:
cd /Users/satyaso/work/code-dev/appliedai-cpaas
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Or use the Makefile
make install
```

**Expected output**: All packages installed successfully

### Step 3: Verify AWS Infrastructure

Your CloudFormation stack is already deployed. Verify it's running:

```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name ai-cpaas-messaging-infrastructure \
  --query 'Stacks[0].StackStatus'

# Should return: "CREATE_COMPLETE"
```

### Step 4: Configure Environment

Your `.env.aws` file is already configured with the deployed infrastructure:

```bash
# Verify configuration exists
cat .env.aws

# Should show:
# - DynamoDB table names
# - AWS region
# - Application role ARN
```

### Step 5: Seed Demo Data

```bash
# Run the data seeder to populate demo data
python3 -c "
from src.ai_cpaas_demo.data.data_seeder import DataSeeder
seeder = DataSeeder()
seeder.seed_all()
print('✅ Demo data seeded successfully!')
"
```

**What this does**:
- Creates 1000+ customer profiles
- Loads WhatsApp templates
- Sets up campaign scenarios
- Initializes promotion data

### Step 6: Start the Web UI

```bash
# Option 1: Using the run script
python3 run_demo_ui.py

# Option 2: Using the Makefile
make run-demo

# Option 3: Direct Flask command
python3 -m flask --app src.ai_cpaas_demo.web.app run --host=0.0.0.0 --port=5000
```

**Expected output**:
```
 * Serving Flask app 'src.ai_cpaas_demo.web.app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

### Step 7: Access the Demo

Open your browser on the Workspace and navigate to:

```
http://localhost:5000
```

**You should see**: The AI-CPaaS Demo UI with the campaign builder interface

---

## Using the Demo

### Quick Test Scenario

1. **Select a Campaign Scenario**:
   - Choose "Flash Sale - Electronics" from the dropdown
   - Click "Load Scenario"

2. **Build Your Segment**:
   - Add dimension: `purchase_history.category = Electronics`
   - Add dimension: `engagement_score > 70`
   - Click "Preview Segment"

3. **Review AI Recommendations**:
   - See predicted engagement rates
   - View channel mix optimization
   - Check cost estimates
   - Review fatigue protection rules

4. **Generate Messages**:
   - Click "Generate Messages"
   - See personalized messages for each channel
   - View WhatsApp template IDs
   - Check message variables

5. **Execute Campaign** (Optional):
   - Click "Execute Campaign"
   - Messages will be sent via AWS End User Messaging
   - View delivery tracking in real-time

---

## Accessing from Other Machines (Optional)

If you want to access the demo from other machines on your network:

### Option 1: Use Your Workspace IP

```bash
# Find your Workspace IP
hostname -I | awk '{print $1}'

# Start server with external access
python3 run_demo_ui.py --host=0.0.0.0 --port=5000
```

Then access from other machines:
```
http://<your-workspace-ip>:5000
```

### Option 2: Use SSH Tunnel (More Secure)

From your local machine:
```bash
# Create SSH tunnel to your Workspace
ssh -L 5000:localhost:5000 satyaso@<workspace-hostname>

# Then access on your local machine:
# http://localhost:5000
```

---

## Running Tests

### Quick Validation Test

```bash
# Run quick demo test
python3 test_demo_quick.py
```

**Expected output**: All tests pass ✅

### Full Test Suite

```bash
# Run all tests
make test

# Or manually:
pytest tests/ -v
```

### Test AWS Messaging Integration

```bash
# Test AWS End User Messaging
python3 example_aws_messaging.py
```

**Expected output**: 
- Rate limiter initialized
- Test messages sent successfully
- Delivery tracking working

---

## Troubleshooting

### Issue 1: Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port
python3 run_demo_ui.py --port=5001
```

### Issue 2: AWS Credentials Not Found

**Error**: `Unable to locate credentials`

**Solution**:
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### Issue 3: Module Not Found

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall
```

### Issue 4: DynamoDB Access Denied

**Error**: `AccessDeniedException`

**Solution**:
```bash
# Check your IAM permissions
aws iam get-user

# Verify you have DynamoDB permissions
aws dynamodb list-tables
```

### Issue 5: Browser Can't Connect

**Error**: Browser shows "Can't reach this page"

**Solution**:
```bash
# Check if server is running
ps aux | grep python

# Check firewall rules (if applicable)
# Ensure port 5000 is not blocked

# Try accessing with explicit IP
curl http://127.0.0.1:5000
```

---

## Performance Optimization

### For Better Performance on Workspace

1. **Use Production Mode**:
```bash
# Set Flask to production mode
export FLASK_ENV=production
python3 run_demo_ui.py
```

2. **Increase Workers** (if using Gunicorn):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 src.ai_cpaas_demo.web.app:app
```

3. **Enable Caching**:
```bash
# Add to .env.aws
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300
```

---

## Monitoring and Logs

### View Application Logs

```bash
# Logs are printed to console by default
# To save to file:
python3 run_demo_ui.py > app.log 2>&1
```

### Monitor AWS Resources

```bash
# Check DynamoDB table status
aws dynamodb describe-table \
  --table-name ai-cpaas-rate-limits \
  --query 'Table.TableStatus'

# View CloudWatch alarms
aws cloudwatch describe-alarms \
  --alarm-names ai-cpaas-sms-throttling \
  --query 'MetricAlarms[0].StateValue'
```

### Check Delivery Tracking

```bash
# Query delivery tracking table
aws dynamodb scan \
  --table-name ai-cpaas-delivery-tracking \
  --max-items 10
```

---

## Stopping the Demo

### Stop the Web Server

```bash
# Press Ctrl+C in the terminal where the server is running

# Or find and kill the process
ps aux | grep "run_demo_ui"
kill <PID>
```

### Clean Up (Optional)

```bash
# Clear demo data (keeps infrastructure)
python3 -c "
from src.ai_cpaas_demo.data.data_seeder import DataSeeder
seeder = DataSeeder()
seeder.clear_all()
print('✅ Demo data cleared')
"
```

---

## Quick Reference Commands

```bash
# Start demo
python3 run_demo_ui.py

# Run tests
python3 test_demo_quick.py

# Check AWS infrastructure
aws cloudformation describe-stacks --stack-name ai-cpaas-messaging-infrastructure

# View logs
tail -f app.log

# Stop demo
# Press Ctrl+C
```

---

## Demo Features Available

When running on your Workspace, you have access to:

### ✅ Core Features
- **Intelligent Segmentation**: Multi-dimensional customer queries
- **AI Predictions**: Engagement scoring and channel optimization
- **Message Generation**: Personalized messages with WhatsApp templates
- **Cost Optimization**: Real-time cost calculations
- **Fatigue Protection**: Automatic suppression rules

### ✅ AWS Integration
- **End User Messaging**: Send SMS and WhatsApp messages
- **Rate Limiting**: Intelligent throttling (80 msg/sec WhatsApp, 20 msg/sec SMS)
- **Delivery Tracking**: Real-time delivery status monitoring
- **CloudWatch Alarms**: Automatic alerts for throttling and failures

### ✅ Demo Data
- **1000+ Customers**: Realistic customer profiles
- **5 WhatsApp Templates**: Pre-approved message templates
- **Campaign Scenarios**: Pre-built campaign examples
- **Product Promotions**: RAG-based promotion data

---

## Next Steps

### 1. Explore the Demo
- Try different campaign scenarios
- Experiment with segmentation queries
- Generate messages for different channels
- Review AI recommendations

### 2. Customize for Your Use Case
- Add your own customer data
- Create custom WhatsApp templates
- Define your own campaign scenarios
- Adjust cost parameters

### 3. Integrate with Your Systems
- Connect to your customer database
- Integrate with your CRM
- Add custom analytics
- Extend with additional channels

### 4. Deploy to Production
- See `AWS_HOSTED_DEPLOYMENT_GUIDE.md` for production deployment
- Set up CI/CD pipelines
- Configure monitoring and alerting
- Scale infrastructure as needed

---

## Support and Documentation

### Key Documentation Files
- `README.md` - Project overview
- `DEMO_QUICK_START.md` - Quick start guide
- `AWS_MESSAGING_README.md` - AWS integration details
- `ROI_ANALYSIS_1M_USERS.md` - Cost savings analysis
- `DEPLOYMENT_SUCCESS.md` - Infrastructure deployment status

### Getting Help
- Check troubleshooting section above
- Review CloudWatch logs for AWS issues
- Check application logs for runtime errors
- Verify AWS credentials and permissions

---

## Summary

Your AI-CPaaS demo is ready to run on your Amazon Workspace:

1. ✅ **Install dependencies**: `pip3 install -r requirements.txt`
2. ✅ **Seed demo data**: Run data seeder
3. ✅ **Start web UI**: `python3 run_demo_ui.py`
4. ✅ **Access demo**: `http://localhost:5000`
5. ✅ **Test features**: Try campaign scenarios

**Estimated setup time**: 15-20 minutes  
**Access**: Browser on your Workspace  
**AWS Integration**: Fully functional with deployed infrastructure

🚀 **You're ready to showcase the AI-CPaaS demo on your Workspace!**
