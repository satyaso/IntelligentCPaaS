# Demo Data Generation

This module generates realistic customer profiles and demo scenarios for the AI-CPaaS demonstration.

## Generated Data

### Customer Profiles (Task 13.1 ✅)

Successfully generated **1000+ unique customer profiles** with:

#### Profile Distribution
- **High-value customers**: ~23% (229 profiles)
  - Prefer email and voice channels
  - Lower communication frequency limits
  - Fewer support tickets
  - Lower fatigue levels

- **Medium-value customers**: ~66% (658 profiles)
  - Prefer WhatsApp and email
  - Moderate communication frequency
  - Average support ticket volume
  - Moderate fatigue levels

- **Low-value customers**: ~11% (113 profiles)
  - Prefer SMS and WhatsApp
  - Higher communication frequency tolerance
  - More support tickets
  - Higher fatigue levels

#### Data Characteristics

**Engagement History** (6 months):
- High-value: 40-80 interactions per customer
- Medium-value: 20-50 interactions per customer
- Low-value: 10-30 interactions per customer

**Sentiment Distribution**:
- Positive: ~80%
- Neutral: ~15%
- Negative: ~5%

**Support Tickets**:
- Total: 3,060 tickets across all customers
- Negative sentiment: ~28% (858 tickets)
- Categories: billing, technical, complaint, feature_request, account

**Fatigue Levels**:
- Low: 63.5%
- Medium: 23.7%
- High: 12.8%

**Channel Preferences**:
- Each customer has preferences for all 4 channels (SMS, WhatsApp, Email, Voice)
- Preference scores range from 0.0 to 1.0
- Includes engagement counts and last engagement timestamps

**Disengagement Signals**:
- Types: low_engagement, unsubscribe, spam_report, bounce, no_response
- Severity scores from 0.0 to 1.0
- Distributed across different channels

## Usage

### Generate Customer Profiles

```python
from ai_cpaas_demo.data import CustomerProfileGenerator

# Generate 1000 profiles
generator = CustomerProfileGenerator(seed=42)
profiles = generator.generate_profiles(count=1000)

# Access profile data
for profile in profiles:
    print(f"Customer {profile.external_id}")
    print(f"  Fatigue Level: {profile.fatigue_level}")
    print(f"  Support Tickets: {len(profile.support_tickets)}")
    print(f"  Preferred Channel: {profile.channel_preferences[0].channel}")
```

### Generate Customer Profiles

```bash
python3 -m src.ai_cpaas_demo.data.generate_demo_data
```

This will:
1. Generate 1000 customer profiles
2. Display distribution statistics
3. Save to `data/demo/customer_profiles.json` (~15MB)

### Generate Campaign Scenarios

```bash
python3 -m src.ai_cpaas_demo.data.generate_campaign_data
```

This will:
1. Generate 8 campaign scenarios (promotional, transactional, support recovery)
2. Display budget and channel analysis
3. Save to `data/demo/campaign_scenarios.json` (~19KB)

### Use Campaign Scenarios in Code

```python
from ai_cpaas_demo.data import CampaignScenarioGenerator

# Generate all scenarios
generator = CampaignScenarioGenerator()
campaigns = generator.generate_all_scenarios()

# Access specific campaign types
promotional = campaigns["promotional"]
transactional = campaigns["transactional"]
support_recovery = campaigns["support_recovery"]

# Use a specific campaign
black_friday = promotional[0]
print(f"Campaign: {black_friday.name}")
print(f"Budget: ${black_friday.budget_impact.total_cost:,.2f}")
print(f"Savings: ${black_friday.budget_impact.savings_vs_spray_pray:,.2f}")
```

### Generate Demo Presentation Scenarios

```bash
python3 -m src.ai_cpaas_demo.data.generate_demo_scenarios
```

This will:
1. Load 1000 customer profiles
2. Generate 5 demo scenarios (before/after AI comparisons)
3. Create detailed story flows for presentations
4. Save to `data/demo/demo_scenarios.json` (~563KB)

### Use Demo Scenarios in Code

```python
from ai_cpaas_demo.data import DemoScenarioGenerator, CustomerProfileGenerator

# Load customer profiles
customer_gen = CustomerProfileGenerator(seed=42)
profiles = customer_gen.generate_profiles(count=1000)

# Generate scenarios
scenario_gen = DemoScenarioGenerator(profiles)
scenarios = scenario_gen.generate_all_scenarios()

# Access specific scenarios
spray_and_pray = scenarios["spray_and_pray_problem"]
ai_solution = scenarios["ai_orchestrated_solution"]
cost_savings = scenarios["cost_savings_demo"]

# Display story flow
for step in spray_and_pray.story_flow:
    print(step)
```

