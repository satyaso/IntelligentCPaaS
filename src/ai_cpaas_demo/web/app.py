"""
Flask web application for AI-CPaaS demo.

Provides a simple web UI for business users to run campaign queries.
"""

import os
import sys
import time
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_cpaas_demo.data.demo_query import DemoQueryEngine

# Environment detection
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production'

# Initialize AWS clients only in production
if IS_PRODUCTION:
    from ai_cpaas_demo.messaging.aws_messaging import AWSEndUserMessaging, MessageRequest
    from ai_cpaas_demo.messaging.aws_ses import AWSSESClient
    from ai_cpaas_demo.messaging.rate_limiter import RateLimiter, RateLimitConfig, Channel
    from ai_cpaas_demo.messaging.delivery_tracker import DeliveryTracker
    
    # Initialize AWS clients
    aws_messaging = AWSEndUserMessaging(
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        phone_pool_id=os.getenv('PHONE_POOL_ID'),
        whatsapp_business_account_id=os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID'),
        dry_run=False
    )
    
    aws_ses = AWSSESClient(
        region=os.getenv('AWS_REGION', 'us-east-1'),
        sender_email=os.getenv('SENDER_EMAIL', 'noreply@example.com'),
        dry_run=False
    )
    
    delivery_tracker = DeliveryTracker(
        use_dynamodb=True,
        table_name=os.getenv('DELIVERY_TRACKING_TABLE', 'ai-cpaas-demo-delivery-tracking-dev'),
        dry_run=False
    )
    
    logging.info("✅ AWS clients initialized for production")
else:
    aws_messaging = None
    aws_ses = None
    delivery_tracker = None
    logging.info("🔧 Running in local mode - AWS clients disabled")

app = Flask(__name__)
CORS(app)

# Initialize demo engine (loads data once at startup)
print("Initializing demo engine...")
demo_engine = DemoQueryEngine()
print("✅ Demo engine ready!")


@app.route('/')
def index():
    """Render the main demo page."""
    return render_template('index.html')


