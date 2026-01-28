"""Content templates and rich media adaptation utilities."""

import re
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from ...core.models import ChannelType, MessageType


class MediaType(str, Enum):
    """Types of media content."""
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    LINK_PREVIEW = "link_preview"


@dataclass
class MediaElement:
    """Represents a media element in content."""
    media_type: MediaType
    url: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None


@dataclass
class ContentTemplate:
    """Template for generating channel-specific content."""
    name: str
    message_type: MessageType
    channel: ChannelType
    template: str
    placeholders: List[str]
    media_slots: List[str]
    max_length: Optional[int] = None


class TemplateManager:
    """Manages content templates for different channels and message types."""
    
    def __init__(self):
        """Initialize the template manager with predefined templates."""
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict[str, ContentTemplate]:
        """Load default templates for different channels and message types."""
        templates = {}
        
        # SMS Templates
        templates["sms_promotional"] = ContentTemplate(
            name="SMS Promotional",
            message_type=MessageType.PROMOTIONAL,
            channel=ChannelType.SMS,
            template="🎉 {offer_text} Use code {promo_code} by {expiry_date}. {cta_url}",
            placeholders=["offer_text", "promo_code", "expiry_date", "cta_url"],
            media_slots=[],
            max_length=160
        )
        
        templates["sms_transactional"] = ContentTemplate(
            name="SMS Transactional",
            message_type=MessageType.TRANSACTIONAL,
            channel=ChannelType.SMS,
            template="{service_name}: {transaction_details}. Ref: {reference_id}",
            placeholders=["service_name", "transaction_details", "reference_id"],
            media_slots=[],
            max_length=160
        )
        
        # WhatsApp Templates
        templates["whatsapp_promotional"] = ContentTemplate(
            name="WhatsApp Promotional",
            message_type=MessageType.PROMOTIONAL,
            channel=ChannelType.WHATSAPP,
            template="""🎉 *{offer_title}*

{offer_description}

💰 *Special Offer:* {discount_details}
⏰ *Valid until:* {expiry_date}
🏷️ *Promo Code:* `{promo_code}`

{media_slot_1}

👆 Tap to shop now!

{cta_button}""",
            placeholders=["offer_title", "offer_description", "discount_details", "expiry_date", "promo_code", "cta_button"],
            media_slots=["media_slot_1"],
            max_length=4096
        )
        
        templates["whatsapp_support"] = ContentTemplate(
            name="WhatsApp Support",
            message_type=MessageType.SUPPORT,
            channel=ChannelType.WHATSAPP,
            template="""👋 Hi {customer_name},

{support_message}

📞 Need immediate help? Call us at {phone_number}
💬 Or reply to this message

We're here to help! 🤝

Best regards,
{agent_name}
{company_name} Support Team""",
            placeholders=["customer_name", "support_message", "phone_number", "agent_name", "company_name"],
            media_slots=[],
            max_length=4096
        )
        
        # Email Templates
        templates["email_promotional"] = ContentTemplate(
            name="Email Promotional",
            message_type=MessageType.PROMOTIONAL,
            channel=ChannelType.EMAIL,
            template="""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{email_subject}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2c3e50;">{offer_title}</h1>
        
        {media_slot_1}
        
        <p style="font-size: 16px;">{offer_description}</p>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #e74c3c; margin-top: 0;">🎉 Special Offer</h2>
            <p style="font-size: 18px; font-weight: bold;">{discount_details}</p>
            <p><strong>Promo Code:</strong> <code style="background-color: #fff; padding: 4px 8px; border-radius: 4px;">{promo_code}</code></p>
            <p><strong>Valid until:</strong> {expiry_date}</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{cta_url}" style="background-color: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                {cta_text}
            </a>
        </div>
        
        {media_slot_2}
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="font-size: 14px; color: #666;">
            Best regards,<br>
            {company_name} Team
        </p>
        
        <p style="font-size: 12px; color: #999;">
            You received this email because you subscribed to our newsletter. 
            <a href="{unsubscribe_url}">Unsubscribe</a>
        </p>
    </div>
</body>
</html>""",
            placeholders=["email_subject", "offer_title", "offer_description", "discount_details", 
                         "promo_code", "expiry_date", "cta_url", "cta_text", "company_name", "unsubscribe_url"],
            media_slots=["media_slot_1", "media_slot_2"],
            max_length=100000
        )
        
        templates["email_transactional"] = ContentTemplate(
            name="Email Transactional",
            message_type=MessageType.TRANSACTIONAL,
            channel=ChannelType.EMAIL,
            template="""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{email_subject}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2c3e50;">{transaction_title}</h1>
        
        <p>Dear {customer_name},</p>
        
        <p>{transaction_message}</p>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0;">Transaction Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Reference ID:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{reference_id}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Date:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{transaction_date}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Amount:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{amount}</td>
                </tr>
            </table>
        </div>
        
        {additional_details}
        
        <p>If you have any questions, please contact our support team at {support_email} or {support_phone}.</p>
        
        <p style="margin-top: 30px;">
            Best regards,<br>
            {company_name} Team
        </p>
    </div>
</body>
</html>""",
            placeholders=["email_subject", "transaction_title", "customer_name", "transaction_message",
                         "reference_id", "transaction_date", "amount", "additional_details",
                         "support_email", "support_phone", "company_name"],
            media_slots=[],
            max_length=100000
        )
        
        return templates
    
    def get_template(self, channel: ChannelType, message_type: MessageType) -> Optional[ContentTemplate]:
        """Get the appropriate template for a channel and message type."""
        template_key = f"{channel.value}_{message_type.value}"
        return self.templates.get(template_key)
    
    def render_template(self, template: ContentTemplate, data: Dict[str, Any], media: List[MediaElement] = None) -> str:
        """Render a template with the provided data and media."""
        content = template.template
        
        # Replace placeholders
        for placeholder in template.placeholders:
            value = data.get(placeholder, f"[{placeholder}]")
            content = content.replace(f"{{{placeholder}}}", str(value))
        
        # Replace media slots
        if media:
            for i, media_element in enumerate(media):
                slot_name = f"media_slot_{i+1}"
                if slot_name in template.media_slots:
                    media_html = self._generate_media_html(media_element, template.channel)
                    content = content.replace(f"{{{slot_name}}}", media_html)
        
        # Clean up unused media slots
        for slot in template.media_slots:
            content = content.replace(f"{{{slot}}}", "")
        
        return content
    
    def _generate_media_html(self, media: MediaElement, channel: ChannelType) -> str:
        """Generate HTML/markup for media elements based on channel."""
        if channel == ChannelType.EMAIL:
            if media.media_type == MediaType.IMAGE:
                alt_text = media.alt_text or "Image"
                caption = f"<p style='font-size: 14px; color: #666; text-align: center; margin-top: 10px;'>{media.caption}</p>" if media.caption else ""
                return f"""
                <div style="text-align: center; margin: 20px 0;">
                    <img src="{media.url}" alt="{alt_text}" style="max-width: 100%; height: auto; border-radius: 8px;">
                    {caption}
                </div>
                """
            elif media.media_type == MediaType.VIDEO:
                return f"""
                <div style="text-align: center; margin: 20px 0;">
                    <video controls style="max-width: 100%; height: auto; border-radius: 8px;">
                        <source src="{media.url}" type="video/mp4">
                        Your email client doesn't support video playback.
                    </video>
                    {f"<p style='font-size: 14px; color: #666; text-align: center; margin-top: 10px;'>{media.caption}</p>" if media.caption else ""}
                </div>
                """
            elif media.media_type == MediaType.LINK_PREVIEW:
                return f"""
                <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <a href="{media.url}" style="text-decoration: none; color: #333;">
                        <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{media.alt_text or "Link"}</h4>
                        <p style="margin: 0; color: #666; font-size: 14px;">{media.caption or "Click to view"}</p>
                    </a>
                </div>
                """
        
        elif channel == ChannelType.WHATSAPP:
            if media.media_type == MediaType.IMAGE:
                # WhatsApp supports direct image URLs
                caption_text = f"\n{media.caption}" if media.caption else ""
                return f"{media.url}{caption_text}"
            elif media.media_type == MediaType.VIDEO:
                caption_text = f"\n🎥 {media.caption}" if media.caption else "\n🎥 Video"
                return f"{media.url}{caption_text}"
            elif media.media_type == MediaType.DOCUMENT:
                caption_text = f"\n📄 {media.caption}" if media.caption else "\n📄 Document"
                return f"{media.url}{caption_text}"
        
        # Fallback: just return the URL
        return media.url


