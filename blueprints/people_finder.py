#!/usr/bin/env python3
"""
People Finder Blueprint
Flask routes for the People Finder tool
"""

from flask import Blueprint, render_template, request, jsonify, session, current_app, Response, stream_with_context
import asyncio
import queue
import threading
import json as json_lib
from utils.people_finder.search_orchestrator import SearchOrchestrator, run_search_with_progress
from utils.people_finder.public_records import PublicRecordsSearcher
from utils.people_finder.phone_apis import PhoneValidator
import os
from datetime import datetime
import time

people_finder_bp = Blueprint('people_finder', __name__)

# Orchestrator will be initialized lazily using Flask config
_orchestrator = None


def get_orchestrator():
    """Get or create the search orchestrator using Flask config"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SearchOrchestrator(
            cache_db_path=current_app.config['PEOPLE_FINDER_DB']
        )
        # Initialize web scraper with API keys from config
        if current_app.config.get('GOOGLE_API_KEY'):
            _orchestrator.web_scraper.google_api_key = current_app.config['GOOGLE_API_KEY']
            _orchestrator.web_scraper.search_engine_id = current_app.config.get('GOOGLE_SEARCH_ENGINE_ID')
        # Initialize phone validator with API key from config
        if current_app.config.get('NUMVERIFY_API_KEY'):
            _orchestrator.phone_validator.numverify_key = current_app.config['NUMVERIFY_API_KEY']
    return _orchestrator


@people_finder_bp.route('/')
def index():
    """Render the main People Finder interface"""
    return render_template('people_finder.html')


@people_finder_bp.route('/api/search', methods=['POST'])
def search():
    """
    Main search endpoint.
    Accepts form data and returns organized results.
    """
    
    # Get search parameters
    data = request.get_json() or request.form

    name = data.get('name', '').strip() or None
    phone = data.get('phone', '').strip() or None
    address = data.get('address', '').strip() or None
    email = data.get('email', '').strip() or None
    state = data.get('state', '').strip() or None
    county = data.get('county', '').strip() or None

    # Get optional API keys from request (sent from frontend localStorage)
    google_api_key = data.get('google_api_key', '').strip() or None
    google_search_engine_id = data.get('google_search_engine_id', '').strip() or None
    numverify_api_key = data.get('numverify_api_key', '').strip() or None

    # Validate that at least one parameter is provided
    if not any([name, phone, address, email]):
        return jsonify({
            "error": "Please provide at least one search parameter"
        }), 400

    try:
        # Run async search in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        orchestrator = get_orchestrator()

        # Temporarily override API keys if provided in request
        # This allows per-request API key configuration from frontend
        if google_api_key:
            orchestrator.web_scraper.google_api_key = google_api_key
        if google_search_engine_id:
            orchestrator.web_scraper.search_engine_id = google_search_engine_id
        if numverify_api_key:
            orchestrator.phone_validator.numverify_key = numverify_api_key

        results = loop.run_until_complete(
            orchestrator.search_person(
                name=name,
                phone=phone,
                address=address,
                email=email,
                state=state,
                county=county
            )
        )

        loop.close()

        return jsonify(results)
    
    except Exception as e:
        return jsonify({
            "error": f"Search failed: {str(e)}"
        }), 500


@people_finder_bp.route('/api/search/stream', methods=['POST'])
def search_stream():
    """
    Search endpoint with real-time progress updates via Server-Sent Events.
    Returns a stream of progress updates followed by final results.

    SSE Format:
    data: {"type": "progress", "message": "Starting search...", "percent": 0}
    data: {"type": "progress", "message": "Searching...", "percent": 50}
    data: {"type": "result", "data": {...}}
    """

    # Get search parameters
    data = request.get_json() or request.form

    name = data.get('name', '').strip() or None
    phone = data.get('phone', '').strip() or None
    address = data.get('address', '').strip() or None
    email = data.get('email', '').strip() or None
    state = data.get('state', '').strip() or None
    county = data.get('county', '').strip() or None

    # Get optional API keys from request
    google_api_key = data.get('google_api_key', '').strip() or None
    google_search_engine_id = data.get('google_search_engine_id', '').strip() or None
    numverify_api_key = data.get('numverify_api_key', '').strip() or None

    # Validate
    if not any([name, phone, address, email]):
        return jsonify({"error": "Please provide at least one search parameter"}), 400

    def generate_progress():
        """Generator function that yields SSE-formatted progress updates"""

        # Create a queue for progress updates
        progress_queue = queue.Queue()
        result_container = {}
        error_container = {}

        def progress_callback(message: str, percent: int):
            """Callback to send progress updates"""
            progress_queue.put({
                "type": "progress",
                "message": message,
                "percent": percent,
                "timestamp": time.time()
            })

        def run_search():
            """Run the search in a separate thread"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                orchestrator = get_orchestrator()

                # Override API keys if provided
                if google_api_key:
                    orchestrator.web_scraper.google_api_key = google_api_key
                if google_search_engine_id:
                    orchestrator.web_scraper.search_engine_id = google_search_engine_id
                if numverify_api_key:
                    orchestrator.phone_validator.numverify_key = numverify_api_key

                # Run search with progress callback
                results = loop.run_until_complete(
                    orchestrator.search_person(
                        name=name,
                        phone=phone,
                        address=address,
                        email=email,
                        state=state,
                        county=county,
                        progress_callback=progress_callback
                    )
                )

                loop.close()

                # Store results
                result_container['data'] = results

                # Send final result message
                progress_queue.put({
                    "type": "result",
                    "data": results
                })

            except Exception as e:
                error_container['error'] = str(e)
                progress_queue.put({
                    "type": "error",
                    "message": str(e)
                })

        # Start search in background thread
        search_thread = threading.Thread(target=run_search)
        search_thread.daemon = True
        search_thread.start()

        # Stream progress updates
        while True:
            try:
                # Wait for progress update (timeout after 60 seconds)
                update = progress_queue.get(timeout=60)

                # Format as SSE
                yield f"data: {json_lib.dumps(update)}\n\n"

                # If this is the final result or error, stop streaming
                if update['type'] in ['result', 'error']:
                    break

            except queue.Empty:
                # Timeout - send keepalive
                yield f"data: {json_lib.dumps({'type': 'keepalive'})}\n\n"

                # Check if thread is still alive
                if not search_thread.is_alive():
                    break

        # Wait for thread to finish
        search_thread.join(timeout=5)

    # Return SSE response
    return Response(
        stream_with_context(generate_progress()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
            'Connection': 'keep-alive'
        }
    )


