"""Automatic message content generator for campaigns."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class CampaignMessageGenerator:
    """Generates personalized campaign messages based on customer and promotion data."""
    
    def __init__(self):
        """Initialize the message generator."""
        self.whatsapp_templates = self._load_whatsapp_templates()
    
    def _load_whatsapp_templates(self) -> Dict:
        """Load WhatsApp templates from JSON file."""
        # Try multiple possible paths
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "data" / "demo" / "whatsapp_templates.json",
            Path("data/demo/whatsapp_templates.json"),
            Path(__file__).parent.parent.parent / "data" / "demo" / "whatsapp_templates.json"
        ]
        
        for templates_file in possible_paths:
            try:
                if templates_file.exists():
                    with open(templates_file, 'r') as f:
                        data = json.load(f)
                    print(f"✅ Loaded WhatsApp templates from: {templates_file}")
                    return {t['template_id']: t for t in data['templates']}
            except Exception as e:
                continue
        
        print(f"⚠️  Warning: Could not load WhatsApp templates from any path")
        return {}
    
    def generate_message(
        self,
        customer_data: Dict,
        promotion_data: Optional[Dict] = None,
        channel: str = "sms",
        query_text: str = ""
    ) -> Dict[str, str]:
        """
        Generate personalized message content for a customer.
        
        Args:
            customer_data: Customer profile with first_name, location, etc.
            promotion_data: Promotion details from RAG (discount, product_name, etc.)
            channel: Communication channel (sms, whatsapp, email)
            query_text: Original campaign query for context
            
        Returns:
            Dictionary with 'subject' (for email) and 'content' keys
        """
        # Extract customer info
        first_name = customer_data.get('first_name', 'Valued Customer')
        location = customer_data.get('location', 'your area')
        
        # Extract promotion info
        if promotion_data:
            product_name = promotion_data.get('product_name', 'our products')
            discount = promotion_data.get('discount_percentage', '20')
            sku = promotion_data.get('sku', '')
            description = promotion_data.get('description', '')
        else:
            # Fallback if no promotion data
            product_name = 'our products'
            discount = '20'
            sku = ''
            description = ''
        
        # Generate content based on channel
        result = {}
        template_id = None
        
        if channel.lower() == 'sms':
            content = self._generate_sms(first_name, product_name, discount, location)
            result = {'content': content}
        
        elif channel.lower() == 'whatsapp':
            content = self._generate_whatsapp(first_name, product_name, discount, location, description)
            result = {'content': content}
            # Extract template ID and add template variables
            template_id = self._extract_template_id(discount)
            result['template_id'] = template_id
            result['template_variables'] = self._get_template_variables(
                template_id, first_name, location, discount, product_name, description, sku
            )
        
        elif channel.lower() == 'email':
            subject, content = self._generate_email(first_name, product_name, discount, location, description)
            result = {'subject': subject, 'content': content}
        
        else:
            # Default to SMS format
            content = self._generate_sms(first_name, product_name, discount, location)
            result = {'content': content}
        
        return result
    
    def _extract_template_id(self, discount: str) -> str:
        """Extract template ID based on discount level."""
        try:
            discount_int = int(discount)
        except (ValueError, TypeError):
            discount_int = 20
        
        if discount_int >= 30:
            return "promotional_urgent_v1"
        elif discount_int >= 20:
            return "promotional_discount_v1"
        else:
            return "promotional_simple_v1"
    
    def _get_template_variables(
        self,
        template_id: str,
        first_name: str,
        location: str,
        discount: str,
        product_name: str,
        description: str,
        sku: str
    ) -> Dict:
        """Get template variables for AWS End User Messaging API."""
        if template_id == "promotional_urgent_v1":
            return {
                "1": first_name,
                "2": str(discount),
                "3": product_name,
                "4": location,
                "5": "15",  # stock_count
                "6": "6",   # hours_remaining
                "7": description or "Amazing deal!"
            }
        elif template_id == "promotional_discount_v1":
            return {
                "1": location,  # header
                "2": first_name,  # body greeting
                "3": location,  # body location
                "4": str(discount),
                "5": product_name,
                "6": description or "Great product!",
                "7": sku or "product"  # URL parameter
            }
        else:  # promotional_simple_v1
            return {
                "1": first_name,
                "2": str(discount),
                "3": product_name,
                "4": location
            }
    
    def _generate_sms(self, first_name: str, product_name: str, discount: str, location: str) -> str:
        """Generate SMS message (160 chars limit)."""
        return f"Hi {first_name}! 🎉 {discount}% OFF on {product_name} in {location}! Limited time offer. Shop now!"
    
    def _generate_whatsapp(
        self, first_name: str, product_name: str, discount: str, location: str, description: str
    ) -> str:
        """Generate WhatsApp message with template ID and rich formatting."""
        # Convert discount to int for comparison
        try:
            discount_int = int(discount)
        except (ValueError, TypeError):
            discount_int = 20
        
        # Select template based on discount level
        if discount_int >= 30:
            template_id = "promotional_urgent_v1"
        elif discount_int >= 20:
            template_id = "promotional_discount_v1"
        else:
            template_id = "promotional_simple_v1"
        
        # Build message preview (what the customer will see)
        if template_id == "promotional_urgent_v1":
            message = f"""⚡ FLASH SALE ALERT!

