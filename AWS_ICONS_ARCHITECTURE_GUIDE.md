# AWS Architecture Diagram with Official Icons - Build Guide

## Overview

This guide shows how to create a professional AWS architecture diagram using official AWS service icons in Draw.io, maintaining the Brain-Heart layer separation and including the complete feedback loop.

---

## Step 1: Enable AWS Icon Library in Draw.io

1. Open [Draw.io](https://app.diagrams.net/)
2. Click **More Shapes** (bottom left)
3. Search for "AWS"
4. Enable these libraries:
   - ✅ **AWS 19** (Latest AWS icons)
   - ✅ **AWS 17** (Additional icons)
5. Click **Apply**

The AWS icon library will appear in the left sidebar.

---

## Step 2: Canvas Setup

1. **File** → **New Diagram**
2. Set canvas size: **1400px width × 2000px height**
3. Enable grid: **View** → **Grid** (10px)
4. Enable guides: **View** → **Guides**

---

## Step 3: Layer 1 - User Interface & Code Management

### Container
- Draw rectangle: 1300px × 180px
- Fill: Light Gray (#F5F5F5)
- Border: Gray (#9E9E9E), 2px
- Label: "LAYER 1: USER INTERFACE & CODE MANAGEMENT"

### Components (Left to Right)

#### 1. GitLab (Custom Icon)
- Rectangle: 200px × 100px
- Fill: Orange (#FF9800)
- Icon: Add GitLab logo or text "GitLab"
- Label: "GitLab\ngitlab.aws.dev\nInternal Repository"
- Position: x=100, y=100

#### 2. AWS CodeCommit
- **AWS Icon**: Search "CodeCommit" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "AWS CodeCommit\nMirror Repository\nAuto-sync"
- Position: x=400, y=100

#### 3. AWS Amplify
- **AWS Icon**: Search "Amplify" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "AWS Amplify\nWeb Hosting\nCI/CD Pipeline"
- Position: x=700, y=100

### Connections
- GitLab → CodeCommit: Arrow, label "Mirror Push"
- CodeCommit → Amplify: Arrow, label "Auto Deploy"

---

## Step 4: Layer 2 - THE BRAIN 🧠 (AI Intelligence)

### Container
- Draw rectangle: 1300px × 400px
- Fill: Light Blue (#E3F2FD)
- Border: Blue (#1976D2), 3px
- Label: "LAYER 2: THE BRAIN 🧠 - AI INTELLIGENCE LAYER"
- Position: y=250

### Section 2A: AI Agents (Left Column)

#### 1. Campaign Orchestration Agent
- Rectangle: 180px × 90px
- Fill: Purple (#9C27B0)
- Icon: 🤖 emoji or robot icon
- Label: "Campaign Orchestration\nCoordinates workflow"
- Position: x=100, y=320

#### 2. Customer Protection Agent
- Rectangle: 180px × 90px
- Fill: Purple (#9C27B0)
- Icon: 🛡️ emoji or shield icon
- Label: "Customer Protection\nSentiment + Fatigue"
- Position: x=100, y=430

#### 3. Cost Optimization Agent
- Rectangle: 180px × 90px
- Fill: Purple (#9C27B0)
- Icon: 💰 emoji or dollar icon
- Label: "Cost Optimization\nChannel selection"
- Position: x=100, y=540

### Section 2B: AI Engines (Center Column)

#### 1. Amazon Bedrock
- **AWS Icon**: Search "Bedrock" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "Amazon Bedrock\nClaude 3 Sonnet\nAI Message Generation"
- Position: x=380, y=320

#### 2. Amazon Comprehend
- **AWS Icon**: Search "Comprehend" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "Amazon Comprehend\nSentiment Analysis\nEmotion Detection"
- Position: x=380, y=430

#### 3. ML Prediction Engine
- **AWS Icon**: Search "SageMaker" in AWS library (use as ML icon)
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "ML Prediction Engine\nChannel Optimization\nFatigue Detection"
- Position: x=380, y=540

### Section 2C: Data Layer (Right Column)

#### 1. Amazon Iceberg (S3 + Athena)
- **AWS Icon**: Search "S3" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "🏔️ Amazon Iceberg\nCustomer Data Lake\n1000+ profiles\n12-18 months history"
- Position: x=660, y=320

#### 2. DynamoDB
- **AWS Icon**: Search "DynamoDB" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "DynamoDB\nSegments + Rate Limits\nrate-limits table\ndelivery-tracking table"
- Position: x=660, y=430

#### 3. RAG Knowledge Base
- **AWS Icon**: Search "OpenSearch" or "Elasticsearch" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "📚 RAG Knowledge Base\nPromotions + SKUs\nVector embeddings\nSemantic search"
- Position: x=660, y=540

### Internal Connections
- AI Agents ↔ AI Engines: Bidirectional dashed arrows
- AI Engines ↔ Data Layer: Bidirectional dashed arrows
- Color: Blue (#1976D2)

### Annotation Box (Top Right)
- Rectangle: 280px × 140px
- Fill: Light Yellow (#FFF9C4)
- Border: Orange (#F57C00)
- Position: x=950, y=320
- Text:
```
🔒 TECHNICAL MOAT
━━━━━━━━━━━━━━━━━━
• 12-18 months AI learning
• AWS-native integration
• $2M+ switching cost
• 40% better delivery rates
```

---

## Step 5: Layer 3 - Integration & Orchestration

### Container
- Draw rectangle: 1300px × 180px
- Fill: Light Yellow (#FFF9C4)
- Border: Orange (#F57C00), 2px
- Label: "LAYER 3: INTEGRATION & ORCHESTRATION LAYER"
- Position: y=700

### Components (Left to Right)

#### 1. Amazon EventBridge
- **AWS Icon**: Search "EventBridge" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "Amazon EventBridge\nEvent Routing\nReal-time events\nDelivery tracking"
- Position: x=200, y=750

#### 2. AWS Lambda
- **AWS Icon**: Search "Lambda" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "AWS Lambda\nDelivery Processor\nEvent handler\nai-cpaas-demo-delivery-processor-dev"
- Position: x=500, y=750

#### 3. Amazon CloudWatch
- **AWS Icon**: Search "CloudWatch" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text below: "Amazon CloudWatch\nMonitoring + Alarms\nCost tracking\nPerformance metrics"
- Position: x=850, y=750

### Connections
- Brain Layer → EventBridge: Thick arrow, label "AI Decisions"
- EventBridge → Lambda: Arrow, label "Trigger"
- Lambda → CloudWatch: Arrow, label "Metrics"

---

## Step 6: Layer 4 - THE HEART ❤️ (AWS CDS Services)

### Container
- Draw rectangle: 1300px × 280px
- Fill: Light Red (#FFEBEE)
- Border: Red (#D32F2F), 3px
- Label: "LAYER 4: THE HEART ❤️ - AWS CDS SERVICES"
- Position: y=930

### Components (Left to Right)

#### 1. AWS End User Messaging
- **AWS Icon**: Search "Pinpoint" in AWS library (use for messaging)
- Drag icon to canvas
- Resize: 80px × 80px
- Add text box below:
```
AWS End User Messaging
SMS + WhatsApp
━━━━━━━━━━━━━━━━━━
📱 SMS: $0.00645/msg
💬 WhatsApp: $0.0042/msg
Template management
Delivery tracking
```
- Position: x=150, y=1000

#### 2. Amazon SES
- **AWS Icon**: Search "SES" or "Simple Email Service" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text box below:
```
Amazon SES
Email Delivery
━━━━━━━━━━━━━━━━━━
📧 Email: $0.10/1000
HTML support
Bounce handling
Rich content
```
- Position: x=500, y=1000

#### 3. Amazon Pinpoint
- **AWS Icon**: Search "Pinpoint" in AWS library
- Drag icon to canvas
- Resize: 80px × 80px
- Add text box below:
```
Amazon Pinpoint
Campaign Management
━━━━━━━━━━━━━━━━━━
Multi-channel
Analytics
Journey orchestration
A/B testing
```
- Position: x=850, y=1000

### Connections
- Lambda → All CDS Services: Thick arrows, label "Send Messages"
- Color: Red (#D32F2F)

---

## Step 7: Layer 5 - Customer Delivery

### Container
- Draw rectangle: 1300px × 180px
- Fill: Light Green (#E8F5E9)
- Border: Green (#388E3C), 2px
- Label: "LAYER 5: CUSTOMER DELIVERY"
- Position: y=1260

### Components (Left to Right)

#### 1. Mobile Devices (SMS)
- Icon: 📱 emoji or phone icon
- Rectangle: 200px × 100px
- Fill: Green (#4CAF50)
- Label: "📱 Mobile Devices\nSMS\n160 char messages\nGlobal delivery"
- Position: x=200, y=1310

#### 2. WhatsApp
- Icon: 💬 emoji or WhatsApp logo
- Rectangle: 200px × 100px
- Fill: Green (#4CAF50)
- Label: "💬 WhatsApp\nRich Media\nTemplates + Buttons\nInteractive messages"
- Position: x=500, y=1310

#### 3. Email Clients
- Icon: 📧 emoji or email icon
- Rectangle: 200px × 100px
- Fill: Green (#4CAF50)
- Label: "📧 Email Clients\nHTML Content\nRich formatting\nAttachments"
- Position: x=850, y=1310

### Connections
- CDS Services → Customer Endpoints: Thick arrows, label "Deliver"
- Color: Green (#388E3C)

---

## Step 8: Feedback Loop 🔄 (RIGHT SIDE - CRITICAL!)

### Container
- Draw rectangle: 300px × 600px
- Fill: Light Purple (#F3E5F5)
- Border: Purple (#7B1FA2), 2px
- Label: "FEEDBACK LOOP 🔄"
- Position: x=1450, y=1260

### Component 1: Engagement Events

#### Customer Engagement Tracking
- Rectangle: 260px × 180px
- Fill: Purple (#9C27B0)
- Position: x=1470, y=1310
- Text:
```
📈 Engagement Events
━━━━━━━━━━━━━━━━━━
Channel Event Reports:
• Delivered ✓
• Opened 👁️
• Clicked 🖱️
• Replied 💬
• Bounced ⚠️
• Unsubscribed ❌
• Failed ✗
```

### Component 2: AI Learning Pipeline

#### Processing Pipeline
- Rectangle: 260px × 220px
- Fill: Purple (#9C27B0)
- Position: x=1470, y=1520
- Text:
```
🔄 AI Learning Pipeline
━━━━━━━━━━━━━━━━━━
1. EventBridge capture
   (delivery events)
2. Lambda processing
   (event transformation)
3. Iceberg storage
   (historical data)
4. Bedrock training
   (model improvement)
5. Comprehend analysis
   (sentiment learning)
```

### Feedback Loop Connections (CRITICAL!)

#### 1. Customers → Engagement Events
- **Source**: Customer Delivery layer (all 3 endpoints)
- **Target**: Engagement Events box
- **Arrow**: Dashed, Purple (#9C27B0), 2px
- **Label**: "User Actions\n(Opens, Clicks, Replies)"
- **Path**: Curve from customers upward to feedback box

#### 2. Engagement Events → EventBridge
- **Source**: Engagement Events box
- **Target**: EventBridge (Layer 3)
- **Arrow**: Solid, Purple (#9C27B0), 2px
- **Label**: "Channel Events"
- **Path**: Horizontal arrow left

#### 3. EventBridge → Learning Pipeline
- **Source**: EventBridge
- **Target**: AI Learning Pipeline box
- **Arrow**: Solid, Purple (#9C27B0), 2px
- **Label**: "Process Events"
- **Path**: Curve from EventBridge to learning pipeline

#### 4. Learning Pipeline → Brain Layer
- **Source**: AI Learning Pipeline box
- **Target**: Brain Layer (Layer 2) - specifically Bedrock & Comprehend
- **Arrow**: Thick dashed, Purple (#9C27B0), 3px
- **Label**: "Continuous Learning\n(Model Updates)"
- **Path**: Curve upward from learning pipeline to Brain layer
- **Note**: This completes the loop!

---

## Step 9: Additional Annotations

### Performance Metrics (Bottom Left)
- Rectangle: 280px × 140px
- Fill: Light Yellow (#FFF9C4)
- Border: Orange (#F57C00)
- Position: x=100, y=1500
- Text:
```
📊 PERFORMANCE
━━━━━━━━━━━━━━
• 98% delivery rate
• 67% open rate
• 23% click rate
• <5s latency
• Real-time tracking
```

### Cost Optimization (Bottom Center)
- Rectangle: 280px × 140px
- Fill: Light Green (#E8F5E9)
- Border: Green (#388E3C)
- Position: x=500, y=1500
- Text:
```
💰 COST OPTIMIZATION
━━━━━━━━━━━━━━━━━━
• 35% cost reduction
• Smart channel selection
• Real-time optimization
• WhatsApp preferred
• ROI: 3.2x
```

---

## Step 10: Data Flow Labels

Add text labels to show the complete flow:

### 1. Brain → Integration
- Position: Between Layer 2 and Layer 3
- Text: "Intelligent Decisions"
- Font: Bold, 14pt, Blue (#1976D2)

### 2. Integration → Heart
- Position: Between Layer 3 and Layer 4
- Text: "Orchestrated Delivery"
- Font: Bold, 14pt, Orange (#FF9800)

### 3. Heart → Customers
- Position: Between Layer 4 and Layer 5
- Text: "Personalized Messages"
- Font: Bold, 14pt, Red (#D32F2F)

### 4. Customers → Feedback
- Position: From Layer 5 to Feedback Loop
- Text: "Engagement Feedback"
- Font: Bold, 14pt, Purple (#9C27B0)

### 5. Feedback → Brain
- Position: From Feedback Loop back to Layer 2
- Text: "Continuous AI Learning"
- Font: Bold, 14pt, Purple (#9C27B0)

---

## AWS Service Icons Reference

### Layer 1 (User Interface)
- CodeCommit: `AWS Developer Tools > CodeCommit`
- Amplify: `AWS Front-End Web & Mobile > Amplify`

### Layer 2 (Brain - AI)
- Bedrock: `AWS Machine Learning > Bedrock`
- Comprehend: `AWS Machine Learning > Comprehend`
- SageMaker: `AWS Machine Learning > SageMaker` (for ML Prediction)
- S3: `AWS Storage > S3` (for Iceberg)
- DynamoDB: `AWS Database > DynamoDB`
- OpenSearch: `AWS Analytics > OpenSearch` (for RAG)

### Layer 3 (Integration)
- EventBridge: `AWS Application Integration > EventBridge`
- Lambda: `AWS Compute > Lambda`
- CloudWatch: `AWS Management & Governance > CloudWatch`

### Layer 4 (Heart - CDS)
- Pinpoint: `AWS Customer Engagement > Pinpoint` (for End User Messaging)
- SES: `AWS Customer Engagement > SES`

---

## Color Palette

```
Layer 1 (User Interface):
- Background: #F5F5F5 (Light Gray)
- Border: #9E9E9E (Gray)
- Text: #212121 (Dark Gray)

Layer 2 (Brain - AI):
- Background: #E3F2FD (Light Blue)
- Border: #1976D2 (Blue)
- Components: #9C27B0 (Purple - Agents), #1565C0 (Dark Blue - Engines), #388E3C (Green - Data)

Layer 3 (Integration):
- Background: #FFF9C4 (Light Yellow)
- Border: #F57C00 (Orange)
- Components: #FF9800 (Orange)

Layer 4 (Heart - CDS):
- Background: #FFEBEE (Light Red)
- Border: #D32F2F (Red)
- Components: #D32F2F (Red)

Layer 5 (Customers):
- Background: #E8F5E9 (Light Green)
- Border: #388E3C (Green)
- Components: #4CAF50 (Green)

Feedback Loop:
- Background: #F3E5F5 (Light Purple)
- Border: #7B1FA2 (Purple)
- Components: #9C27B0 (Purple)
```

---

## Export Settings

### For Presentations
1. **File** → **Export as** → **PNG**
2. Settings:
   - Resolution: 300 DPI
   - Transparent Background: No
   - Border Width: 10px
   - Size: Fit to content

### For Documentation
1. **File** → **Export as** → **PDF**
2. Settings:
   - Include: All pages
   - Crop: No
   - Embed fonts: Yes

### For Web
1. **File** → **Export as** → **SVG**
2. Settings:
   - Embed images: Yes
   - Include: All layers

---

## Key Improvements Over Previous Diagram

1. ✅ **Official AWS Icons**: Professional AWS service icons instead of generic rectangles
2. ✅ **Complete Feedback Loop**: Channel event reports flow back to intelligence layer
3. ✅ **Event Tracking**: Detailed engagement events (Delivered, Opened, Clicked, Replied, Bounced, Unsubscribed, Failed)
4. ✅ **Learning Pipeline**: Shows how events feed back to Bedrock and Comprehend
5. ✅ **Continuous Learning**: Visual representation of AI improvement cycle
6. ✅ **Layer Separation**: Maintains clear Brain-Heart architecture
7. ✅ **Professional Look**: AWS-standard diagram style

---

## Partner Demo Flow with Feedback Loop

### 1. Start at User Interface
"Campaign creation begins here - GitLab for code, Amplify for hosting."

### 2. Show the Brain (AI Intelligence)
"AI Agents analyze data, AI Engines make predictions, Data Layer stores intelligence."

### 3. Highlight Integration
"EventBridge routes events, Lambda processes, CloudWatch monitors."

### 4. Emphasize the Heart (CDS)
"AWS CDS services deliver messages - SMS, WhatsApp, Email."

### 5. Follow to Customers
"Messages reach customers on their preferred channels."

### 6. **CRITICAL: Show Feedback Loop**
"Here's the magic - every customer action (open, click, reply) flows back through EventBridge to the AI Learning Pipeline. This data goes into Iceberg, trains Bedrock models, and improves Comprehend sentiment analysis. The AI gets smarter with every message!"

### 7. Complete the Circle
"This continuous learning loop is the MOAT - 12-18 months of intelligence that can't be transferred to competitors."

---

## Next Steps

1. ✅ Open Draw.io
2. ✅ Enable AWS icon libraries
3. ✅ Follow this guide step-by-step
4. ✅ Pay special attention to the Feedback Loop (Step 8)
5. ✅ Export as PNG for presentations
6. ✅ Use in partner demos to show complete intelligence cycle

---

**Pro Tip**: The feedback loop is what makes this architecture special. Make sure the arrows clearly show:
- Customer actions → Engagement Events
- Engagement Events → EventBridge
- EventBridge → Learning Pipeline
- Learning Pipeline → Brain (Bedrock & Comprehend)

This visual representation of continuous learning is your competitive advantage!