class RichMediaAdapter:
    """Handles rich media adaptation for different channels."""
    
    def __init__(self):
        """Initialize the rich media adapter."""
        self.template_manager = TemplateManager()
        self.url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    
    def extract_media_urls(self, content: str) -> List[str]:
        """Extract media URLs from content."""
        return self.url_pattern.findall(content)
    
    def classify_media_url(self, url: str) -> MediaType:
        """Classify a URL as a specific media type."""
        url_lower = url.lower()
        
        # Image extensions
        if any(url_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
            return MediaType.IMAGE
        
        # Video extensions
        if any(url_lower.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']):
            return MediaType.VIDEO
        
        # Document extensions
        if any(url_lower.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']):
            return MediaType.DOCUMENT
        
        # Audio extensions
        if any(url_lower.endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
            return MediaType.AUDIO
        
        # Default to link preview
        return MediaType.LINK_PREVIEW
    
    def create_media_elements(self, urls: List[str]) -> List[MediaElement]:
        """Create MediaElement objects from URLs."""
        media_elements = []
        
        for url in urls:
            media_type = self.classify_media_url(url)
            media_elements.append(MediaElement(
                media_type=media_type,
                url=url,
                alt_text=self._generate_alt_text(url, media_type),
                caption=self._generate_caption(url, media_type)
            ))
        
        return media_elements
    
    def _generate_alt_text(self, url: str, media_type: MediaType) -> str:
        """Generate appropriate alt text for media."""
        filename = url.split('/')[-1].split('?')[0]  # Extract filename without query params
        
        if media_type == MediaType.IMAGE:
            return f"Image: {filename}"
        elif media_type == MediaType.VIDEO:
            return f"Video: {filename}"
        elif media_type == MediaType.DOCUMENT:
            return f"Document: {filename}"
        elif media_type == MediaType.AUDIO:
            return f"Audio: {filename}"
        else:
            return f"Link: {filename}"
    
    def _generate_caption(self, url: str, media_type: MediaType) -> str:
        """Generate appropriate caption for media."""
        if media_type == MediaType.IMAGE:
            return "Click to view full image"
        elif media_type == MediaType.VIDEO:
            return "Click to play video"
        elif media_type == MediaType.DOCUMENT:
            return "Click to download document"
        elif media_type == MediaType.AUDIO:
            return "Click to play audio"
        else:
            return "Click to open link"
    
    def validate_media_url(self, url: str) -> bool:
        """Validate that a media URL is accessible and safe."""
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            'javascript:', 'data:', 'vbscript:', 'file:', 'ftp:'
        ]
        
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in suspicious_patterns):
            return False
        
        return True
    
    def optimize_media_for_channel(self, media: MediaElement, channel: ChannelType) -> MediaElement:
        """Optimize media element for specific channel constraints."""
        optimized = MediaElement(
            media_type=media.media_type,
            url=media.url,
            alt_text=media.alt_text,
            caption=media.caption,
            thumbnail_url=media.thumbnail_url
        )
        
        if channel == ChannelType.SMS:
            # SMS doesn't support rich media, convert to text
            optimized.url = f"View: {media.url}"
            optimized.caption = None
        
        elif channel == ChannelType.WHATSAPP:
            # WhatsApp has good media support, minimal optimization needed
            if media.media_type == MediaType.DOCUMENT and media.caption:
                # Ensure caption is not too long
                optimized.caption = media.caption[:100] + "..." if len(media.caption) > 100 else media.caption
        
        elif channel == ChannelType.EMAIL:
            # Email supports rich HTML, no optimization needed
            pass
        
        return optimized