## Data Files

- `customer_profiles.json`: 1000 customer profiles with complete history (~15MB)
- `campaign_scenarios.json`: 8 campaign scenarios with budget analysis (~19KB)
- `demo_scenarios.json`: 5 presentation scenarios with before/after comparisons (~563KB)
- Format: JSON with ISO datetime strings

### Campaign Scenarios (Task 13.2 ✅)

Successfully generated **8 campaign scenarios** across 3 categories:

#### Campaign Distribution

**Promotional Campaigns** (3 scenarios):
- Black Friday Flash Sale
  - Target: high-value and medium-value customers
  - Budget: $50,000 | Savings: $15,000 (30%)
  - Channels: SMS, WhatsApp, Email, Voice
  - ROI: 450%

- New Product Launch - Premium Series
  - Target: high-value customers only
  - Budget: $30,000 | Savings: $12,000 (40%)
  - Channels: Email, Voice, WhatsApp (no SMS)
  - ROI: 380%

- Summer Sale - All Customers
  - Target: all customer segments
  - Budget: $40,000 | Savings: $20,000 (50%)
  - Channels: SMS, WhatsApp, Email, Voice
  - ROI: 420%

**Transactional Campaigns** (3 scenarios):
- Order Confirmation
  - Bypasses fatigue limits (critical transactional)
  - No guardrail approval required
  - Channels: SMS, Email, WhatsApp

- Shipping Update
  - Real-time tracking notifications
  - Bypasses fatigue limits
  - Channels: SMS, Email, WhatsApp

- Delivery Confirmation
  - Includes feedback request
  - Bypasses fatigue limits
  - Channels: SMS, Email, WhatsApp

**Support Recovery Campaigns** (2 scenarios):
- Angry Customer Recovery
  - Target: customers with negative sentiment
  - Channels: Email, Voice only (personal touch)
  - Requires guardrail approval
  - Excludes SMS/WhatsApp (too impersonal)

- Complaint Resolution Follow-up
  - Target: resolved complaint tickets
  - Channels: Email, WhatsApp
  - Respects fatigue limits
  - Requires guardrail approval

#### Budget Analysis
- **Total campaign budget**: $43,000
- **Total savings vs spray-and-pray**: $47,000
- **Savings percentage**: 52.2%
- **Projected annual savings**: $564,000

#### Channel Usage
- Email: 8 campaigns (100%)
- WhatsApp: 6 campaigns (75%)
- SMS: 5 campaigns (62.5%)
- Voice: 3 campaigns (37.5%)

### Demo Presentation Scenarios (Task 13.3 ✅)

Successfully generated **5 comprehensive demo scenarios** for presentations:

#### Scenario Types

**1. Spray-and-Pray Problem** (Before AI):
- Demonstrates traditional mass marketing failures
- Shows impact on 7 customer samples (high-value, angry, fatigued)
- 42 story steps explaining the problems
- Cost impact: $221,000 per campaign
- Results: 12% engagement, 8% unsubscribe, 45 complaints

**2. AI Orchestrated Solution** (After AI):
- Shows intelligent AI-powered approach
- Same 7 customers with personalized treatment
- 65 story steps showing AI decision-making
- Cost impact: $3,919 per campaign (98% savings)
- Results: 62% engagement, 0.5% unsubscribe, 2 complaints

**3. Cost Savings Demonstration**:
- Detailed ROI analysis and projections
- 46 story steps with financial breakdowns
- Annual savings: $11,288,212
- ROI: 450% (AI) vs -12% (spray-and-pray)
- Payback period: Immediate

**4. Fatigue Protection Demo**:
- Shows anti-fatigue system in action
- 5 fatigued customer examples
- 57 story steps explaining protection logic
- Outcome: 102 unsubscribes prevented, $244,800 value preserved

**5. Tone-Deaf Prevention Demo**:
- Demonstrates guardrail system blocking inappropriate messages
- 3 angry customer examples
- 83 story steps showing sentiment analysis and blocking
- Outcome: 23 escalations prevented, $145,600 value preserved

