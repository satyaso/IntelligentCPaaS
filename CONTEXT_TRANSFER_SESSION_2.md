# Context Transfer - Session 2: AWS End User Messaging Integration

**Date**: January 22, 2026  
**Previous Session**: Context transfer from long conversation  
**Current Focus**: Integrate AWS End User Messaging for actual SMS/WhatsApp/Email sending

---

## Current Status Summary

### ✅ What's Already Deployed (AWS Backend)
- **DynamoDB Tables**: Rate limits + Delivery tracking
- **Lambda Function**: Delivery status processor (listens to EventBridge)
- **EventBridge Rules**: SMS + WhatsApp delivery events
- **IAM Roles**: Application role + Lambda execution role
- **CloudWatch Alarms**: Throttling + delivery failure monitoring
- **SNS Topic**: Alarm notifications

**Stack**: `ai-cpaas-messaging-infrastructure` (CREATE_COMPLETE)  
**Config**: `.env.aws` with all resource ARNs

### ✅ What's Already Built (Code)
- **AWS Messaging Client**: `src/ai_cpaas_demo/messaging/aws_messaging.py`
- **Rate Limiter**: `src/ai_cpaas_demo/messaging/rate_limiter.py` (supports custom TPS)
- **Delivery Tracker**: `src/ai_cpaas_demo/messaging/delivery_tracker.py`
- **WhatsApp Templates**: `data/demo/whatsapp_templates.json` (5 templates)
- **Message Generator**: Loads templates, generates personalized messages
- **Web UI**: Flask app with campaign query functionality

### ❌ What's Missing (Need to Implement)
1. **Send Campaign Endpoint**: `/api/send-campaign` in Flask app
2. **Email Support**: AWS SES integration (separate from End User Messaging)
3. **UI Send Button**: "Send Campaign" button with throughput input
4. **Progress Tracking**: Real-time sending progress display
5. **Amplify Deployment**: Deploy Flask app to AWS Amplify

---

## Architecture Clarification

### Message Sending Flow
```
User clicks "Send Campaign" (with TPS input)
    ↓
Flask App (Amplify hosted)
    ↓
Groups users by AI-selected channel (SMS/WhatsApp/Email)
    ↓
Applies rate limiter (user's custom TPS)
    ↓
Calls AWS End User Messaging (SMS/WhatsApp) OR AWS SES (Email)
    ↓
AWS sends messages
```

### Delivery Tracking Flow (Automatic)
```
AWS End User Messaging sends message
    ↓
Message delivered/failed
    ↓
AWS emits EventBridge event
    ↓
Lambda function triggered
    ↓
Updates DynamoDB delivery tracking table
```

### Key Points
- **Lambda does NOT send messages** - only tracks delivery
- **Flask app sends directly** via AWS SDK
- **AI already selects channel** per customer (channel scoring)
- **User provides ONE throughput** (TPS) for all channels
- **Three separate functions** needed: SMS, WhatsApp, Email

---

## Design Decisions Made

### 1. Throughput Management
- **User Input**: Single "Throughput (TPS)" field in UI
- **Applied To**: All channels (SMS, WhatsApp, Email)
- **Rate Limiter**: Uses `RateLimitConfig` with custom `max_requests_per_second`
- **Example**: User sets 10 TPS → All channels throttled to 10 msg/sec

### 2. Channel Selection
- **AI-Driven**: Channel already determined by AI (channel scoring + preferences)
- **No User Choice**: User doesn't select channels - AI does
- **Campaign Results**: Already include `channel` field per user

### 3. Separate Channel Functions
```python
send_sms_messages(users, limiter)      # AWS End User Messaging
send_whatsapp_messages(users, limiter) # AWS End User Messaging  
send_email_messages(users, limiter)    # AWS SES (different API)
```

### 4. Deployment Strategy
- **Amplify**: Host entire Flask app (frontend + backend)
- **NOT using API Gateway**: Amplify serves both
- **Infrastructure**: Already deployed, only app deployment needed

---

## Implementation Plan

### Phase 1: Backend - Send Campaign Endpoint
**File**: `src/ai_cpaas_demo/web/app.py`

**Add endpoint**:
```python
@app.route('/api/send-campaign', methods=['POST'])
def send_campaign():
    # 1. Get campaign results + user's TPS
    # 2. Group users by AI-selected channel
    # 3. Create rate limiters with custom TPS
    # 4. Send via appropriate channel functions
    # 5. Track delivery in DynamoDB
    # 6. Return progress/status
```

**Create channel-specific functions**:
- `send_sms_messages()` - AWS End User Messaging SMS API
- `send_whatsapp_messages()` - AWS End User Messaging WhatsApp API
- `send_email_messages()` - AWS SES API (NEW)

### Phase 2: AWS SES Integration
**File**: `src/ai_cpaas_demo/messaging/aws_ses.py` (NEW)

**Implement**:
- SES client initialization
- Email sending with rate limiting
- Delivery tracking integration
- Template support for emails

### Phase 3: Frontend - Send Button & Progress
**File**: `src/ai_cpaas_demo/web/templates/index.html`

**Add UI elements**:
- Throughput (TPS) input field
- "Send Campaign" button
- Progress bar / status display
- Delivery statistics (sent, failed, pending)