@people_finder_bp.route('/api/search/trail-follow', methods=['POST'])
def search_trail_follow():
    """
    Advanced "follow the trail" search endpoint.
    Searches initial person, then their associates, then associates' associates.
    Builds comprehensive relationship network like professional skip tracing tools.

    Request body:
    {
        "name": "John Smith",
        "phone": "5551234567",  # optional
        "address": "123 Main St",  # optional
        "email": "email@example.com",  # optional
        "state": "OH",  # optional
        "county": "Franklin",  # optional
        "max_depth": 2,  # 1-3 (how many degrees of separation)
        "max_associates": 10  # limit associates per level
    }
    """

    # Import trail follower
    try:
        from utils.people_finder.trail_follower import TrailFollower
    except ImportError:
        return jsonify({"error": "Trail following feature not available"}), 500

    # Get search parameters
    data = request.get_json() or request.form

    name = data.get('name', '').strip() or None
    phone = data.get('phone', '').strip() or None
    address = data.get('address', '').strip() or None
    email = data.get('email', '').strip() or None
    state = data.get('state', '').strip() or None
    county = data.get('county', '').strip() or None
    max_depth = int(data.get('max_depth', 2))  # Default 2 degrees
    max_associates = int(data.get('max_associates', 10))  # Default 10 per level

    # Get optional API keys
    google_api_key = data.get('google_api_key', '').strip() or None
    google_search_engine_id = data.get('google_search_engine_id', '').strip() or None
    numverify_api_key = data.get('numverify_api_key', '').strip() or None

    # Validate
    if not name:
        return jsonify({"error": "Name is required for trail following"}), 400

    # Limit depth
    if max_depth < 1 or max_depth > 3:
        return jsonify({"error": "max_depth must be between 1 and 3"}), 400

    try:
        # Run async trail following
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        orchestrator = get_orchestrator()

        # Override API keys if provided
        if google_api_key:
            orchestrator.web_scraper.google_api_key = google_api_key
        if google_search_engine_id:
            orchestrator.web_scraper.search_engine_id = google_search_engine_id
        if numverify_api_key:
            orchestrator.phone_validator.numverify_key = numverify_api_key

        # Create trail follower
        trail_follower = TrailFollower(orchestrator)

        # Follow the trail!
        results = loop.run_until_complete(
            trail_follower.follow_trail(
                initial_name=name,
                initial_phone=phone,
                initial_address=address,
                initial_email=email,
                state=state,
                county=county,
                max_depth=max_depth,
                max_associates=max_associates,
                progress_callback=None  # Could add SSE support here too
            )
        )

        loop.close()

        return jsonify(results)

    except Exception as e:
        return jsonify({
            "error": f"Trail following failed: {str(e)}"
        }), 500


