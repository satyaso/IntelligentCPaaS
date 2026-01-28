"""AWS Native content adaptation engine with Bedrock Claude integration."""

import json
import logging
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError, BotoCoreError

from .base import BaseContentAdaptationEngine
from ...core.interfaces import AdaptationRequest, AdaptationResult, ContentChange
from ...core.models import ChannelType, BrandProfile, MessageType
from .templates import MediaElement, RichMediaAdapter

logger = logging.getLogger(__name__)


class AWSNativeContentAdaptationEngine(BaseContentAdaptationEngine):
    """AWS Native implementation using Bedrock Claude for content adaptation."""

    def __init__(self, region_name: str = "us-east-1"):
        """Initialize the AWS Native content adaptation engine."""
        super().__init__()
        self.region_name = region_name
        
        # Initialize AWS clients
        try:
            self.bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=region_name
            )
            self.comprehend = boto3.client(
                'comprehend',
                region_name=region_name
            )
            self.s3 = boto3.client('s3', region_name=region_name)
        except Exception as e:
            logger.warning(f"Failed to initialize AWS clients: {e}")
            # Set to None for testing/development
            self.bedrock_runtime = None
            self.comprehend = None
            self.s3 = None
        
        # Claude model configuration
        self.claude_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.max_tokens = 4000
        self.temperature = 0.3  # Lower temperature for more consistent results

    async def adapt_content(self, request: AdaptationRequest) -> AdaptationResult:
        """Adapt content using AWS Bedrock Claude."""
        logger.info(f"AWS Native: Adapting content for {request.target_channel}")
        
        try:
            # Use Bedrock Claude for intelligent adaptation
            if self.bedrock_runtime:
                return await self._adapt_with_bedrock(request)
            else:
                # Fallback to base implementation
                logger.warning("Bedrock not available, falling back to base implementation")
                return await super().adapt_content(request)
        except Exception as e:
            logger.error(f"Bedrock adaptation failed: {e}")
            # Fallback to base implementation
            return await super().adapt_content(request)

    async def shrink_for_sms(self, content: str, max_length: int = 160) -> str:
        """Use Claude to intelligently shrink content for SMS."""
        if not self.bedrock_runtime:
            return await super().shrink_for_sms(content, max_length)
        
        try:
            prompt = self._create_sms_shrinking_prompt(content, max_length)
            response = await self._call_bedrock_claude(prompt)
            
            # Extract the shortened content from Claude's response
            shrunk_content = self._extract_content_from_response(response)
            
            # Validate length and fallback if necessary
            if len(shrunk_content) > max_length:
                logger.warning("Claude response too long, using base implementation")
                return await super().shrink_for_sms(content, max_length)
            
            return shrunk_content
            
        except Exception as e:
            logger.error(f"Claude SMS shrinking failed: {e}")
            return await super().shrink_for_sms(content, max_length)

    async def expand_for_rich_media(self, content: str, channel: ChannelType) -> str:
        """Use Claude to expand content for rich media channels with media support."""
        if not self.bedrock_runtime:
            return await super().expand_for_rich_media(content, channel)
        
        try:
            # Extract media from content
            media_urls = self.media_adapter.extract_media_urls(content)
            media_elements = self.media_adapter.create_media_elements(media_urls)
            
            # Create enhanced prompt with media context
            prompt = self._create_rich_media_expansion_prompt(content, channel, media_elements)
            response = await self._call_bedrock_claude(prompt)
            
            expanded_content = self._extract_content_from_response(response)
            return expanded_content
            
        except Exception as e:
            logger.error(f"Claude rich media expansion failed: {e}")
            return await super().expand_for_rich_media(content, channel)

    async def generate_template_content(
        self, 
        message_type: MessageType, 
        channel: ChannelType, 
        data: Dict[str, Any],
        media: List[MediaElement] = None
    ) -> AdaptationResult:
        """Generate content using templates enhanced with Claude intelligence."""
        try:
            # First try template-based generation
            template_content = await self.generate_from_template(message_type, channel, data, media or [])
            
            if self.bedrock_runtime and template_content:
                # Enhance template content with Claude
                prompt = self._create_template_enhancement_prompt(template_content, channel, data)
                enhanced_response = await self._call_bedrock_claude(prompt)
                enhanced_content = self._extract_content_from_response(enhanced_response)
                
                # Create adaptation result
                modifications = [ContentChange(
                    change_type="claude_template_enhancement",
                    original_text=template_content,
                    modified_text=enhanced_content,
                    reason="Enhanced template content with Claude intelligence"
                )]
                
                return AdaptationResult(
                    adapted_content=enhanced_content,
                    preserved_elements=self._extract_key_elements(template_content),
                    modifications=modifications,
                    quality_score=0.9  # High quality for template + Claude
                )
            else:
                # Fallback to template only
                return AdaptationResult(
                    adapted_content=template_content,
                    preserved_elements=self._extract_key_elements(template_content),
                    modifications=[],
                    quality_score=0.8  # Good quality for template only
                )
                
        except Exception as e:
            logger.error(f"Template content generation failed: {e}")
            # Final fallback
            basic_content = self._generate_basic_content(message_type, channel, data)
            return AdaptationResult(
                adapted_content=basic_content,
                preserved_elements=[],
                modifications=[],
                quality_score=0.6  # Lower quality for basic fallback
            )

    async def _adapt_with_bedrock(self, request: AdaptationRequest) -> AdaptationResult:
        """Perform content adaptation using Bedrock Claude."""
        original_content = request.original_content.strip()
        target_channel = request.target_channel
        max_length = request.max_length or self.channel_limits[target_channel]
        
        # Create adaptation prompt
        prompt = self._create_adaptation_prompt(request)
        
        # Call Claude
        response = await self._call_bedrock_claude(prompt)
        
        # Parse Claude's response
        adaptation_data = self._parse_claude_adaptation_response(response)
        
        # Extract key elements
        preserved_elements = self._extract_key_elements(original_content)
        
        # Create modifications list
        modifications = self._create_modifications_from_claude_response(
            original_content, adaptation_data
        )
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            original_content, adaptation_data.get('adapted_content', ''), preserved_elements
        )
        
        return AdaptationResult(
            adapted_content=adaptation_data.get('adapted_content', original_content),
            preserved_elements=preserved_elements,
            modifications=modifications,
            quality_score=quality_score,
        )

    async def _call_bedrock_claude(self, prompt: str) -> str:
        """Call Bedrock Claude with the given prompt."""
        try:
            # Prepare the request body for Claude
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.claude_model_id,
                body=json.dumps(body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                return response_body['content'][0]['text']
            else:
                raise ValueError("Invalid response format from Claude")
                
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS Bedrock error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Bedrock: {e}")
            raise

    def _create_adaptation_prompt(self, request: AdaptationRequest) -> str:
        """Create a comprehensive adaptation prompt for Claude."""
        channel_guidance = {
            ChannelType.SMS: "SMS (160 characters max): Be concise, use abbreviations, preserve key info",
            ChannelType.WHATSAPP: "WhatsApp: Use emojis, line breaks, conversational tone",
            ChannelType.EMAIL: "Email: Professional format, proper greeting/closing, detailed",
            ChannelType.VOICE: "Voice: Conversational, easy to pronounce, natural flow"
        }
        
        brand_info = ""
        if request.brand_guidelines:
            brand_info = f"\nBrand Guidelines: {json.dumps(request.brand_guidelines, indent=2)}"
        
        max_length_info = ""
        if request.max_length:
            max_length_info = f"\nMaximum length: {request.max_length} characters"
        
        prompt = f"""You are an expert content adaptation specialist. Adapt the following content for {request.target_channel.value}.

Original Content:
{request.original_content}

Channel Requirements:
{channel_guidance.get(request.target_channel, "Standard adaptation")}
{max_length_info}
{brand_info}

Please provide your response in the following JSON format:
{{
    "adapted_content": "The adapted content here",
    "key_changes": ["List of key changes made"],
    "preserved_elements": ["Important elements preserved"],
    "reasoning": "Brief explanation of adaptation strategy"
}}

Focus on:
1. Preserving key information (URLs, prices, contact info, codes)
2. Maintaining brand voice and tone
3. Optimizing for the target channel's characteristics
4. Ensuring the message remains clear and actionable"""

        return prompt

    def _create_sms_shrinking_prompt(self, content: str, max_length: int) -> str:
        """Create a specific prompt for SMS content shrinking."""
        prompt = f"""You are an expert at condensing content for SMS while preserving essential information.

Original Content ({len(content)} characters):
{content}

Requirements:
- Maximum {max_length} characters
- Preserve URLs, phone numbers, prices, and codes exactly
- Use common abbreviations (you→u, and→&, with→w/, etc.)
- Remove filler words but keep meaning clear
- Maintain urgency and call-to-action

Provide only the shortened content, no explanation needed."""

        return prompt

    def _create_expansion_prompt(self, content: str, channel: ChannelType) -> str:
        """Create a prompt for expanding content for rich media channels."""
        channel_specific = {
            ChannelType.EMAIL: "Add professional greeting, detailed explanation, proper closing, and clear call-to-action",
            ChannelType.WHATSAPP: "Add relevant emojis, use line breaks for readability, make it conversational",
            ChannelType.VOICE: "Make it sound natural when spoken, add pauses, use conversational language"
        }
        
        guidance = channel_specific.get(channel, "Expand with relevant details")
        
        prompt = f"""Expand the following content for {channel.value}:

Original Content:
{content}

Instructions:
{guidance}

Requirements:
- Keep all original key information (URLs, prices, contact details)
- Enhance readability and engagement
- Maintain professional tone
- Add value without being verbose

Provide only the expanded content."""

        return prompt

    def _create_rich_media_expansion_prompt(self, content: str, channel: ChannelType, media: List[MediaElement]) -> str:
        """Create a prompt for expanding content with rich media support."""
        channel_specific = {
            ChannelType.EMAIL: "Create professional HTML email with embedded media, proper structure, and clear call-to-action",
            ChannelType.WHATSAPP: "Add relevant emojis, use line breaks, include media references with appropriate descriptions",
            ChannelType.VOICE: "Make it sound natural when spoken, describe visual elements verbally"
        }
        
        guidance = channel_specific.get(channel, "Expand with relevant details and media integration")
        
        media_context = ""
        if media:
            media_descriptions = []
            for m in media:
                media_descriptions.append(f"- {m.media_type.value}: {m.url} ({m.alt_text or 'No description'})")
            media_context = f"\n\nAvailable Media:\n" + "\n".join(media_descriptions)
        
        prompt = f"""Expand the following content for {channel.value} with rich media integration:

Original Content:
{content}
{media_context}

Instructions:
{guidance}

Requirements:
- Integrate media elements naturally into the content
- Keep all original key information (URLs, prices, contact details)
- Enhance readability and engagement
- Maintain professional tone
- Add value without being verbose
- For email: Use proper HTML structure with media placeholders
- For WhatsApp: Reference media with emojis and descriptions

Provide only the expanded content with media integration."""

        return prompt

    def _create_template_enhancement_prompt(self, template_content: str, channel: ChannelType, data: Dict[str, Any]) -> str:
        """Create a prompt for enhancing template-generated content."""
        prompt = f"""Enhance the following template-generated content for {channel.value}:

Template Content:
{template_content}

Context Data:
{json.dumps(data, indent=2)}

Instructions:
- Improve the flow and readability
- Add personality while maintaining professionalism
- Ensure all placeholders are properly filled
- Optimize for {channel.value} best practices
- Keep the core message and structure intact
- Add subtle improvements to engagement

Provide only the enhanced content."""

        return prompt

    def _extract_content_from_response(self, response: str) -> str:
        """Extract content from Claude's response."""
        # Try to parse as JSON first
        try:
            data = json.loads(response)
            if 'adapted_content' in data:
                return data['adapted_content']
        except json.JSONDecodeError:
            pass
        
        # If not JSON, return the response as-is (for simple prompts)
        return response.strip()

    def _parse_claude_adaptation_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude's structured adaptation response."""
        try:
            data = json.loads(response)
            return data
        except json.JSONDecodeError:
            # Fallback: treat as plain text adaptation
            return {
                'adapted_content': response.strip(),
                'key_changes': ['Content adapted by Claude'],
                'preserved_elements': [],
                'reasoning': 'Claude adaptation without structured response'
            }

    def _create_modifications_from_claude_response(
        self, original: str, adaptation_data: Dict[str, Any]
    ) -> List[ContentChange]:
        """Create ContentChange objects from Claude's response."""
        modifications = []
        
        adapted_content = adaptation_data.get('adapted_content', '')
        key_changes = adaptation_data.get('key_changes', [])
        reasoning = adaptation_data.get('reasoning', '')
        
        # Create a general modification record
        if adapted_content != original:
            change_type = "claude_adaptation"
            if len(adapted_content) < len(original):
                change_type = "claude_shortened"
            elif len(adapted_content) > len(original):
                change_type = "claude_expanded"
            
            modifications.append(ContentChange(
                change_type=change_type,
                original_text=original,
                modified_text=adapted_content,
                reason=f"Claude adaptation: {reasoning}"
            ))
        
        # Add specific changes mentioned by Claude
        for change in key_changes:
            modifications.append(ContentChange(
                change_type="claude_specific_change",
                original_text="",
                modified_text="",
                reason=change
            ))
        
        return modifications

    async def analyze_content_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze content sentiment using AWS Comprehend."""
        if not self.comprehend:
            return {"sentiment": "NEUTRAL", "confidence": 0.5}
        
        try:
            response = self.comprehend.detect_sentiment(
                Text=content,
                LanguageCode='en'
            )
            
            return {
                "sentiment": response['Sentiment'],
                "confidence": response['SentimentScore'][response['Sentiment']],
                "scores": response['SentimentScore']
            }
        except Exception as e:
            logger.error(f"Comprehend sentiment analysis failed: {e}")
            return {"sentiment": "NEUTRAL", "confidence": 0.5}

    async def extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract entities from content using AWS Comprehend."""
        if not self.comprehend:
            return []
        
        try:
            response = self.comprehend.detect_entities(
                Text=content,
                LanguageCode='en'
            )
            
            return [
                {
                    "text": entity['Text'],
                    "type": entity['Type'],
                    "confidence": entity['Score']
                }
                for entity in response['Entities']
            ]
        except Exception as e:
            logger.error(f"Comprehend entity extraction failed: {e}")
            return []