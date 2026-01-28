#!/bin/bash

# AI-CPaaS Demo - AWS Infrastructure Deployment Script
# This script deploys the AWS End User Messaging infrastructure with rate limiting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="ai-cpaas-messaging-infrastructure"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PROJECT_NAME="ai-cpaas-demo"

# Determine script directory and template location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/cloudformation/messaging-infrastructure.yaml"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    print_success "AWS CLI found"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure'"
        exit 1
    fi
    print_success "AWS credentials configured"
    
    # Check template file
    if [ ! -f "$TEMPLATE_FILE" ]; then
        print_error "Template file not found: $TEMPLATE_FILE"
        exit 1
    fi
    print_success "CloudFormation template found"
    
    echo ""
}

# Validate CloudFormation template
validate_template() {
    print_header "Validating CloudFormation Template"
    
    if aws cloudformation validate-template \
        --template-body file://$TEMPLATE_FILE \
        --region $REGION &> /dev/null; then
        print_success "Template validation passed"
    else
        print_error "Template validation failed"
        exit 1
    fi
    
    echo ""
}

# Deploy stack
deploy_stack() {
    print_header "Deploying CloudFormation Stack"
    
    print_info "Stack Name: $STACK_NAME"
    print_info "Region: $REGION"
    print_info "Environment: $ENVIRONMENT"
    print_info "Project: $PROJECT_NAME"
    echo ""
    
    # Check if stack exists
    if aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION &> /dev/null; then
        print_warning "Stack already exists. Updating..."
        OPERATION="update-stack"
    else
        print_info "Creating new stack..."
        OPERATION="create-stack"
    fi
    
    # Deploy stack
    aws cloudformation $OPERATION \
        --stack-name $STACK_NAME \
        --template-body file://$TEMPLATE_FILE \
        --parameters \
            ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION \
        --tags \
            Key=Project,Value=$PROJECT_NAME \
            Key=Environment,Value=$ENVIRONMENT \
            Key=ManagedBy,Value=CloudFormation
    
    print_success "Stack deployment initiated"
    echo ""
}

# Wait for stack completion
wait_for_stack() {
    print_header "Waiting for Stack Completion"
    
    print_info "This may take a few minutes..."
    
    if aws cloudformation wait stack-$1-complete \
        --stack-name $STACK_NAME \
        --region $REGION; then
        print_success "Stack $1 completed successfully"
    else
        print_error "Stack $1 failed"
        print_error "Check AWS Console for details"
        exit 1
    fi
    
    echo ""
}

# Get stack outputs
get_outputs() {
    print_header "Stack Outputs"
    
    aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table
    
    echo ""
}

# Save outputs to .env file
save_env_file() {
    print_header "Saving Configuration"
    
    # Determine project root (parent of infrastructure directory)
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    ENV_FILE="$PROJECT_ROOT/.env.aws"
    
    # Get outputs
    RATE_LIMITS_TABLE=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`RateLimitsTableName`].OutputValue' \
        --output text)
    
    DELIVERY_TABLE=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`DeliveryTrackingTableName`].OutputValue' \
        --output text)
    
    MESSAGING_ROLE=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`MessagingApplicationRoleArn`].OutputValue' \
        --output text)
    
    # Create .env file
    cat > $ENV_FILE << EOF
# AWS End User Messaging Infrastructure Configuration
# Generated by deploy.sh on $(date)

# AWS Configuration
AWS_REGION=$REGION
AWS_ENVIRONMENT=$ENVIRONMENT

# DynamoDB Tables
RATE_LIMITS_TABLE=$RATE_LIMITS_TABLE
DELIVERY_TRACKING_TABLE=$DELIVERY_TABLE

# IAM Roles
MESSAGING_ROLE_ARN=$MESSAGING_ROLE

# CloudFormation Stack
STACK_NAME=$STACK_NAME
EOF
    
    print_success "Configuration saved to $ENV_FILE"
    print_info "Source this file in your application: source $ENV_FILE"
    
    echo ""
}

# Print next steps
print_next_steps() {
    print_header "Next Steps"
    
    echo "1. Update your application configuration:"
    echo "   - Set RATE_LIMITS_TABLE environment variable"
    echo "   - Set DELIVERY_TRACKING_TABLE environment variable"
    echo ""
    echo "2. Test the infrastructure:"
    echo "   cd .."
    echo "   python example_aws_messaging.py"
    echo ""
    echo "3. Monitor CloudWatch alarms:"
    echo "   aws cloudwatch describe-alarms --region $REGION"
    echo ""
    echo "4. View delivery tracking:"
    echo "   aws dynamodb scan --table-name $DELIVERY_TABLE --region $REGION"
    echo ""
    
    print_success "Deployment complete! 🚀"
}

# Main execution
main() {
    print_header "AI-CPaaS AWS Infrastructure Deployment"
    echo ""
    
    check_prerequisites
    validate_template
    deploy_stack
    
    # Determine operation for wait
    if aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION &> /dev/null; then
        WAIT_OP="update"
    else
        WAIT_OP="create"
    fi
    
    wait_for_stack $WAIT_OP
    get_outputs
    save_env_file
    print_next_steps
}

# Run main function
main
