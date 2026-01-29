#!/usr/bin/env python3
"""
Example: AWS End User Messaging with Rate Limiting

This script demonstrates how to send campaign messages using AWS End User Messaging
with intelligent rate limiting and throughput management.

Run in dry-run mode (no actual AWS calls):
    python3 example_aws_messaging.py --dry-run

Run with actual AWS integration:
    python3 example_aws_messaging.py --phone-pool-id pool-abc123 --whatsapp-account waba-xyz789
"""

import sys
import time
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_cpaas_demo.messaging import (
    AWSEndUserMessaging,
    ThroughputManager,
    DeliveryTracker,
    MessageRequest,
    Channel,
    DeliveryStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def send_campaign_with_rate_limiting(
    customers,
    messaging_client,
    throughput_manager,
    delivery_tracker,
    campaign_id='demo-campaign'
):
    """
    Send campaign messages with intelligent rate limiting.
    
    Args:
        customers: List of customer dictionaries
        messaging_client: AWSEndUserMessaging instance
        throughput_manager: ThroughputManager instance
        delivery_tracker: DeliveryTracker instance
        campaign_id: Campaign identifier
    """
    logger.info(f"🚀 Starting campaign: {campaign_id}")
    logger.info(f"📊 Total customers: {len(customers)}")
    
    sent_count = 0
    throttled_count = 0
    failed_count = 0
    
    for i, customer in enumerate(customers, 1):
        # Determine channel (simplified - in production use AI prediction)
        channel = customer.get('preferred_channel', 'sms').upper()
        channel_enum = Channel.WHATSAPP if channel == 'WHATSAPP' else Channel.SMS
        
        # Check rate limit before sending
        can_send, retry_after = throughput_manager.can_send(channel_enum, count=1)
        
        if not can_send:
            throttled_count += 1
            logger.warning(f"⏳ Rate limit reached. Waiting {retry_after:.2f}s...")
            time.sleep(retry_after)
            
            # Try again after waiting
            can_send, _ = throughput_manager.can_send(channel_enum, count=1)
        
        if can_send:
            # Create message request
            if channel == 'WHATSAPP':
                request = MessageRequest(
                    channel='WHATSAPP',
                    destination_phone_number=customer['phone'],
                    template_name='promotional_discount_v1',
                    template_parameters={
                        '1': customer.get('location', 'Seattle'),
                        '2': customer.get('first_name', 'Customer'),
                        '3': customer.get('location', 'Seattle'),
                        '4': '25',
                        '5': 'Premium Laptop',
                        '6': 'Amazing deal on premium laptops!',
                        '7': 'laptop'
                    },
                    campaign_id=campaign_id,
                    customer_id=customer['customer_id'],
                    metadata={'promotion_id': 'promo-123'}
                )
            else:  # SMS
                request = MessageRequest(
                    channel='SMS',
                    destination_phone_number=customer['phone'],
                    message_body=f"Hi {customer.get('first_name', 'Customer')}! 🎉 25% OFF on Premium Laptop in {customer.get('location', 'Seattle')}! Limited time offer. Shop now!",
                    campaign_id=campaign_id,
                    customer_id=customer['customer_id'],
                    metadata={'promotion_id': 'promo-123'}
                )
            
            # Send message
            response = messaging_client.send_message(request)
            
            if response.success:
                sent_count += 1
                
                # Record successful send
                delivery_tracker.record_sent(
                    message_id=response.message_id,
                    customer_id=customer['customer_id'],
                    channel=channel.lower(),
                    destination=customer['phone'],
                    metadata={'campaign_id': campaign_id}
                )
                
                logger.info(
                    f"✅ [{i}/{len(customers)}] Sent {channel} to {customer['customer_id']} "
                    f"(Message ID: {response.message_id})"
                )
            else:
                failed_count += 1
                logger.error(
                    f"❌ [{i}/{len(customers)}] Failed to send to {customer['customer_id']}: "
                    f"{response.error_message}"
                )
                
                if response.throttled:
                    throttled_count += 1
                    time.sleep(response.retry_after or 60)
        
        # Progress update every 10 messages
        if i % 10 == 0:
            logger.info(f"📊 Progress: {i}/{len(customers)} processed")
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 Campaign Summary")
    logger.info("=" * 80)
    logger.info(f"✅ Successfully sent: {sent_count}")
    logger.info(f"❌ Failed: {failed_count}")
    logger.info(f"⏳ Throttled: {throttled_count}")
    logger.info(f"📈 Success rate: {(sent_count / len(customers) * 100):.1f}%")
    logger.info("=" * 80 + "\n")
    
    # Show throughput stats
    show_throughput_stats(throughput_manager)
    
    # Show delivery stats
    show_delivery_stats(delivery_tracker)


def show_throughput_stats(throughput_manager):
    """Display throughput statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("⚡ Throughput Statistics")
    logger.info("=" * 80)
    
    for channel in [Channel.SMS, Channel.WHATSAPP]:
        stats = throughput_manager.get_throughput_stats(channel)
        logger.info(f"""
{channel.value.upper()}:
  • Available Capacity: {stats['available_capacity']} messages
  • Max Capacity: {stats['max_capacity']} messages
  • Rate Limit: {stats['rate_per_second']} msg/sec
  • Utilization: {stats['utilization_percent']:.1f}%
        """)
    
    logger.info("=" * 80 + "\n")


def show_delivery_stats(delivery_tracker):
    """Display delivery statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("📊 Delivery Statistics")
    logger.info("=" * 80)
    
    all_stats = delivery_tracker.get_all_stats()
    
    for channel, stats in all_stats.items():
        logger.info(f"""
{channel.upper()}:
  • Total Sent: {stats.total_sent}
  • Delivered: {stats.total_delivered} ({stats.delivery_rate:.1f}%)
  • Failed: {stats.total_failed}
  • Bounced: {stats.total_bounced}
  • Complained: {stats.total_complained}
        """)
    
    logger.info("=" * 80 + "\n")


def simulate_delivery_updates(delivery_tracker, message_ids):
    """Simulate delivery status updates (for demo purposes)."""
    import random
    
    logger.info("🔄 Simulating delivery status updates...")
    
    for message_id in message_ids[:10]:  # Update first 10 for demo
        # Simulate delivery with 90% success rate
        if random.random() < 0.9:
            delivery_tracker.update_status(message_id, DeliveryStatus.DELIVERED)
        else:
            delivery_tracker.update_status(
                message_id,
                DeliveryStatus.FAILED,
                error_code='INVALID_NUMBER',
                error_message='Invalid phone number'
            )
        
        time.sleep(0.1)  # Simulate delay
    
    logger.info("✅ Delivery updates complete")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='AWS End User Messaging Example')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual AWS calls)')
    parser.add_argument('--phone-pool-id', help='AWS phone pool ID for SMS')
    parser.add_argument('--whatsapp-account', help='WhatsApp Business Account ID')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--num-customers', type=int, default=50, help='Number of customers to send to')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.dry_run and (not args.phone_pool_id or not args.whatsapp_account):
        logger.error("❌ --phone-pool-id and --whatsapp-account are required when not in dry-run mode")
        sys.exit(1)
    
    logger.info("\n" + "=" * 80)
    logger.info("🚀 AWS End User Messaging Example")
    logger.info("=" * 80)
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    logger.info(f"Region: {args.region}")
    logger.info(f"Customers: {args.num_customers}")
    logger.info("=" * 80 + "\n")
    
    # Initialize components
    logger.info("🔧 Initializing components...")
    
    messaging_client = AWSEndUserMessaging(
        region_name=args.region,
        phone_pool_id=args.phone_pool_id,
        whatsapp_business_account_id=args.whatsapp_account,
        dry_run=args.dry_run
    )
    
    throughput_manager = ThroughputManager(
        use_dynamodb=not args.dry_run,
        dry_run=args.dry_run
    )
    
    delivery_tracker = DeliveryTracker(
        use_dynamodb=not args.dry_run,
        dry_run=args.dry_run
    )
    
    logger.info("✅ Components initialized\n")
    
    # Generate sample customers
    logger.info("📝 Generating sample customers...")
    customers = []
    for i in range(args.num_customers):
        customers.append({
            'customer_id': f'CUST-{i:04d}',
            'first_name': f'Customer{i}',
            'phone': f'+1555000{i:04d}',
            'location': ['Seattle', 'Portland', 'San Francisco', 'Los Angeles'][i % 4],
            'preferred_channel': 'whatsapp' if i % 3 == 0 else 'sms'
        })
    
    logger.info(f"✅ Generated {len(customers)} customers\n")
    
    # Send campaign
    send_campaign_with_rate_limiting(
        customers,
        messaging_client,
        throughput_manager,
        delivery_tracker,
        campaign_id='demo-campaign-001'
    )
    
    # In dry-run mode, simulate some delivery updates
    if args.dry_run:
        message_ids = [f'dry-run-msg-{i}' for i in range(args.num_customers)]
        simulate_delivery_updates(delivery_tracker, message_ids)
        show_delivery_stats(delivery_tracker)
    
    logger.info("✅ Example complete!")


if __name__ == '__main__':
    main()