### Phase 4: Amplify Deployment
**Files**: `amplify.yml`, `start.sh`, `requirements.txt`

**Steps**:
1. Create Amplify config files
2. Push to GitLab
3. Connect Amplify to GitLab repo
4. Configure environment variables
5. Deploy and test

---

## Technical Details

### Rate Limiter Usage
```python
from ai_cpaas_demo.messaging.rate_limiter import RateLimiter, RateLimitConfig, Channel

# User sets TPS = 10
config = RateLimitConfig(
    channel=Channel.SMS,
    max_requests_per_second=10,  # User's TPS
    burst_capacity=100,
    region="us-east-1"
)

limiter = RateLimiter(config)

# Before each send
can_send, retry_after = limiter.acquire()
if not can_send:
    time.sleep(retry_after)
```

### AWS End User Messaging Client
```python
from ai_cpaas_demo.messaging.aws_messaging import AWSEndUserMessaging

client = AWSEndUserMessaging(
    region='us-east-1',
    phone_pool_id='...',  # From AWS config
    whatsapp_account_id='...'  # From AWS config
)

# Send SMS
message_id = client.send_message(
    phone_number='+1234567890',
    message='Your message',
    channel='sms'
)

# Send WhatsApp
message_id = client.send_message(
    phone_number='+1234567890',
    message='Your message',
    channel='whatsapp',
    template_id='PROMO_HIGH_DISCOUNT'
)
```

### Delivery Tracking
```python
from ai_cpaas_demo.messaging.delivery_tracker import DeliveryTracker

tracker = DeliveryTracker(
    table_name='ai-cpaas-demo-delivery-tracking-dev',
    region='us-east-1'
)

tracker.track_message(
    message_id='msg-123',
    customer_id='CUST-456',
    channel='sms',
    phone_number='+1234567890'
)
```

---

## Environment Configuration

### Required Environment Variables (Amplify)
```bash
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=378318846552
DYNAMODB_RATE_LIMITS_TABLE=ai-cpaas-demo-rate-limits-dev
DYNAMODB_DELIVERY_TRACKING_TABLE=ai-cpaas-demo-delivery-tracking-dev
FLASK_ENV=production
PORT=8080

# AWS End User Messaging (need to configure)
PHONE_POOL_ID=<to-be-configured>
WHATSAPP_ACCOUNT_ID=<to-be-configured>
```

### AWS Permissions Needed
- `sms-voice:SendTextMessage` (SMS + WhatsApp)
- `ses:SendEmail` (Email)
- `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem` (Rate limits + Tracking)
- `cloudwatch:PutMetricData` (Metrics)

---

## Next Steps (Priority Order)

1. **Implement `/api/send-campaign` endpoint** in Flask app
2. **Create AWS SES integration** for email sending
3. **Add UI send button** with throughput input
4. **Test locally** with dry-run mode
5. **Deploy to Amplify** for public access
6. **Configure AWS End User Messaging** (Phone Pool + WhatsApp Account)
7. **Test with real messages** (small batch)

---

## Key Files to Work With

### Backend
- `src/ai_cpaas_demo/web/app.py` - Add send campaign endpoint
- `src/ai_cpaas_demo/messaging/aws_ses.py` - NEW - Email integration
- `src/ai_cpaas_demo/messaging/aws_messaging.py` - Already exists (SMS/WhatsApp)
- `src/ai_cpaas_demo/messaging/rate_limiter.py` - Already exists
- `src/ai_cpaas_demo/messaging/delivery_tracker.py` - Already exists

### Frontend
- `src/ai_cpaas_demo/web/templates/index.html` - Add send button + progress UI

### Deployment
- `amplify.yml` - NEW - Amplify build config
- `start.sh` - NEW - Gunicorn startup script
- `requirements.txt` - Add gunicorn dependency

### Configuration
- `.env.aws` - Already exists with infrastructure details
- `.env.example` - Update with new variables

---

## Important Notes

1. **Channel Selection**: AI already determines optimal channel - don't add channel selection UI
2. **Rate Limiting**: Single TPS applies to all channels, not per-channel
3. **Lambda Role**: Lambda only tracks delivery, doesn't send messages
4. **Email API**: Use AWS SES, NOT End User Messaging
5. **Dry Run Mode**: Test without actual AWS calls first
6. **WhatsApp Templates**: Must be approved by Meta before use
7. **Cost Control**: User's TPS input controls sending velocity and costs

---

## Questions to Resolve

1. **Default TPS**: What should be the default if user doesn't specify? (Suggest: 10 msg/sec)
2. **Progress Display**: Real-time updates or final summary? (Suggest: Real-time)
3. **Error Handling**: Retry failed messages or just log? (Suggest: Log + display)
4. **Batch Size**: Send all at once or in batches? (Suggest: Batches of 100)

---

## Success Criteria

- ✅ User can set custom throughput (TPS)
- ✅ Messages sent via correct channel (AI-selected)
- ✅ Rate limiting enforced (no AWS throttling)
- ✅ Delivery tracked in DynamoDB
- ✅ Progress displayed in UI
- ✅ Deployed on Amplify with public URL
- ✅ All three channels working (SMS, WhatsApp, Email)

---

**Ready to start implementation in new session!**