{first_name}, hurry! ⏰

*{discount}% OFF* on {product_name}
📍 Available in {location}

🔥 Only 15 units left!
⏳ Ends in 6 hours!

{description}

Don't miss this amazing deal!

Reply STOP to unsubscribe.

---
📋 Template ID: {template_id}
🔧 AWS End User Messaging Template"""
        elif template_id == "promotional_discount_v1":
            message = f"""🎉 Exclusive Offer for {location}!

Hello {first_name}! 👋

We have an *exclusive offer* just for you in {location}!

🎁 Get *{discount}% OFF* on {product_name}!

✨ {description}

⏰ Limited time offer - Don't miss out!
🛒 Shop now and save big!

Reply STOP to unsubscribe.

---
📋 Template ID: {template_id}
🔧 AWS End User Messaging Template
🔗 Shop Now: https://example.com/shop/product"""
        else:  # promotional_simple_v1
            message = f"""🎁 Special Offer!

Hi {first_name}! 🎉

*{discount}% OFF* on {product_name} in {location}!

Limited time offer. Shop now!

Reply STOP to unsubscribe.

---
📋 Template ID: {template_id}
🔧 AWS End User Messaging Template
🔗 View Offer: https://example.com/offers"""
        
        return message
    
    def _generate_email(
        self, first_name: str, product_name: str, discount: str, location: str, description: str
    ) -> tuple:
        """Generate email subject and body."""
        subject = f"{first_name}, {discount}% OFF on {product_name} - Exclusive {location} Offer!"
        
        body = f"""
Dear {first_name},

We have an exclusive offer just for you in {location}!

🎉 GET {discount}% OFF ON {product_name.upper()}! 🎉

{description if description else f'Enjoy amazing savings on {product_name} with our limited-time promotion.'}

This special offer is available for a limited time only, so don't miss out!

Why shop with us?
✓ Premium quality products
✓ Fast delivery to {location}
✓ Secure payment options
✓ 30-day return policy

Click below to shop now and claim your discount!

[SHOP NOW]

Best regards,
Your Shopping Team

---
This is a promotional message. If you wish to unsubscribe, click here.
        """.strip()
        
        return subject, body
    
    def generate_batch_messages(
        self,
        customers: List[Dict],
        promotion_data: Optional[Dict] = None,
        channel: str = "sms",
        query_text: str = ""
    ) -> List[Dict]:
        """
        Generate messages for multiple customers.
        
        Returns:
            List of dicts with customer_id, external_id, and message content
        """
        messages = []
        
        for customer in customers:
            message = self.generate_message(customer, promotion_data, channel, query_text)
            messages.append({
                'customer_id': customer.get('customer_id'),
                'external_id': customer.get('external_id'),
                'first_name': customer.get('first_name'),
                'location': customer.get('location'),
                'channel': channel,
                **message
            })
        
        return messages