#### Metrics Summary
- Total scenarios: 5
- Total story steps: 293
- Customer examples: 22
- File size: ~563KB

## Next Steps

- [x] Task 13.2: Create campaign scenario data ✅
- [x] Task 13.3: Generate demo presentation scenarios ✅
- [x] Task 13.4: Set up data seeding and management for 1000+ customer scale ✅

## Task 13.4 Implementation ✅

Successfully implemented data seeding and management system with:

### Features Implemented

**1. Location and SKU Enrichment** (`location_sku_enrichment.py`):
- Enriches 1000 customer profiles with location data (40% Bangalore for demo)
- Adds product SKU interests, purchase history, browsing history, cart items
- 10 product SKUs across Electronics, Wearables, Audio, Photography, Accessories
- Supports filtering by location, SKU, or both

**2. Data Seeding Module** (`data_seeder.py`):
- In-memory storage for demo without DynamoDB (DataSeeder class)
- DynamoDB support ready for when Task 3 is completed (DynamoDBSeeder class)
- Batch operations (25 items per batch for DynamoDB limits)
- Efficient indexing by location and SKU for fast queries
- Data export/import capabilities
- Refresh utilities for demo resets

**3. Interactive Demo Query Engine** (`demo_query.py`):
- Simulates user's demo goal: "Run campaign for Bangalore users for SKU X"
- Shows suppressed users (angry, fatigued, disengaged)
- Demonstrates WhatsApp-first routing decisions
- Displays time-optimized send scheduling
- Calculates before/after metrics side-by-side

### Demo Results

**Bangalore Users for SKU-LAPTOP-001**:
- Found: 362 matching customers
- Suppressed: 124 (34.3%) - angry, fatigued, or disengaged
- Eligible: 238 customers
- Cost savings: $1.24 (34.3% reduction)
- Engagement improvement: +50% (12% → 62%)
- Unsubscribes prevented: 28
- Complaints prevented: 18

**Bangalore Users for SKU-PHONE-002**:
- Found: 363 matching customers
- Suppressed: 117 (32.2%)
- Eligible: 246 customers
- Cost savings: $1.17 (32.2% reduction)
- Engagement improvement: +50%
- Unsubscribes prevented: 28
- Complaints prevented: 18

### Usage

**Seed Demo Data**:
```bash
python3 src/ai_cpaas_demo/data/seed_demo_data.py
```

**Run Interactive Demo**:
```bash
python3 src/ai_cpaas_demo/data/demo_query.py
```

**Use in Code**:
```python
from ai_cpaas_demo.data import DataSeeder

# Initialize and seed data
seeder = DataSeeder()
seeder.seed_in_memory()

# Query by location
bangalore_users = seeder.query_by_location("Bangalore")

# Query by SKU
laptop_users = seeder.query_by_sku("SKU-LAPTOP-001")

# Query by both (for demo)
target_users = seeder.query_by_location_and_sku("Bangalore", "SKU-LAPTOP-001")

# Get statistics
stats = seeder.get_statistics()
```

### Data Files Generated

- `customer_profiles.json`: 1000 customer profiles (~15MB)
- `campaign_scenarios.json`: 8 campaign scenarios (~19KB)
- `demo_scenarios.json`: 5 presentation scenarios (~563KB)
- `enriched_customers.json`: 1000 enriched profiles with location/SKU data (~1.2MB)

### Next Steps for Production

When Task 3 (AWS Infrastructure) is completed:
1. Use `DynamoDBSeeder` class instead of `DataSeeder`
2. Create DynamoDB table with GSI on location field
3. Seed data with: `seeder.seed_dynamodb()`
4. Query using DynamoDB: `seeder.query_dynamodb_by_location("Bangalore")`

## Requirements Validated

✅ **Requirement 1.1**: Customer engagement patterns across all channels
✅ **Requirement 2.1**: Customer sentiment and interaction history
✅ **Requirement 5.1**: Communication frequency tracking and fatigue levels
✅ **Requirement 6.1**: Campaign scenario templates (promotional, transactional, support)
✅ **Requirement 6.2**: Before/after AI comparison demonstrations
✅ **Requirement 6.3**: Cost savings and ROI calculations
✅ **Requirement 6.4**: Budget analysis and cost savings calculations
✅ **Requirement 6.5**: Fatigue protection and tone-deaf prevention examples
✅ **Requirement 7.2**: Multi-step campaign planning with constraints