@people_finder_bp.route('/api/validate-phone', methods=['POST'])
def validate_phone():
    """
    Quick phone validation endpoint.
    Returns carrier, line type, and location info.
    """
    
    data = request.get_json() or request.form
    phone = data.get('phone', '').strip()

    # Get optional NumVerify API key from request (or fallback to config)
    numverify_key = data.get('numverify_api_key', '').strip() or current_app.config.get('NUMVERIFY_API_KEY')

    if not phone:
        return jsonify({"error": "Phone number required"}), 400

    try:
        validator = PhoneValidator(numverify_key=numverify_key)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            validator.validate_and_lookup(phone)
        )

        loop.close()

        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "error": f"Validation failed: {str(e)}"
        }), 500


@people_finder_bp.route('/api/autofill-form', methods=['POST'])
def get_autofill_form():
    """
    Get pre-filled form data for manual court/record searches.
    Returns form fields that can be used to auto-fill web forms.
    """
    
    data = request.get_json() or request.form
    
    state = data.get('state', '').upper()
    record_type = data.get('record_type', 'courts')  # courts, property, etc.
    
    search_params = {
        "name": data.get('name'),
        "phone": data.get('phone'),
        "address": data.get('address'),
        "email": data.get('email')
    }
    
    try:
        public_records = PublicRecordsSearcher()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        form_data = loop.run_until_complete(
            public_records.get_auto_fill_form_data(state, record_type, search_params)
        )
        
        loop.close()
        
        return jsonify(form_data)
    
    except Exception as e:
        return jsonify({
            "error": f"Failed to generate form data: {str(e)}"
        }), 500


@people_finder_bp.route('/api/export/<format>', methods=['POST'])
def export_results(format):
    """
    Export search results to various formats (PDF, CSV, JSON).

    Args:
        format: Export format (pdf, csv, json)
    """

    data = request.get_json()
    results = data.get('results', {})

    if format == 'json':
        return jsonify(results)

    elif format == 'csv':
        return _export_csv(results)

    elif format == 'pdf':
        return _export_pdf(results)

    else:
        return jsonify({"error": "Invalid export format"}), 400


def _export_csv(results):
    """Generate CSV file from search results"""
    import csv
    import io
    from flask import Response

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'Name', 'Confidence %', 'Phone Numbers', 'Addresses',
        'Emails', 'Public Records', 'Social Media', 'Sources'
    ])

    # Write each person
    for person in results.get('persons', []):
        phones = '; '.join([p['formatted'] for p in person.get('organized_data', {}).get('phone_numbers', [])])
        addresses = '; '.join([a['full_address'] for a in person.get('organized_data', {}).get('addresses', [])])
        emails = '; '.join([e['email'] for e in person.get('organized_data', {}).get('emails', [])])
        records_count = len(person.get('organized_data', {}).get('public_records', []))
        social_count = len(person.get('organized_data', {}).get('social_media', []))
        sources = ', '.join(person.get('confidence_sources', []))

        writer.writerow([
            person.get('name', 'Unknown'),
            round(person.get('overall_confidence', 0)),
            phones or 'None',
            addresses or 'None',
            emails or 'None',
            records_count,
            social_count,
            sources
        ])

    # Create response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=people_finder_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )


