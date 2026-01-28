"""AWS Native prediction engine implementation using SageMaker and Bedrock."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import boto3
import numpy as np
import pandas as pd
from botocore.exceptions import ClientError

from ...config.settings import settings
from ...core.interfaces import PredictionRequest, PredictionResult
from ...core.models import ChannelType, CustomerProfile, MessageType, SentimentType
from .base import BasePredictionEngine

logger = logging.getLogger(__name__)


class AWSNativePredictionEngine(BasePredictionEngine):
    """AWS Native implementation using SageMaker and Bedrock."""

    def __init__(self):
        """Initialize AWS services."""
        super().__init__()
        
        # Initialize AWS clients
        self.sagemaker_runtime = boto3.client(
            'sagemaker-runtime',
            region_name=settings.aws.region
        )
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws.bedrock_region
        )
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=settings.aws.region
        )
        
        # DynamoDB tables
        self.customer_table = self.dynamodb.Table(settings.aws.dynamodb_customer_table)
        self.decisions_table = self.dynamodb.Table(settings.aws.dynamodb_decisions_table)
        
        self.sagemaker_endpoint = settings.aws.sagemaker_endpoint_name
        self.bedrock_model_id = settings.aws.bedrock_model_id

    async def predict_channel(self, request: PredictionRequest) -> PredictionResult:
        """Predict optimal channel using SageMaker model and Bedrock reasoning."""
        logger.info(f"AWS Native prediction for customer {request.customer_id}")
        
        try:
            # Get customer profile from DynamoDB
            customer_profile = await self._get_customer_profile_from_dynamodb(request.customer_id)
            
            # Use SageMaker for initial prediction
            sagemaker_prediction = await self._invoke_sagemaker_model(request, customer_profile)
            
            # Use Bedrock for reasoning and confidence adjustment
            bedrock_analysis = await self._invoke_bedrock_reasoning(request, customer_profile, sagemaker_prediction)
            
            # Combine results
            result = await self._combine_predictions(request, sagemaker_prediction, bedrock_analysis)
            
            # Store decision record
            await self._store_decision_record(request, result)
            
            return result
            
        except Exception as e:
            logger.error(f"AWS Native prediction failed: {e}")
            # Fallback to base implementation
            logger.info("Falling back to base prediction engine")
            return await super().predict_channel(request)

    async def _invoke_sagemaker_model(
        self, request: PredictionRequest, customer_profile: CustomerProfile
    ) -> Dict[str, any]:
        """Invoke SageMaker endpoint for channel prediction."""
        try:
            # Prepare features for SageMaker model
            features = self._prepare_sagemaker_features(request, customer_profile)
            
            # Invoke SageMaker endpoint
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.sagemaker_endpoint,
                ContentType='application/json',
                Body=json.dumps(features)
            )
            
            # Parse response
            result = json.loads(response['Body'].read().decode())
            
            logger.debug(f"SageMaker prediction result: {result}")
            return result
            
        except ClientError as e:
            logger.error(f"SageMaker invocation failed: {e}")
            # Return mock prediction for development
            return self._mock_sagemaker_prediction(request)
        except Exception as e:
            logger.error(f"Unexpected error in SageMaker invocation: {e}")
            return self._mock_sagemaker_prediction(request)

    async def _invoke_bedrock_reasoning(
        self, 
        request: PredictionRequest, 
        customer_profile: CustomerProfile,
        sagemaker_prediction: Dict[str, any]
    ) -> Dict[str, any]:
        """Use Bedrock for advanced reasoning and explanation."""
        try:
            # Prepare prompt for Bedrock
            prompt = self._prepare_bedrock_prompt(request, customer_profile, sagemaker_prediction)
            
            # Invoke Bedrock
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.bedrock_model_id,
                body=json.dumps(body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            reasoning_text = response_body['content'][0]['text']
            
            # Parse structured reasoning from Bedrock response
            bedrock_analysis = self._parse_bedrock_response(reasoning_text)
            
            logger.debug(f"Bedrock analysis: {bedrock_analysis}")
            return bedrock_analysis
            
        except ClientError as e:
            logger.error(f"Bedrock invocation failed: {e}")
            return self._mock_bedrock_analysis(request)
        except Exception as e:
            logger.error(f"Unexpected error in Bedrock invocation: {e}")
            return self._mock_bedrock_analysis(request)

    def _prepare_sagemaker_features(
        self, request: PredictionRequest, customer_profile: CustomerProfile
    ) -> Dict[str, any]:
        """Prepare feature vector for SageMaker model."""
        # Calculate engagement features
        engagement_features = {}
        for channel in ChannelType:
            channel_records = [
                record for record in customer_profile.engagement_history
                if record.channel == channel
            ]
            
            if channel_records:
                engagement_features[f"{channel.value}_engagement_rate"] = np.mean([
                    1.0 if record.opened else 0.0 for record in channel_records
                ])
                engagement_features[f"{channel.value}_click_rate"] = np.mean([
                    1.0 if record.clicked else 0.0 for record in channel_records
                ])
                engagement_features[f"{channel.value}_avg_score"] = np.mean([
                    record.engagement_score for record in channel_records
                ])
                engagement_features[f"{channel.value}_message_count"] = len(channel_records)
            else:
                engagement_features[f"{channel.value}_engagement_rate"] = 0.0
                engagement_features[f"{channel.value}_click_rate"] = 0.0
                engagement_features[f"{channel.value}_avg_score"] = 0.0
                engagement_features[f"{channel.value}_message_count"] = 0
        
        # Message features
        message_features = {
            "message_type_promotional": 1.0 if request.message_type == MessageType.PROMOTIONAL else 0.0,
            "message_type_transactional": 1.0 if request.message_type == MessageType.TRANSACTIONAL else 0.0,
            "message_type_support": 1.0 if request.message_type == MessageType.SUPPORT else 0.0,
            "urgency_low": 1.0 if request.urgency.value == "low" else 0.0,
            "urgency_medium": 1.0 if request.urgency.value == "medium" else 0.0,
            "urgency_high": 1.0 if request.urgency.value == "high" else 0.0,
            "content_length": request.content_length,
        }
        
        # Customer features
        customer_features = {
            "total_messages": len(customer_profile.engagement_history),
            "fatigue_level_low": 1.0 if customer_profile.fatigue_level.value == "low" else 0.0,
            "fatigue_level_medium": 1.0 if customer_profile.fatigue_level.value == "medium" else 0.0,
            "fatigue_level_high": 1.0 if customer_profile.fatigue_level.value == "high" else 0.0,
            "support_tickets_count": len(customer_profile.support_tickets),
            "disengagement_signals_count": len(customer_profile.disengagement_signals),
        }
        
        # Combine all features
        features = {
            **engagement_features,
            **message_features,
            **customer_features,
        }
        
        return {"instances": [features]}

    def _prepare_bedrock_prompt(
        self, 
        request: PredictionRequest, 
        customer_profile: CustomerProfile,
        sagemaker_prediction: Dict[str, any]
    ) -> str:
        """Prepare prompt for Bedrock reasoning."""
        
        # Calculate engagement summary
        total_messages = len(customer_profile.engagement_history)
        recent_engagement = 0.0
        if total_messages > 0:
            recent_records = customer_profile.engagement_history[-10:]  # Last 10 messages
            recent_engagement = sum(record.engagement_score for record in recent_records) / len(recent_records)
        
        # Support ticket summary
        open_tickets = [ticket for ticket in customer_profile.support_tickets if ticket.status in ["open", "in_progress"]]
        recent_negative_sentiment = any(
            record.sentiment == SentimentType.NEGATIVE 
            for record in customer_profile.sentiment_history[-5:]  # Last 5 sentiment records
        )
        
        prompt = f"""You are an AI communication expert analyzing the optimal channel for customer messaging. Your goal is to maximize engagement while minimizing cost and respecting customer preferences.

