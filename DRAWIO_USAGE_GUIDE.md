# Draw.io Architecture Diagram - Usage Guide

## Quick Start

### Option 1: Import XML File (Recommended)
1. Open [Draw.io](https://app.diagrams.net/) or [diagrams.net](https://www.diagrams.net/)
2. Click **File** → **Open from** → **Device**
3. Select `PRODUCTION_ARCHITECTURE_DRAWIO.xml`
4. The complete architecture diagram will load automatically

### Option 2: AWS Architecture Icons
If you want to enhance the diagram with official AWS icons:
1. In Draw.io, click **More Shapes** (bottom left)
2. Search for "AWS Architecture"
3. Enable "AWS 19" icon library
4. Drag AWS service icons onto the diagram

---

## Diagram Overview

The diagram shows the complete AWS AI-CPaaS production architecture with 5 layers:

### Layer 1: User Interface & Code Management
- **GitLab** (gitlab.aws.dev) - Internal repository
- **AWS CodeCommit** - Mirror repository for Amplify
- **AWS Amplify** - Web hosting with CI/CD

### Layer 2: THE BRAIN 🧠 - AI Intelligence
- **AI Agents**: Campaign Orchestration, Customer Protection, Cost Optimization
- **AI Engines**: Amazon Bedrock, Amazon Comprehend, ML Prediction
- **Data Layer**: Amazon Iceberg, DynamoDB, RAG Knowledge Base

### Layer 3: Integration & Orchestration
- **Amazon EventBridge** - Event routing
- **AWS Lambda** - Delivery processor
- **Amazon CloudWatch** - Monitoring and alarms

### Layer 4: THE HEART ❤️ - AWS CDS Services
- **AWS End User Messaging** - SMS + WhatsApp ($0.00645 and $0.0042 per message)
- **Amazon SES** - Email delivery ($0.10 per 1000 emails)
- **Amazon Pinpoint** - Campaign management

### Layer 5: Customer Delivery
- **Mobile Devices** - SMS delivery
- **WhatsApp** - Rich media messages
- **Email Clients** - HTML content

### Feedback Loop 🔄 (Right Side)
- **Engagement Events** - Delivered, Opened, Clicked, Replied
- **AI Learning Pipeline** - EventBridge → Lambda → Iceberg → Bedrock
- **Continuous Learning** - Feeds back to Brain layer

---

## Key Annotations

### 🔒 Technical Moat
- 12-18 months AI learning
- AWS-native integration
- $2M+ switching cost
- 40% better delivery rates

### 📊 Performance
- 98% delivery rate
- 67% open rate
- 23% click rate
- <5s latency

### 💰 Cost Optimization
- 35% cost reduction
- Smart channel selection
- Real-time optimization
- WhatsApp preferred

---

## Customization Tips

### Change Colors
1. Select a component
2. Click **Fill Color** in toolbar
3. Choose from color scheme:
   - Brain (AI): Light Blue (#E3F2FD)
   - Heart (CDS): Light Red (#FFEBEE)
   - Integration: Light Yellow (#FFF9C4)
   - Customers: Light Green (#E8F5E9)
   - Feedback: Light Purple (#F3E5F5)

### Add More Components
1. Click **+** in left sidebar
2. Search for AWS services
3. Drag onto canvas
4. Connect with arrows

### Adjust Layout
1. Select multiple components (Shift+Click)
2. Use **Arrange** menu to align
3. Use **Format** → **Spacing** to adjust gaps

---

## Export Options

### For Presentations
1. **File** → **Export as** → **PNG**
2. Set resolution: 300 DPI
3. Check "Transparent Background" if needed
4. Use for PowerPoint, Keynote, Google Slides

### For Documentation
1. **File** → **Export as** → **PDF**
2. Include all pages
3. Embed in technical docs

### For Web
1. **File** → **Export as** → **SVG**
2. Scalable vector format
3. Use in web pages, wikis

---

## Partner Demo Tips

### Highlight the Moat
1. Zoom into **Layer 2 (Brain)** and **Layer 4 (Heart)**
2. Show the **Feedback Loop** on the right
3. Point to **Technical Moat** annotation
4. Explain: "AI learns from AWS CDS delivery data - 12-18 months of intelligence"

### Show Data Flow
1. Start at **Layer 1** (User creates campaign)
2. Follow arrows down through **Brain** (AI decides)
3. Through **Integration** (EventBridge triggers)
4. To **Heart** (CDS delivers)
5. To **Customers** (Messages received)
6. Back up **Feedback Loop** (AI learns)

### Emphasize Cost Savings
1. Point to **Cost Optimization** annotation
2. Show **AWS End User Messaging** pricing
3. Explain: "35% cost reduction through smart channel selection"
4. Compare: WhatsApp ($0.0042) vs SMS ($0.00645)

---

## Diagram Dimensions

- **Canvas Size**: 1200px × 1800px
- **Layer Heights**:
  - Layer 1: 150px
  - Layer 2 (Brain): 350px
  - Layer 3: 150px
  - Layer 4 (Heart): 250px
  - Layer 5: 150px
  - Feedback Loop: 400px (vertical)

---

## Troubleshooting

### Diagram Doesn't Load
- Ensure you're using Draw.io or diagrams.net (not other tools)
- Try opening in incognito/private mode
- Clear browser cache

### Components Overlap
- Use **Arrange** → **Layout** → **Vertical Flow**
- Manually adjust spacing
- Use grid (View → Grid)

### Missing Icons
- Enable AWS icon library: **More Shapes** → Search "AWS"
- Download AWS Architecture Icons separately if needed

---

## Next Steps

1. **Import the diagram** into Draw.io
2. **Customize** with your specific details (account IDs, regions)
3. **Export** as PNG for presentations
4. **Share** with partners and stakeholders
5. **Update** as architecture evolves

---

## Related Documents

- `AWS_CDS_TECHNICAL_MOAT.md` - Technical moat strategy
- `CDS_REVENUE_MOAT_STRATEGY.md` - Revenue moat strategy
- `AI_BRAIN_HEART_ARCHITECTURE.md` - Architecture explanation
- `.env.aws` - Deployed infrastructure configuration

---

**Pro Tip**: Keep this diagram updated as you add new AWS services or features. It's your visual story of the technical moat!