@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get available locations."""
    stats = demo_engine.seeder.get_statistics()
    locations = list(stats['locations'].keys())
    return jsonify({
        'locations': sorted(locations),
        'total_customers': stats['total_customers']
    })


@app.route('/api/skus', methods=['GET'])
def get_skus():
    """Get available product SKUs."""
    # Access the SKU dictionary directly from seeder
    skus = list(demo_engine.seeder.customers_by_sku.keys())
    return jsonify({
        'skus': sorted(skus),
        'total_skus': len(skus)
    })


@app.route('/api/query', methods=['POST'])
def run_query():
    """
    Run a campaign query.
    
    Expected JSON body:
    {
        "location": "Bangalore",
        "sku": "SKU-LAPTOP-001",
        "natural_language_query": "Run campaign for SKU-Camera-006 for Bangalore users who are more than age 40",
        "filters": {  // Optional
            "min_purchases": 1,
            "category": "Electronics",
            "has_cart_items": true
        }
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    location = data.get('location')
    sku = data.get('sku')
    additional_filters = data.get('filters', {})
    natural_language_query = data.get('natural_language_query', '')
    
    if not location or not sku:
        return jsonify({'error': 'Both location and sku are required'}), 400
    
    try:
        # Run the campaign query with optional filters and NL query
        results = demo_engine.run_campaign_query(location, sku, additional_filters, natural_language_query)
        
        # Format response for web UI
        response = {
            'success': True,
            'query': {
                'location': location,
                'sku': sku,
                'filters': additional_filters,
                'natural_language': natural_language_query
            },
            'results': {
                'total_matched': results['total_matched'],
                'segment_id': results.get('segment_id'),  # Include segment ID
                'sql_query': results.get('sql_query'),  # Include SQL query
                'unsupported_dimensions': results.get('unsupported_dimensions', []),
                'suggestions': results.get('suggestions', []),
                'parsed_dimensions': results.get('parsed_dimensions', []),  # Include parsed dimensions
                'promotion': results.get('promotion'),  # Include promotion data
                'sample_messages': results.get('sample_messages', []),  # Include generated messages
                'suppressed': {
                    'count': len(results['suppressed_users']),
                    'users': results['suppressed_users'][:10]  # Limit to 10 for display
                },
                'whatsapp_routing': {
                    'count': len(results['whatsapp_routing']),
                    'users': results['whatsapp_routing'][:10]
                },
                'time_optimized': {
                    'count': len(results['time_optimized']),
                    'users': results['time_optimized'][:10]
                },
                'eligible_count': len(results['eligible_users']),
                'before_metrics': results['before_metrics'],
                'after_metrics': results['after_metrics']
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/intelligent-query', methods=['POST'])
def run_intelligent_query():
    """
    Run an intelligent campaign query that parses natural language.
    
    Expected JSON body:
    {
        "query": "Run campaign for laptop in Bangalore"
    }
    """
    data = request.get_json()
    
    if not data or not data.get('query'):
        return jsonify({'error': 'Query text is required'}), 400
    
    query_text = data.get('query')
    
    try:
        # Run intelligent query
        results = demo_engine.run_intelligent_campaign(query_text)
        
        if results.get('error'):
            return jsonify({
                'success': False,
                'error': results['error'],
                'suggestions': results.get('suggestions', [])
            }), 400
        
        # Format response for web UI
        response = {
            'success': True,
            'query': {
                'text': query_text,
                'location': results.get('location'),
                'sku': results.get('sku'),
                'category': results.get('category'),
                'customer_id': results.get('customer_id')
            },
            'results': {
                'total_matched': results['total_matched'],
                'segment_id': results.get('segment_id'),
                'sql_query': results.get('sql_query'),
                'unsupported_dimensions': results.get('unsupported_dimensions', []),
                'suggestions': results.get('suggestions', []),
                'parsed_dimensions': results.get('parsed_dimensions', []),
                'promotion': results.get('promotion'),
                'sample_messages': results.get('sample_messages', []),
                'suppressed': {
                    'count': len(results.get('suppressed_users', [])),
                    'users': results.get('suppressed_users', [])[:10]
                },
                'whatsapp_routing': {
                    'count': len(results.get('whatsapp_routing', [])),
                    'users': results.get('whatsapp_routing', [])[:10]
                },
                'time_optimized': {
                    'count': len(results.get('time_optimized', [])),
                    'users': results.get('time_optimized', [])[:10]
                },
                'eligible_count': len(results.get('eligible_users', [])),
                'before_metrics': results.get('before_metrics', {}),
                'after_metrics': results.get('after_metrics', {})
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics."""
    stats = demo_engine.seeder.get_statistics()
    return jsonify(stats)


@app.route('/api/segments', methods=['GET'])
def get_segments():
    """Get all persisted segments."""
    try:
        segments_list = []
        for criteria_hash, segment_id in demo_engine.segments.items():
            segments_list.append({
                'segment_id': segment_id,
                'criteria_hash': criteria_hash
            })
        
        return jsonify({
            'success': True,
            'segments': segments_list,
            'total': len(segments_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/save-template', methods=['POST'])
def save_template():
    """
    Save an edited message template for future use.
    
    Expected JSON body:
    {
        "customer_id": "CUST-123",
        "channel": "sms",
        "content": "Edited message content",
        "template_name": "Optional template name"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    customer_id = data.get('customer_id')
    channel = data.get('channel')
    content = data.get('content')
    template_name = data.get('template_name', f'Custom_{channel}_{customer_id}')
    
    if not all([customer_id, channel, content]):
        return jsonify({'error': 'customer_id, channel, and content are required'}), 400
    
    try:
        # Store template in memory (in production, would save to database)
        if not hasattr(demo_engine, 'custom_templates'):
            demo_engine.custom_templates = {}
        
        template_id = f"{channel}_{customer_id}_{len(demo_engine.custom_templates)}"
        demo_engine.custom_templates[template_id] = {
            'template_id': template_id,
            'template_name': template_name,
            'customer_id': customer_id,
            'channel': channel,
            'content': content,
            'created_at': str(Path(__file__).parent.parent.parent.parent / "data" / "demo" / "custom_templates.json")
        }
        
        return jsonify({
            'success': True,
            'template_id': template_id,
            'message': 'Template saved successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get all saved custom templates."""
    try:
        if not hasattr(demo_engine, 'custom_templates'):
            demo_engine.custom_templates = {}
        
        return jsonify({
            'success': True,
            'templates': list(demo_engine.custom_templates.values()),
            'total': len(demo_engine.custom_templates)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/send-campaign', methods=['POST'])
def send_campaign():
    """
    Send campaign messages via AWS End User Messaging and SES.
    Only available in production environment.
    
    Expected JSON body:
    {
        "eligible_users": [...],  // List of eligible users from campaign query
        "throughput_tps": 10,     // Transactions per second (custom throughput)
        "campaign_id": "optional"
    }
    """
    # Check if running in production
    if not IS_PRODUCTION:
        return jsonify({
            'success': False,
            'error': 'Campaign sending is only available in production environment'
        }), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    eligible_users = data.get('eligible_users', [])
    throughput_tps = data.get('throughput_tps', 10)
    campaign_id = data.get('campaign_id', f'campaign-{int(time.time())}')
    
    if not eligible_users:
        return jsonify({'error': 'No eligible users provided'}), 400
    
    if throughput_tps <= 0 or throughput_tps > 100:
        return jsonify({'error': 'Throughput must be between 1 and 100 TPS'}), 400
    
    try:
        # Group users by AI-selected channel
        users_by_channel = {
            'sms': [],
            'whatsapp': [],
            'email': []
        }
        
        for user in eligible_users:
            channel = user.get('selected_channel', 'sms').lower()
            if channel in users_by_channel:
                users_by_channel[channel].append(user)
        
        # Create rate limiters with custom TPS for each channel
        rate_limiters = {}
        for channel in ['sms', 'whatsapp', 'email']:
            config = RateLimitConfig(
                channel=Channel[channel.upper()],
                max_requests_per_second=throughput_tps,
                burst_capacity=throughput_tps * 5,  # 5x burst capacity
                region=os.getenv('AWS_REGION', 'us-east-1')
            )
            rate_limiters[channel] = RateLimiter(config)
        
        # Send messages for each channel
        results = {
            'total_sent': 0,
            'total_failed': 0,
            'by_channel': {},
            'campaign_id': campaign_id
        }
        
        # Send SMS messages
        if users_by_channel['sms']:
            sms_results = send_sms_messages(
                users_by_channel['sms'],
                rate_limiters['sms'],
                campaign_id
            )
            results['by_channel']['sms'] = sms_results
            results['total_sent'] += sms_results['sent']
            results['total_failed'] += sms_results['failed']
        
        # Send WhatsApp messages
        if users_by_channel['whatsapp']:
            whatsapp_results = send_whatsapp_messages(
                users_by_channel['whatsapp'],
                rate_limiters['whatsapp'],
                campaign_id
            )
            results['by_channel']['whatsapp'] = whatsapp_results
            results['total_sent'] += whatsapp_results['sent']
            results['total_failed'] += whatsapp_results['failed']
        
        # Send Email messages
        if users_by_channel['email']:
            email_results = send_email_messages(
                users_by_channel['email'],
                rate_limiters['email'],
                campaign_id
            )
            results['by_channel']['email'] = email_results
            results['total_sent'] += email_results['sent']
            results['total_failed'] += email_results['failed']
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        logging.error(f"❌ Error sending campaign: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def send_sms_messages(users, rate_limiter, campaign_id):
    """Send SMS messages via AWS End User Messaging."""
    sent = 0
    failed = 0
    
    for user in users:
        # Rate limiting
        can_send, retry_after = rate_limiter.acquire(1)
        if not can_send:
            time.sleep(retry_after)
            can_send, retry_after = rate_limiter.acquire(1)
        
        # Prepare message
        message_request = MessageRequest(
            channel='SMS',
            destination_phone_number=user.get('phone', ''),
            message_body=user.get('message', ''),
            campaign_id=campaign_id,
            customer_id=user.get('customer_id'),
            metadata={'user_id': user.get('customer_id')}
        )
        
        # Send message
        response = aws_messaging.send_message(message_request)
        
        if response.success:
            sent += 1
            # Track delivery
            delivery_tracker.record_sent(
                message_id=response.message_id,
                customer_id=user.get('customer_id'),
                channel='sms',
                destination=user.get('phone', ''),
                metadata={'campaign_id': campaign_id}
            )
        else:
            failed += 1
            logging.error(f"❌ Failed to send SMS to {user.get('customer_id')}: {response.error_message}")
    
    return {'sent': sent, 'failed': failed, 'total': len(users)}


def send_whatsapp_messages(users, rate_limiter, campaign_id):
    """Send WhatsApp messages via AWS End User Messaging."""
    sent = 0
    failed = 0
    
    for user in users:
        # Rate limiting
        can_send, retry_after = rate_limiter.acquire(1)
        if not can_send:
            time.sleep(retry_after)
            can_send, retry_after = rate_limiter.acquire(1)
        
        # Prepare message (WhatsApp requires template)
        message_request = MessageRequest(
            channel='WHATSAPP',
            destination_phone_number=user.get('phone', ''),
            template_name=user.get('template_name', 'default_template'),
            template_parameters=user.get('template_parameters', {}),
            campaign_id=campaign_id,
            customer_id=user.get('customer_id'),
            metadata={'user_id': user.get('customer_id')}
        )
        
        # Send message
        response = aws_messaging.send_message(message_request)
        
        if response.success:
            sent += 1
            # Track delivery
            delivery_tracker.record_sent(
                message_id=response.message_id,
                customer_id=user.get('customer_id'),
                channel='whatsapp',
                destination=user.get('phone', ''),
                metadata={'campaign_id': campaign_id}
            )
        else:
            failed += 1
            logging.error(f"❌ Failed to send WhatsApp to {user.get('customer_id')}: {response.error_message}")
    
    return {'sent': sent, 'failed': failed, 'total': len(users)}


def send_email_messages(users, rate_limiter, campaign_id):
    """Send Email messages via AWS SES."""
    sent = 0
    failed = 0
    
    for user in users:
        # Rate limiting
        can_send, retry_after = rate_limiter.acquire(1)
        if not can_send:
            time.sleep(retry_after)
            can_send, retry_after = rate_limiter.acquire(1)
        
        # Send email
        result = aws_ses.send_email(
            to_email=user.get('email', ''),
            subject=user.get('subject', 'Special Offer'),
            body_text=user.get('message', ''),
            body_html=user.get('message_html'),
            customer_id=user.get('customer_id')
        )
        
        if result['status'] == 'sent':
            sent += 1
            # Track delivery
            delivery_tracker.record_sent(
                message_id=result['message_id'],
                customer_id=user.get('customer_id'),
                channel='email',
                destination=user.get('email', ''),
                metadata={'campaign_id': campaign_id}
            )
        else:
            failed += 1
            logging.error(f"❌ Failed to send email to {user.get('customer_id')}: {result.get('error')}")
    
    return {'sent': sent, 'failed': failed, 'total': len(users)}


@app.route('/api/environment', methods=['GET'])
def get_environment():
    """Get current environment information."""
    return jsonify({
        'is_production': IS_PRODUCTION,
        'environment': 'production' if IS_PRODUCTION else 'local',
        'aws_enabled': IS_PRODUCTION
    })


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🚀 Applied-Agentic AI AWS CPaaS Demo Web UI")
    print("=" * 80)
    print("\n📍 Open your browser to: http://localhost:5000")
    print("\n💡 Try queries like:")
    print("   - Location: Bangalore, SKU: SKU-LAPTOP-001")
    print("   - Location: Mumbai, SKU: SKU-PHONE-002")
    print("\n" + "=" * 80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
