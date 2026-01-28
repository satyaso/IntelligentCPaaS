"""AWS Native safety guardrail engine with Comprehend integration."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ...core.interfaces import GuardrailRequest, GuardrailResult
from ...core.models import MessageType
from .base import BaseSafetyGuardrail

logger = logging.getLogger(__name__)


class AWSNativeSafetyGuardrail(BaseSafetyGuardrail):
    """AWS Native implementation of the safety guardrail system using Comprehend and Bedrock."""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize the AWS Native safety guardrail engine."""
        super().__init__()
        self.region_name = region_name
        
        # Initialize AWS clients with fallback handling
        try:
            self.comprehend_client = boto3.client('comprehend', region_name=region_name)
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
            self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
            self.aws_available = True
            logger.info("AWS services initialized successfully")
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"AWS services not available: {e}. Falling back to base implementation.")
            self.aws_available = False
        
        # DynamoDB table names (would be created by infrastructure)
        self.interactions_table_name = "customer-interactions"
        self.support_tickets_table_name = "support-tickets"
        self.guardrail_logs_table_name = "guardrail-decisions"

    async def analyze_customer_sentiment(self, customer_id: UUID) -> Dict[str, Any]:
        """Analyze recent customer sentiment using AWS Comprehend."""
        logger.debug(f"Analyzing sentiment for customer {customer_id} using AWS Comprehend")
        
        if not self.aws_available:
            logger.info("AWS not available, falling back to base implementation")
            return await super().analyze_customer_sentiment(customer_id)
        
        try:
            # Get recent interactions from DynamoDB
            recent_interactions = await self._get_customer_interactions(customer_id)
            
            if not recent_interactions:
                logger.info(f"No recent interactions found for customer {customer_id}")
                return await super().analyze_customer_sentiment(customer_id)
            
            # Analyze sentiment using Comprehend
            sentiment_results = []
            for interaction in recent_interactions:
                content = interaction.get('content', '')
                if content and len(content.strip()) > 0:
                    sentiment_result = await self._analyze_with_comprehend(content)
                    sentiment_results.append({
                        'interaction': interaction,
                        'sentiment': sentiment_result
                    })
            
            # Aggregate sentiment analysis
            return self._aggregate_sentiment_analysis(sentiment_results)
            
        except Exception as e:
            logger.error(f"Error in AWS sentiment analysis: {e}")
            # Fall back to base implementation
            return await super().analyze_customer_sentiment(customer_id)

    async def check_support_issues(self, customer_id: UUID) -> bool:
        """Check if customer has unresolved support issues using DynamoDB."""
        logger.debug(f"Checking support issues for customer {customer_id}")
        
        if not self.aws_available:
            return await super().check_support_issues(customer_id)
        
        try:
            # Query DynamoDB for open support tickets
            table = self.dynamodb.Table(self.support_tickets_table_name)
            
            response = table.query(
                IndexName='customer-status-index',
                KeyConditionExpression='customer_id = :customer_id AND ticket_status = :status',
                ExpressionAttributeValues={
                    ':customer_id': str(customer_id),
                    ':status': 'open'
                }
            )
            
            open_tickets = response.get('Items', [])
            has_issues = len(open_tickets) > 0
            
            if has_issues:
                logger.info(f"Customer {customer_id} has {len(open_tickets)} open support tickets")
                
                # Log to CloudWatch for monitoring
                await self._log_support_check(customer_id, len(open_tickets))
            
            return has_issues
            
        except Exception as e:
            logger.error(f"Error checking support issues: {e}")
            # Fall back to base implementation
            return await super().check_support_issues(customer_id)

    async def check_safety(self, request: GuardrailRequest) -> GuardrailResult:
        """Enhanced safety check using AWS Bedrock for context understanding."""
        logger.info(f"Performing AWS Native safety check for customer {request.customer_id}")
        
        # Get base analysis
        base_result = await super().check_safety(request)
        
        if not self.aws_available:
            return base_result
        
        try:
            # Use Bedrock for enhanced context understanding
            enhanced_analysis = await self._analyze_with_bedrock(request, base_result)
            
            # Combine base and enhanced analysis
            final_result = self._combine_analysis_results(base_result, enhanced_analysis)
            
            # Log decision to DynamoDB and CloudWatch
            await self._log_guardrail_decision(request, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error in enhanced safety analysis: {e}")
            # Return base result if enhanced analysis fails
            return base_result

    async def _get_customer_interactions(self, customer_id: UUID) -> List[Dict[str, Any]]:
        """Get recent customer interactions from DynamoDB."""
        try:
            table = self.dynamodb.Table(self.interactions_table_name)
            
            # Query for interactions in the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            response = table.query(
                KeyConditionExpression='customer_id = :customer_id',
                FilterExpression='interaction_timestamp > :timestamp',
                ExpressionAttributeValues={
                    ':customer_id': str(customer_id),
                    ':timestamp': thirty_days_ago.isoformat()
                },
                ScanIndexForward=False,  # Most recent first
                Limit=10  # Limit to last 10 interactions
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error fetching customer interactions: {e}")
            # Fall back to simulated data
            return self._get_simulated_interactions(customer_id)

    async def _analyze_with_comprehend(self, text: str) -> Dict[str, Any]:
        """Analyze text sentiment using AWS Comprehend."""
        try:
            # Comprehend has a 5000 byte limit, truncate if necessary
            if len(text.encode('utf-8')) > 5000:
                text = text[:4900] + "..."
            
            # Detect sentiment
            sentiment_response = self.comprehend_client.detect_sentiment(
                Text=text,
                LanguageCode='en'
            )
            
            # Detect key phrases for additional context
            key_phrases_response = self.comprehend_client.detect_key_phrases(
                Text=text,
                LanguageCode='en'
            )
            
            return {
                'sentiment': sentiment_response['Sentiment'].lower(),
                'sentiment_scores': sentiment_response['SentimentScore'],
                'confidence': sentiment_response['SentimentScore'][sentiment_response['Sentiment'].title()],
                'key_phrases': [phrase['Text'] for phrase in key_phrases_response['KeyPhrases'][:5]]
            }
            
        except Exception as e:
            logger.error(f"Error in Comprehend analysis: {e}")
            # Fall back to base sentiment analysis
            return self._analyze_text_sentiment(text)

    async def _analyze_with_bedrock(self, request: GuardrailRequest, base_result: GuardrailResult) -> Dict[str, Any]:
        """Use Bedrock Claude for enhanced context understanding."""
        try:
            # Prepare context for Bedrock
            context = {
                'customer_id': str(request.customer_id),
                'proposed_message': request.proposed_message,
                'message_type': request.message_type.value,
                'base_analysis': {
                    'approved': base_result.approved,
                    'risk_level': base_result.risk_level,
                    'blocked_reasons': base_result.blocked_reasons
                },
                'recent_interactions': request.recent_interactions[:3]  # Last 3 interactions
            }
            
            # Create prompt for Claude
            prompt = f"""You are an AI safety guardrail system analyzing whether a message should be sent to a customer.

Context:
- Customer ID: {context['customer_id']}
- Message Type: {context['message_type']}
- Proposed Message: "{context['proposed_message']}"

Base Analysis Results:
- Approved: {context['base_analysis']['approved']}
- Risk Level: {context['base_analysis']['risk_level']}
- Blocked Reasons: {context['base_analysis']['blocked_reasons']}

Recent Customer Interactions:
{json.dumps(context['recent_interactions'], indent=2)}

Please provide an enhanced analysis considering:
1. Customer context and interaction history
2. Message timing and appropriateness
3. Potential brand risk
4. Alternative approaches

Respond in JSON format with:
{{
    "enhanced_risk_level": "low|medium|high",
    "confidence": 0.0-1.0,
    "additional_concerns": ["concern1", "concern2"],
    "recommended_actions": ["action1", "action2"],
    "reasoning": "detailed explanation"
}}"""

            # Call Bedrock Claude
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Try to parse JSON response
            try:
                enhanced_analysis = json.loads(content)
                return enhanced_analysis
            except json.JSONDecodeError:
                logger.warning("Bedrock response not valid JSON, extracting key information")
                return self._extract_analysis_from_text(content)
                
        except Exception as e:
            logger.error(f"Error in Bedrock analysis: {e}")
            return {
                'enhanced_risk_level': base_result.risk_level,
                'confidence': base_result.confidence,
                'additional_concerns': [],
                'recommended_actions': ['Use base analysis results'],
                'reasoning': f'Bedrock analysis failed: {str(e)}'
            }

    def _extract_analysis_from_text(self, text: str) -> Dict[str, Any]:
        """Extract analysis information from text when JSON parsing fails."""
        # Simple extraction logic for fallback
        risk_level = 'medium'
        if 'high risk' in text.lower() or 'high-risk' in text.lower():
            risk_level = 'high'
        elif 'low risk' in text.lower() or 'low-risk' in text.lower():
            risk_level = 'low'
        
        return {
            'enhanced_risk_level': risk_level,
            'confidence': 0.6,
            'additional_concerns': [],
            'recommended_actions': ['Review Bedrock analysis manually'],
            'reasoning': 'Extracted from text analysis'
        }

    def _aggregate_sentiment_analysis(self, sentiment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate multiple sentiment analysis results."""
        if not sentiment_results:
            return {
                'overall_sentiment': 'neutral',
                'sentiment_score': 0.0,
                'negative_interactions': 0,
                'support_interactions': 0,
                'recent_interaction_count': 0,
                'confidence': 0.5
            }
        
        # Calculate weighted sentiment scores
        total_weight = 0
        weighted_score = 0
        negative_count = 0
        support_count = 0
        
        for result in sentiment_results:
            sentiment = result['sentiment']
            interaction = result['interaction']
            
            # Weight more recent interactions higher
            age_hours = (datetime.now() - datetime.fromisoformat(interaction.get('interaction_timestamp', datetime.now().isoformat()))).total_seconds() / 3600
            weight = max(0.1, 1.0 - (age_hours / 168))  # Decay over 1 week
            
            # Convert sentiment to score
            if sentiment['sentiment'] == 'negative':
                score = -sentiment['confidence']
                negative_count += 1
            elif sentiment['sentiment'] == 'positive':
                score = sentiment['confidence']
            else:
                score = 0
            
            weighted_score += score * weight
            total_weight += weight
            
            if interaction.get('type') == 'support':
                support_count += 1
        
        avg_sentiment_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Determine overall sentiment
        if avg_sentiment_score < -0.3:
            overall_sentiment = 'negative'
        elif avg_sentiment_score > 0.3:
            overall_sentiment = 'positive'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'overall_sentiment': overall_sentiment,
            'sentiment_score': avg_sentiment_score,
            'negative_interactions': negative_count,
            'support_interactions': support_count,
            'recent_interaction_count': len(sentiment_results),
            'confidence': min(0.9, 0.5 + (len(sentiment_results) * 0.1))
        }

    def _combine_analysis_results(self, base_result: GuardrailResult, enhanced_analysis: Dict[str, Any]) -> GuardrailResult:
        """Combine base and enhanced analysis results."""
        # Use enhanced risk level if available and different
        final_risk_level = enhanced_analysis.get('enhanced_risk_level', base_result.risk_level)
        
        # Combine blocked reasons
        final_blocked_reasons = list(base_result.blocked_reasons)
        final_blocked_reasons.extend(enhanced_analysis.get('additional_concerns', []))
        
        # Combine alternative actions
        final_alternative_actions = list(base_result.alternative_actions)
        final_alternative_actions.extend(enhanced_analysis.get('recommended_actions', []))
        
        # Determine final approval based on enhanced analysis
        final_approved = base_result.approved
        if final_risk_level == 'high':
            final_approved = False
        
        # Use higher confidence if enhanced analysis is more confident
        final_confidence = max(base_result.confidence, enhanced_analysis.get('confidence', 0.0))
        
        return GuardrailResult(
            approved=final_approved,
            risk_level=final_risk_level,
            blocked_reasons=final_blocked_reasons,
            alternative_actions=final_alternative_actions,
            confidence=final_confidence
        )

    async def _log_guardrail_decision(self, request: GuardrailRequest, result: GuardrailResult) -> None:
        """Log guardrail decision to DynamoDB and CloudWatch."""
        try:
            # Log to DynamoDB
            table = self.dynamodb.Table(self.guardrail_logs_table_name)
            
            log_entry = {
                'decision_id': str(UUID.uuid4()),
                'customer_id': str(request.customer_id),
                'timestamp': datetime.now().isoformat(),
                'message_type': request.message_type.value,
                'proposed_message': request.proposed_message[:500],  # Truncate for storage
                'approved': result.approved,
                'risk_level': result.risk_level,
                'blocked_reasons': result.blocked_reasons,
                'confidence': result.confidence,
                'ttl': int((datetime.now() + timedelta(days=90)).timestamp())  # Auto-delete after 90 days
            }
            
            table.put_item(Item=log_entry)
            
            # Log metrics to CloudWatch
            self.cloudwatch.put_metric_data(
                Namespace='AI-CPaaS/Guardrail',
                MetricData=[
                    {
                        'MetricName': 'GuardrailDecisions',
                        'Dimensions': [
                            {'Name': 'RiskLevel', 'Value': result.risk_level},
                            {'Name': 'Approved', 'Value': str(result.approved)},
                            {'Name': 'MessageType', 'Value': request.message_type.value}
                        ],
                        'Value': 1,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'GuardrailConfidence',
                        'Dimensions': [
                            {'Name': 'RiskLevel', 'Value': result.risk_level}
                        ],
                        'Value': result.confidence,
                        'Unit': 'None'
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Error logging guardrail decision: {e}")

    async def _log_support_check(self, customer_id: UUID, ticket_count: int) -> None:
        """Log support check to CloudWatch."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='AI-CPaaS/Guardrail',
                MetricData=[
                    {
                        'MetricName': 'SupportTicketChecks',
                        'Dimensions': [
                            {'Name': 'HasOpenTickets', 'Value': str(ticket_count > 0)}
                        ],
                        'Value': 1,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'OpenSupportTickets',
                        'Value': ticket_count,
                        'Unit': 'Count'
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Error logging support check: {e}")