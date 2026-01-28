# AI-CPaaS Demo

A demonstration application addressing the 2026 communication crisis: "Brands are shouting, but customers aren't listening." This demo showcases how Applied AI integrated with CPaaS can solve channel fatigue, eliminate the 'spray and pray' tax, reduce content friction, and prevent tone-deaf messaging that kills brands.

## Solution Vision

**"We are moving from Broadcasting to Orchestrating."**

The demo showcases an Applied AI layer that sits on top of communication pipes. It doesn't just send data; it reasons before it hits 'Send.'

- **It Predicts:** Which channel will this specific user actually open?
- **It Adapts:** Uses GenAI to automatically shrink or expand content for the chosen channel.
- **It Protects:** Acts as a safety guardrail, checking sentiment before annoying a frustrated customer.

## Implementation Variants

The demo is developed in two technology variants:

- **Variant A: AWS Native AI Stack** - Leverages AWS Bedrock, SageMaker, Lambda, and other native AWS AI services
- **Variant B: Open Source AI Framework Stack** - Built using LangChain, LangGraph, and other open-source frameworks deployed on AWS

## Project Structure

```
ai-cpaas-demo/
├── src/ai_cpaas_demo/           # Main application code
│   ├── core/                    # Core data models and interfaces
│   ├── engines/                 # AI engines (prediction, adaptation, guardrail, etc.)
│   ├── agents/                  # AI agents (orchestration, protection, optimization)
│   ├── services/                # Business services and orchestration
│   ├── integrations/            # CPaaS and external service integrations
│   ├── api/                     # FastAPI application and routes
│   └── config/                  # Configuration management
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── property/                # Property-based tests
├── infrastructure/              # AWS CDK infrastructure code
├── frontend/                    # React/Next.js frontend application
└── docs/                        # Documentation
```

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry for dependency management
- AWS CLI configured (for AWS services)
- Node.js 18+ (for frontend)

### Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   poetry install
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend && npm install
   ```

### Development

1. Activate the virtual environment:
   ```bash
   poetry shell
   ```
2. Run the backend API:
   ```bash
   uvicorn ai_cpaas_demo.api.main:app --reload
   ```
3. Run the frontend (in another terminal):
   ```bash
   cd frontend && npm run dev
   ```

### Testing

Run all tests:
```bash
poetry run pytest
```

Run property-based tests:
```bash
poetry run pytest -m property
```

Run tests with coverage:
```bash
poetry run pytest --cov
```

## Architecture

The system implements five core AI engines:

1. **Prediction Engine** - Analyzes customer data to predict optimal communication channels
2. **Content Adaptation Engine** - Uses GenAI to automatically resize content for different channels
3. **Safety Guardrail** - Prevents tone-deaf messaging by analyzing customer context and sentiment
4. **Anti-Fatigue Protection System** - Monitors communication frequency and prevents customer overload
5. **Real-Time Analytics Engine** - Processes communication patterns and provides business insights

## Configuration

Configuration is managed through environment variables and AWS Systems Manager Parameter Store. See `src/ai_cpaas_demo/config/` for configuration schemas.

## Deployment

Infrastructure is managed using AWS CDK. See `infrastructure/` directory for deployment scripts.

## Contributing

1. Follow the established code style (Black, isort, flake8)
2. Write tests for new functionality
3. Update documentation as needed
4. Use conventional commit messages

## License

This project is for demonstration purposes only.