Customer Analysis:
- Customer ID: {request.customer_id}
- Message Type: {request.message_type.value}
- Urgency Level: {request.urgency.value}
- Content Length: {request.content_length} characters
- Customer Fatigue Level: {customer_profile.fatigue_level.value}
- Total Historical Messages: {total_messages}
- Recent Engagement Score: {recent_engagement:.2f}/1.0
- Open Support Tickets: {len(open_tickets)}
- Recent Negative Sentiment: {"Yes" if recent_negative_sentiment else "No"}
- Disengagement Signals: {len(customer_profile.disengagement_signals)}

SageMaker Model Prediction:
{json.dumps(sagemaker_prediction, indent=2)}

Channel Options Analysis:
1. SMS: High open rates (85%), immediate delivery, character limits (160), cost: $0.0075
2. WhatsApp: Good engagement (75%), rich media support, cost: $0.005
3. Email: Lower open rates (25%), rich formatting, very low cost: $0.0001
4. Voice: Personal connection (15% answer rate), highest cost: $0.013/min

Decision Factors to Consider:
- Message urgency and type appropriateness
- Customer's historical channel preferences
- Content length and formatting needs
- Cost-effectiveness for the message type
- Customer fatigue and sentiment state
- Time-sensitive nature of the message

Please analyze this data and provide your recommendation in the following JSON format:
{{
    "recommended_channel": "sms|whatsapp|email|voice",
    "confidence": 0.85,
    "reasoning": [
        "Primary reason for channel selection",
        "Supporting factor based on customer data",
        "Cost-benefit analysis consideration"
    ],
    "channel_analysis": {{
        "sms": {{"score": 0.8, "risk": "low", "cost_effectiveness": 0.9}},
        "whatsapp": {{"score": 0.7, "risk": "low", "cost_effectiveness": 0.8}},
        "email": {{"score": 0.6, "risk": "medium", "cost_effectiveness": 0.95}},
        "voice": {{"score": 0.4, "risk": "high", "cost_effectiveness": 0.3}}
    }},
    "engagement_probability": 0.75,
    "risk_assessment": "low|medium|high",
    "alternative_recommendation": "backup_channel_if_primary_fails"
}}