def _export_pdf(results):
    """Generate PDF report from search results"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    import io
    from flask import Response

    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3c72'),
        spaceAfter=30
    )
    story.append(Paragraph("People Finder - Search Results", title_style))
    story.append(Spacer(1, 0.2 * inch))

    # Search metadata
    search_params = results.get('search_params', {})
    search_time = results.get('search_timestamp', '')

    meta_text = f"<b>Search Date:</b> {search_time}<br/>"
    meta_text += f"<b>Total Results:</b> {results.get('total_persons_found', 0)}<br/>"
    if search_params.get('name'):
        meta_text += f"<b>Search Name:</b> {search_params['name']}<br/>"
    if search_params.get('phone'):
        meta_text += f"<b>Search Phone:</b> {search_params['phone']}<br/>"
    if search_params.get('state'):
        meta_text += f"<b>Search State:</b> {search_params['state']}<br/>"

    story.append(Paragraph(meta_text, styles['BodyText']))
    story.append(Spacer(1, 0.3 * inch))

    # Person cards
    for i, person in enumerate(results.get('persons', []), 1):
        # Person header
        confidence = round(person.get('overall_confidence', 0))
        confidence_color = colors.green if confidence >= 70 else colors.orange if confidence >= 40 else colors.red

        header_text = f"<font size=14><b>{i}. {person.get('name', 'Unknown')}</b></font> "
        header_text += f"<font color={confidence_color.hexval()}><b>({confidence}% Match)</b></font>"
        story.append(Paragraph(header_text, styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))

        # Person details
        org_data = person.get('organized_data', {})

        # Phone numbers
        phones = org_data.get('phone_numbers', [])
        if phones:
            story.append(Paragraph("<b>Phone Numbers:</b>", styles['Heading3']))
            for phone in phones:
                story.append(Paragraph(f"• {phone['formatted']} ({phone['source']})", styles['BodyText']))

        # Addresses
        addresses = org_data.get('addresses', [])
        if addresses:
            story.append(Paragraph("<b>Addresses:</b>", styles['Heading3']))
            for addr in addresses:
                story.append(Paragraph(f"• {addr['full_address']}", styles['BodyText']))

        # Emails
        emails = org_data.get('emails', [])
        if emails:
            story.append(Paragraph("<b>Emails:</b>", styles['Heading3']))
            for email in emails:
                story.append(Paragraph(f"• {email['email']}", styles['BodyText']))

        # Public records
        records = org_data.get('public_records', [])
        if records:
            story.append(Paragraph(f"<b>Public Records:</b> {len(records)} found", styles['Heading3']))

        # Social media
        social = org_data.get('social_media', [])
        if social:
            story.append(Paragraph("<b>Social Media:</b>", styles['Heading3']))
            for link in social[:3]:  # Limit to first 3
                platform = link.get('platform', 'Unknown')
                url = link.get('url', '')
                story.append(Paragraph(f"• {platform}: {url}", styles['BodyText']))

        # Sources
        sources = ', '.join(person.get('confidence_sources', []))
        story.append(Paragraph(f"<b>Data Sources:</b> {sources}", styles['BodyText']))

        story.append(Spacer(1, 0.3 * inch))

    # Footer
    footer_text = f"<i>Report generated by ZoolZ People Finder on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    story.append(Paragraph(footer_text, styles['Italic']))

    # Build PDF
    doc.build(story)

    # Return as download
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=people_finder_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        }
    )


@people_finder_bp.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear search cache"""
    
    try:
        orchestrator = get_orchestrator()
        orchestrator.organizer.clear_old_cache(days=0)  # Clear all
        return jsonify({"success": True, "message": "Cache cleared"})
    
    except Exception as e:
        return jsonify({
            "error": f"Failed to clear cache: {str(e)}"
        }), 500


@people_finder_bp.route('/api/stats')
def get_stats():
    """Get usage statistics"""

    orchestrator = get_orchestrator()

    # Query database for real stats
    try:
        import sqlite3
        conn = sqlite3.connect(current_app.config['PEOPLE_FINDER_DB'])
        cursor = conn.cursor()

        # Count total searches from history
        cursor.execute('SELECT COUNT(*) FROM search_history')
        total_searches = cursor.fetchone()[0]

        # Count cached results (non-expired)
        cursor.execute("SELECT COUNT(*) FROM search_cache WHERE expires_at > datetime('now')")
        cached_results = cursor.fetchone()[0]

        conn.close()
    except Exception as e:
        # Fallback to 0 if database query fails
        total_searches = 0
        cached_results = 0

    stats = {
        "total_searches": total_searches,
        "cached_results": cached_results,
        "daily_api_queries": orchestrator.web_scraper.daily_query_count if hasattr(orchestrator, 'web_scraper') else 0,
        "api_limit": 100  # Free tier limit
    }

    return jsonify(stats)


# Configuration route (for setting API keys, etc.)
@people_finder_bp.route('/api/config', methods=['GET', 'POST'])
def config():
    """
    Get or update configuration (API keys, preferences).
    Should be secured in production!
    """
    
    if request.method == 'GET':
        # Return current config (without revealing keys)
        config_data = {
            "has_google_api_key": bool(current_app.config.get('GOOGLE_API_KEY')),
            "has_numverify_key": bool(current_app.config.get('NUMVERIFY_API_KEY')),
            "rate_limit_delay": 2,
            "cache_duration_hours": current_app.config.get('PEOPLE_FINDER_CACHE_HOURS', 24)
        }
        return jsonify(config_data)
    
    elif request.method == 'POST':
        # Update config
        # In production, this should be secured!
        data = request.get_json()
        
        # Save to environment or config file
        # For now, just return success
        return jsonify({"success": True, "message": "Configuration updated"})


# Error handlers
@people_finder_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@people_finder_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500
