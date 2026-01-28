"""Base content adaptation engine implementation."""

import logging
import re
from typing import Dict, List, Optional
from uuid import uuid4

from ...core.interfaces import (
    ContentAdaptationEngine,
    AdaptationRequest,
    AdaptationResult,
    ContentChange,
)
from ...core.models import ChannelType, BrandProfile, MessageType
from .templates import TemplateManager, RichMediaAdapter, MediaElement

logger = logging.getLogger(__name__)


class BaseContentAdaptationEngine(ContentAdaptationEngine):
    """Base implementation of the content adaptation engine."""

    def __init__(self):
        """Initialize the content adaptation engine."""
        self.channel_limits = {
            ChannelType.SMS: 160,
            ChannelType.WHATSAPP: 4096,
            ChannelType.EMAIL: 100000,  # Practically unlimited
            ChannelType.VOICE: 300,  # ~30 seconds of speech
        }
        
        # Initialize template and media managers
        self.template_manager = TemplateManager()
        self.media_adapter = RichMediaAdapter()
        
        # Key elements that should be preserved during adaptation
        self.preserve_patterns = [
            r'\b(?:https?://\S+|www\.\S+)\b',  # URLs
            r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b',  # Numbers/prices
            r'\b[A-Z][A-Z0-9]{2,}\b',  # Codes/SKUs
            r'#\w+',  # Hashtags
            r'@\w+',  # Mentions
            r'\b(?:call|text|email|visit)\s+(?:us\s+)?(?:at|on)?\s*[:\-]?\s*\S+',  # Contact info
        ]

    async def adapt_content(self, request: AdaptationRequest) -> AdaptationResult:
        """Adapt content for the target channel."""
        logger.info(f"Adapting content for {request.target_channel}")
        
        original_content = request.original_content.strip()
        target_channel = request.target_channel
        max_length = request.max_length or self.channel_limits[target_channel]
        
        # Extract key elements to preserve
        preserved_elements = self._extract_key_elements(original_content)
        
        # Determine adaptation strategy
        if len(original_content) <= max_length:
            # Content fits, minimal adaptation needed
            adapted_content = await self._minimal_adaptation(
                original_content, target_channel, request.brand_guidelines
            )
            modifications = []
        elif target_channel == ChannelType.SMS:
            # Shrink for SMS
            adapted_content = await self.shrink_for_sms(original_content, max_length)
            modifications = self._track_shrinking_changes(original_content, adapted_content)
        else:
            # Expand for rich media channels
            adapted_content = await self.expand_for_rich_media(original_content, target_channel)
            modifications = self._track_expansion_changes(original_content, adapted_content)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            original_content, adapted_content, preserved_elements
        )
        
        return AdaptationResult(
            adapted_content=adapted_content,
            preserved_elements=preserved_elements,
            modifications=modifications,
            quality_score=quality_score,
        )

    async def shrink_for_sms(self, content: str, max_length: int = 160) -> str:
        """Intelligently shrink content for SMS while preserving key elements."""
        logger.debug(f"Shrinking content from {len(content)} to {max_length} chars")
        
        if len(content) <= max_length:
            return content
        
        # Extract and preserve key elements
        key_elements = self._extract_key_elements(content)
        
        # Remove less important elements first
        shrunk = content
        
        # Step 1: Remove extra whitespace
        shrunk = re.sub(r'\s+', ' ', shrunk).strip()
        
        # Step 2: Remove common filler words
        filler_words = [
            r'\b(?:please|kindly|very|really|quite|rather|just|simply|actually|basically)\b',
            r'\b(?:in order to|for the purpose of)\b',
            r'\b(?:at this time|at the moment|currently)\b',
        ]
        for pattern in filler_words:
            if len(shrunk) > max_length:
                shrunk = re.sub(pattern, '', shrunk, flags=re.IGNORECASE)
                shrunk = re.sub(r'\s+', ' ', shrunk).strip()
        
        # Step 3: Abbreviate common phrases
        abbreviations = {
            r'\byou\b': 'u',
            r'\band\b': '&',
            r'\bwith\b': 'w/',
            r'\bwithout\b': 'w/o',
            r'\binformation\b': 'info',
            r'\bmessage\b': 'msg',
            r'\btomorrow\b': 'tmrw',
            r'\btonight\b': 'tnght',
            r'\bthrough\b': 'thru',
        }
        
        for pattern, replacement in abbreviations.items():
            if len(shrunk) > max_length:
                shrunk = re.sub(pattern, replacement, shrunk, flags=re.IGNORECASE)
        
        # Step 4: Remove articles and prepositions if still too long
        if len(shrunk) > max_length:
            articles = r'\b(?:the|a|an)\b'
            shrunk = re.sub(articles, '', shrunk, flags=re.IGNORECASE)
            shrunk = re.sub(r'\s+', ' ', shrunk).strip()
        
        # Step 5: Truncate sentences if necessary
        if len(shrunk) > max_length:
            sentences = shrunk.split('. ')
            result = ""
            for sentence in sentences:
                if len(result + sentence + '. ') <= max_length:
                    result += sentence + '. '
                else:
                    break
            shrunk = result.strip()
            if shrunk.endswith('.'):
                shrunk = shrunk[:-1]  # Remove trailing period if we truncated
        
        # Final truncation if still too long
        if len(shrunk) > max_length:
            shrunk = shrunk[:max_length-3] + '...'
        
        return shrunk

    async def expand_for_rich_media(self, content: str, channel: ChannelType) -> str:
        """Expand content with rich media for email/WhatsApp."""
        logger.debug(f"Expanding content for {channel}")
        
        # Extract media URLs from content
        media_urls = self.media_adapter.extract_media_urls(content)
        media_elements = self.media_adapter.create_media_elements(media_urls)
        
        # Optimize media for the target channel
        optimized_media = [
            self.media_adapter.optimize_media_for_channel(media, channel)
            for media in media_elements
        ]
        
        expanded = content
        
        if channel == ChannelType.EMAIL:
            # Add email-specific formatting with rich media support
            expanded = self._add_email_formatting_with_media(expanded, optimized_media)
        elif channel == ChannelType.WHATSAPP:
            # Add WhatsApp-specific formatting with media support
            expanded = self._add_whatsapp_formatting_with_media(expanded, optimized_media)
        
        return expanded

    async def generate_from_template(
        self, 
        message_type: MessageType, 
        channel: ChannelType, 
        data: Dict[str, any],
        media: List[MediaElement] = None
    ) -> str:
        """Generate content using predefined templates."""
        template = self.template_manager.get_template(channel, message_type)
        
        if template:
            return self.template_manager.render_template(template, data, media or [])
        else:
            # Fallback to basic content generation
            return self._generate_basic_content(message_type, channel, data)

    async def _minimal_adaptation(
        self, content: str, channel: ChannelType, brand_guidelines: Optional[Dict] = None
    ) -> str:
        """Apply minimal channel-specific adaptations."""
        adapted = content
        
        if channel == ChannelType.SMS:
            # Ensure SMS-friendly formatting
            adapted = re.sub(r'\n+', ' ', adapted)  # Remove line breaks
            adapted = re.sub(r'\s+', ' ', adapted).strip()  # Normalize whitespace
        elif channel == ChannelType.EMAIL:
            # Ensure proper email formatting
            if not adapted.endswith('.'):
                adapted += '.'
        elif channel == ChannelType.WHATSAPP:
            # WhatsApp supports emojis and formatting
            adapted = self._add_whatsapp_formatting(adapted)
        
        return adapted

    def _extract_key_elements(self, content: str) -> List[str]:
        """Extract key elements that should be preserved during adaptation."""
        key_elements = []
        
        for pattern in self.preserve_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            key_elements.extend(matches)
        
        return list(set(key_elements))  # Remove duplicates

    def _add_email_formatting(self, content: str) -> str:
        """Add email-specific formatting and structure."""
        # Add proper greeting if missing
        if not re.match(r'^(?:dear|hello|hi|greetings)', content, re.IGNORECASE):
            content = "Dear Valued Customer,\n\n" + content
        
        # Add proper closing if missing
        if not re.search(r'(?:sincerely|regards|best|thank you)', content, re.IGNORECASE):
            content += "\n\nBest regards,\nYour Customer Service Team"
        
        # Add call-to-action section
        if 'http' in content or 'www' in content:
            content += "\n\n[Click here to learn more]"
        
        return content

    def _add_whatsapp_formatting(self, content: str) -> str:
        """Add WhatsApp-specific formatting."""
        # Add emojis for better engagement
        if 'offer' in content.lower() or 'sale' in content.lower():
            content = "🎉 " + content
        elif 'urgent' in content.lower() or 'important' in content.lower():
            content = "⚠️ " + content
        elif 'thank' in content.lower():
            content = "🙏 " + content
        
        # Format for WhatsApp readability
        content = content.replace('. ', '.\n\n')  # Add line breaks after sentences
        
        return content

    def _add_email_formatting_with_media(self, content: str, media: List[MediaElement]) -> str:
        """Add email-specific formatting with rich media support."""
        # Start with basic email formatting
        formatted = self._add_email_formatting(content)
        
        # Insert media elements at appropriate positions
        if media:
            # Find a good position to insert media (after first paragraph)
            paragraphs = formatted.split('\n\n')
            if len(paragraphs) > 1:
                # Insert media after first paragraph
                media_html = self._generate_media_html_for_email(media)
                paragraphs.insert(1, media_html)
                formatted = '\n\n'.join(paragraphs)
        
        return formatted

    def _add_whatsapp_formatting_with_media(self, content: str, media: List[MediaElement]) -> str:
        """Add WhatsApp-specific formatting with media support."""
        # Start with basic WhatsApp formatting
        formatted = self._add_whatsapp_formatting(content)
        
        # Add media URLs at the end for WhatsApp
        if media:
            media_text = self._generate_media_text_for_whatsapp(media)
            if media_text:
                formatted += f"\n\n{media_text}"
        
        return formatted

    def _generate_media_html_for_email(self, media: List[MediaElement]) -> str:
        """Generate HTML for media elements in email."""
        html_parts = []
        
        for media_element in media:
            if media_element.media_type.value == "image":
                alt_text = media_element.alt_text or "Image"
                caption = f"<p style='font-size: 14px; color: #666; text-align: center; margin-top: 10px;'>{media_element.caption}</p>" if media_element.caption else ""
                html_parts.append(f"""
                <div style="text-align: center; margin: 20px 0;">
                    <img src="{media_element.url}" alt="{alt_text}" style="max-width: 100%; height: auto; border-radius: 8px;">
                    {caption}
                </div>
                """)
            elif media_element.media_type.value == "link_preview":
                html_parts.append(f"""
                <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <a href="{media_element.url}" style="text-decoration: none; color: #333;">
                        <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{media_element.alt_text or "Link"}</h4>
                        <p style="margin: 0; color: #666; font-size: 14px;">{media_element.caption or "Click to view"}</p>
                    </a>
                </div>
                """)
        
        return '\n'.join(html_parts)

    def _generate_media_text_for_whatsapp(self, media: List[MediaElement]) -> str:
        """Generate text representation of media for WhatsApp."""
        media_parts = []
        
        for media_element in media:
            if media_element.media_type.value == "image":
                emoji = "🖼️"
            elif media_element.media_type.value == "video":
                emoji = "🎥"
            elif media_element.media_type.value == "document":
                emoji = "📄"
            elif media_element.media_type.value == "audio":
                emoji = "🎵"
            else:
                emoji = "🔗"
            
            caption_text = f" - {media_element.caption}" if media_element.caption else ""
            media_parts.append(f"{emoji} {media_element.url}{caption_text}")
        
        return '\n'.join(media_parts)

    def _generate_basic_content(self, message_type: MessageType, channel: ChannelType, data: Dict[str, any]) -> str:
        """Generate basic content when no template is available."""
        # Simple fallback content generation
        if message_type == MessageType.PROMOTIONAL:
            return f"Special offer: {data.get('offer', 'Great deals available!')} Visit: {data.get('url', 'our website')}"
        elif message_type == MessageType.TRANSACTIONAL:
            return f"Transaction update: {data.get('message', 'Your transaction has been processed.')} Ref: {data.get('ref', 'N/A')}"
        elif message_type == MessageType.SUPPORT:
            return f"Support message: {data.get('message', 'We are here to help you.')} Contact: {data.get('contact', 'support team')}"
        else:
            return data.get('message', 'Thank you for your interest.')

    def _track_shrinking_changes(self, original: str, adapted: str) -> List[ContentChange]:
        """Track changes made during content shrinking."""
        changes = []
        
        if len(adapted) < len(original):
            changes.append(ContentChange(
                change_type="shortened",
                original_text=original,
                modified_text=adapted,
                reason=f"Reduced from {len(original)} to {len(adapted)} characters for SMS"
            ))
        
        # Check for specific modifications
        if '&' in adapted and ' and ' in original:
            changes.append(ContentChange(
                change_type="abbreviated",
                original_text=" and ",
                modified_text=" & ",
                reason="Abbreviated 'and' to '&' for space saving"
            ))
        
        if 'u' in adapted and ' you ' in original:
            changes.append(ContentChange(
                change_type="abbreviated",
                original_text=" you ",
                modified_text=" u ",
                reason="Abbreviated 'you' to 'u' for space saving"
            ))
        
        return changes

    def _track_expansion_changes(self, original: str, adapted: str) -> List[ContentChange]:
        """Track changes made during content expansion."""
        changes = []
        
        if len(adapted) > len(original):
            changes.append(ContentChange(
                change_type="expanded",
                original_text=original,
                modified_text=adapted,
                reason=f"Expanded from {len(original)} to {len(adapted)} characters for rich media"
            ))
        
        # Check for specific additions
        if "Dear Valued Customer" in adapted and "Dear Valued Customer" not in original:
            changes.append(ContentChange(
                change_type="greeting_added",
                original_text="",
                modified_text="Dear Valued Customer,",
                reason="Added professional greeting for email format"
            ))
        
        if "Best regards" in adapted and "Best regards" not in original:
            changes.append(ContentChange(
                change_type="closing_added",
                original_text="",
                modified_text="Best regards, Your Customer Service Team",
                reason="Added professional closing for email format"
            ))
        
        return changes

    def _calculate_quality_score(
        self, original: str, adapted: str, preserved_elements: List[str]
    ) -> float:
        """Calculate quality score for the adaptation."""
        score = 1.0
        
        # Check if key elements are preserved
        preserved_count = 0
        for element in preserved_elements:
            if element in adapted:
                preserved_count += 1
        
        if preserved_elements:
            preservation_ratio = preserved_count / len(preserved_elements)
            score *= preservation_ratio
        
        # Penalize excessive length changes
        length_ratio = len(adapted) / len(original) if len(original) > 0 else 1.0
        if length_ratio > 2.0 or length_ratio < 0.3:
            score *= 0.8  # Penalize extreme length changes
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))