Focus on providing actionable insights that balance engagement probability, cost efficiency, and customer experience."""
        
        return prompt

    def _parse_bedrock_response(self, reasoning_text: str) -> Dict[str, any]:
        """Parse structured response from Bedrock."""
        try:
            # Try to extract JSON from the response
            start_idx = reasoning_text.find('{')
            end_idx = reasoning_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = reasoning_text[start_idx:end_idx]
                parsed_response = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["recommended_channel", "confidence", "reasoning", "engagement_probability"]
                if all(field in parsed_response for field in required_fields):
                    return parsed_response
                else:
                    logger.warning("Bedrock response missing required fields, using fallback")
                    return self._fallback_parse_bedrock_response(reasoning_text)
            else:
                # Fallback parsing if JSON is not found
                return self._fallback_parse_bedrock_response(reasoning_text)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Bedrock JSON response: {e}, using fallback")
            return self._fallback_parse_bedrock_response(reasoning_text)
        except Exception as e:
            logger.error(f"Unexpected error parsing Bedrock response: {e}")
            return self._fallback_parse_bedrock_response(reasoning_text)

    def _fallback_parse_bedrock_response(self, reasoning_text: str) -> Dict[str, any]:
        """Fallback parsing for non-JSON Bedrock responses."""
        # Enhanced keyword-based parsing
        text_lower = reasoning_text.lower()
        
        # Channel detection with priority order
        recommended_channel = "email"  # Default fallback
        confidence = 0.6  # Default confidence
        
        # Channel priority based on keywords
        channel_keywords = {
            "sms": ["sms", "text message", "short message", "160 character", "immediate"],
            "whatsapp": ["whatsapp", "rich media", "multimedia", "chat"],
            "email": ["email", "detailed", "formatted", "newsletter", "marketing"],
            "voice": ["voice", "call", "phone", "speak", "urgent call"]
        }
        
        channel_scores = {}
        for channel, keywords in channel_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                channel_scores[channel] = score
        
        if channel_scores:
            recommended_channel = max(channel_scores.keys(), key=lambda k: channel_scores[k])
            confidence = min(0.8, 0.5 + (channel_scores[recommended_channel] * 0.1))
        
        # Extract reasoning from text
        reasoning_lines = []
        sentences = reasoning_text.split('.')
        for sentence in sentences[:3]:  # Take first 3 sentences
            if sentence.strip() and len(sentence.strip()) > 10:
                reasoning_lines.append(sentence.strip())
        
        if not reasoning_lines:
            reasoning_lines = [f"AI analysis recommends {recommended_channel} based on message characteristics"]
        
        # Engagement probability based on channel
        engagement_probabilities = {
            "sms": 0.85,
            "whatsapp": 0.75,
            "email": 0.25,
            "voice": 0.15
        }
        
        return {
            "recommended_channel": recommended_channel,
            "confidence": confidence,
            "reasoning": reasoning_lines,
            "engagement_probability": engagement_probabilities.get(recommended_channel, 0.5),
            "risk_assessment": "medium",
            "alternative_recommendation": "email" if recommended_channel != "email" else "sms"
        }

    async def _combine_predictions(
        self, 
        request: PredictionRequest,
        sagemaker_prediction: Dict[str, any],
        bedrock_analysis: Dict[str, any]
    ) -> PredictionResult:
        """Combine SageMaker and Bedrock predictions into final result."""
        # Use Bedrock's recommendation as primary
        channel_name = bedrock_analysis.get("recommended_channel", "email")
        
        # Map channel name to enum
        channel_mapping = {
            "sms": ChannelType.SMS,
            "whatsapp": ChannelType.WHATSAPP,
            "email": ChannelType.EMAIL,
            "voice": ChannelType.VOICE,
        }
        
        selected_channel = channel_mapping.get(channel_name.lower(), ChannelType.EMAIL)
        
        # Calculate final confidence (blend SageMaker and Bedrock)
        bedrock_confidence = bedrock_analysis.get("confidence", 0.7)
        sagemaker_confidence = sagemaker_prediction.get("confidence", 0.6)
        final_confidence = (bedrock_confidence * 0.7) + (sagemaker_confidence * 0.3)
        
        # Get reasoning
        reasoning = bedrock_analysis.get("reasoning", ["AI-powered channel selection"])
        
        # Calculate cost and engagement probability
        cost_estimate = self._calculate_cost_estimate(selected_channel, request.content_length)
        engagement_probability = bedrock_analysis.get("engagement_probability", 0.6)
        
        return PredictionResult(
            channel=selected_channel,
            confidence=min(final_confidence, 1.0),
            cost_estimate=cost_estimate,
            engagement_probability=engagement_probability,
            reasoning=reasoning,
        )

    async def _get_customer_profile_from_dynamodb(self, customer_id: UUID) -> CustomerProfile:
        """Get customer profile from DynamoDB."""
        try:
            response = self.customer_table.get_item(
                Key={'customer_id': str(customer_id)}
            )
            
            if 'Item' in response:
                # Convert DynamoDB item to CustomerProfile
                item = response['Item']
                return CustomerProfile(
                    id=UUID(item['customer_id']),
                    external_id=item.get('external_id', str(customer_id)),
                    # TODO: Parse other fields from DynamoDB item
                    channel_preferences=[],
                    engagement_history=[],
                    sentiment_history=[],
                    support_tickets=[],
                )
            else:
                # Return default profile if not found
                logger.warning(f"Customer profile not found for {customer_id}, using default")
                return await super()._get_customer_profile(customer_id)
                
        except ClientError as e:
            logger.error(f"DynamoDB query failed: {e}")
            return await super()._get_customer_profile(customer_id)

    async def _store_decision_record(self, request: PredictionRequest, result: PredictionResult):
        """Store prediction decision in DynamoDB for tracking."""
        try:
            decision_record = {
                'decision_id': str(uuid4()),
                'customer_id': str(request.customer_id),
                'timestamp': datetime.utcnow().isoformat(),
                'decision_type': 'channel_prediction',
                'input_data': {
                    'message_type': request.message_type.value,
                    'urgency': request.urgency.value,
                    'content_length': request.content_length,
                    'variant': request.variant.value,
                },
                'output_data': {
                    'selected_channel': result.channel.value,
                    'confidence': result.confidence,
                    'cost_estimate': result.cost_estimate,
                    'engagement_probability': result.engagement_probability,
                },
                'reasoning': result.reasoning,
                'variant': 'aws',
                'engine_name': 'prediction',
            }
            
            self.decisions_table.put_item(Item=decision_record)
            logger.debug(f"Stored decision record: {decision_record['decision_id']}")
            
        except ClientError as e:
            logger.error(f"Failed to store decision record: {e}")

    def _mock_sagemaker_prediction(self, request: PredictionRequest) -> Dict[str, any]:
        """Mock SageMaker prediction for development/testing."""
        # Simple mock based on message type
        if request.message_type == MessageType.PROMOTIONAL:
            return {
                "predictions": [
                    {"channel": "email", "score": 0.7},
                    {"channel": "whatsapp", "score": 0.6},
                    {"channel": "sms", "score": 0.4},
                    {"channel": "voice", "score": 0.2},
                ],
                "confidence": 0.75,
            }
        elif request.message_type == MessageType.TRANSACTIONAL:
            return {
                "predictions": [
                    {"channel": "sms", "score": 0.8},
                    {"channel": "email", "score": 0.7},
                    {"channel": "whatsapp", "score": 0.5},
                    {"channel": "voice", "score": 0.3},
                ],
                "confidence": 0.8,
            }
        else:  # SUPPORT
            return {
                "predictions": [
                    {"channel": "voice", "score": 0.9},
                    {"channel": "whatsapp", "score": 0.6},
                    {"channel": "email", "score": 0.5},
                    {"channel": "sms", "score": 0.4},
                ],
                "confidence": 0.85,
            }

    def _mock_bedrock_analysis(self, request: PredictionRequest) -> Dict[str, any]:
        """Mock Bedrock analysis for development/testing."""
        
        # More sophisticated mock based on message characteristics
        analysis_map = {
            MessageType.PROMOTIONAL: {
                "low_urgency": {
                    "recommended_channel": "email",
                    "confidence": 0.78,
                    "reasoning": [
                        "Email provides rich formatting ideal for promotional content",
                        "Cost-effective for marketing campaigns with detailed product information",
                        "Allows for comprehensive brand storytelling and visual elements"
                    ],
                    "engagement_probability": 0.32,
                    "risk_assessment": "low"
                },
                "medium_urgency": {
                    "recommended_channel": "whatsapp",
                    "confidence": 0.82,
                    "reasoning": [
                        "WhatsApp balances rich media with higher engagement rates",
                        "Suitable for time-sensitive promotional offers",
                        "Personal feel increases conversion probability"
                    ],
                    "engagement_probability": 0.68,
                    "risk_assessment": "low"
                },
                "high_urgency": {
                    "recommended_channel": "sms",
                    "confidence": 0.85,
                    "reasoning": [
                        "SMS ensures immediate visibility for urgent promotions",
                        "Highest open rates for time-critical offers",
                        "Direct and concise messaging drives quick action"
                    ],
                    "engagement_probability": 0.85,
                    "risk_assessment": "medium"
                }
            },
            MessageType.TRANSACTIONAL: {
                "low_urgency": {
                    "recommended_channel": "email",
                    "confidence": 0.75,
                    "reasoning": [
                        "Email provides detailed transaction records and receipts",
                        "Customers expect comprehensive transactional information",
                        "Cost-effective for routine transaction confirmations"
                    ],
                    "engagement_probability": 0.78,
                    "risk_assessment": "low"
                },
                "medium_urgency": {
                    "recommended_channel": "sms",
                    "confidence": 0.88,
                    "reasoning": [
                        "SMS ideal for important transaction notifications",
                        "Immediate delivery ensures customer awareness",
                        "Concise format perfect for status updates"
                    ],
                    "engagement_probability": 0.92,
                    "risk_assessment": "low"
                },
                "high_urgency": {
                    "recommended_channel": "sms",
                    "confidence": 0.95,
                    "reasoning": [
                        "Critical transaction alerts require immediate attention",
                        "SMS guarantees fastest delivery and highest visibility",
                        "Essential for security and fraud prevention notifications"
                    ],
                    "engagement_probability": 0.95,
                    "risk_assessment": "low"
                }
            },
            MessageType.SUPPORT: {
                "low_urgency": {
                    "recommended_channel": "email",
                    "confidence": 0.72,
                    "reasoning": [
                        "Email allows for detailed support documentation",
                        "Customers can reference support information later",
                        "Suitable for non-urgent follow-ups and surveys"
                    ],
                    "engagement_probability": 0.65,
                    "risk_assessment": "low"
                },
                "medium_urgency": {
                    "recommended_channel": "whatsapp",
                    "confidence": 0.80,
                    "reasoning": [
                        "WhatsApp enables interactive support conversations",
                        "Customers prefer chat for moderate support issues",
                        "Allows for quick back-and-forth problem resolution"
                    ],
                    "engagement_probability": 0.75,
                    "risk_assessment": "medium"
                },
                "high_urgency": {
                    "recommended_channel": "voice",
                    "confidence": 0.90,
                    "reasoning": [
                        "Voice calls provide immediate human connection for urgent issues",
                        "Complex problems require real-time conversation",
                        "Highest customer satisfaction for critical support needs"
                    ],
                    "engagement_probability": 0.70,
                    "risk_assessment": "high"
                }
            }
        }
        
        # Get the appropriate analysis
        urgency_key = f"{request.urgency.value}_urgency"
        message_analysis = analysis_map.get(request.message_type, {})
        selected_analysis = message_analysis.get(urgency_key, message_analysis.get("medium_urgency", {
            "recommended_channel": "email",
            "confidence": 0.6,
            "reasoning": ["Default recommendation based on general best practices"],
            "engagement_probability": 0.5,
            "risk_assessment": "medium"
        }))
        
        # Add content length adjustments
        if request.content_length > 300 and selected_analysis["recommended_channel"] == "sms":
            # Switch to email for long content
            selected_analysis = {
                "recommended_channel": "email",
                "confidence": 0.85,
                "reasoning": [
                    "Content length exceeds SMS limits, email provides better formatting",
                    "Detailed information requires rich text presentation",
                    "Email prevents message truncation and maintains readability"
                ],
                "engagement_probability": 0.45,
                "risk_assessment": "low"
            }
        
        # Add alternative recommendation
        alternatives = {"sms": "whatsapp", "whatsapp": "email", "email": "sms", "voice": "whatsapp"}
        selected_analysis["alternative_recommendation"] = alternatives.get(
            selected_analysis["recommended_channel"], "email"
        )
        
        return selected_analysis