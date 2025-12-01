#!/usr/bin/env python3
"""
Digital Footprint Finder - Flask Blueprint

API endpoints for digital footprint discovery and reputation management.
"""

from flask import Blueprint, request, jsonify, render_template, Response, stream_with_context
import asyncio
import sys
import os
import queue
import threading
import json as json_lib
import time

from .utils.footprint_finder import DigitalFootprintFinder
from .utils.exposure_analyzer import ExposureAnalyzer

digital_footprint_bp = Blueprint(
    'digital_footprint',
    __name__,
    url_prefix='/footprint',
    template_folder='templates',
    static_folder='static',
    static_url_path='/footprint/static'
)


@digital_footprint_bp.route('/')
def index():
    """
    Main digital footprint finder page.
    """
    return render_template('digital_footprint.html')


@digital_footprint_bp.route('/api/search', methods=['POST'])
def search_footprint():
    """
    Standard digital footprint search (non-streaming).

    Request JSON:
    {
        "username": "optional_username",
        "email": "optional@email.com",
        "phone": "555-123-4567",
        "full_name": "John Doe",
        "additional_identifiers": ["nickname", "handle"]
    }

    Response JSON:
    {
        "findings": {...},
        "exposure_analysis": {...},
        "summary": {...},
        "recommendations": [...]
    }
    """

    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    phone = data.get('phone')
    full_name = data.get('full_name')
    additional_identifiers = data.get('additional_identifiers', [])

    # Validate: at least one identifier required
    if not any([username, email, phone, full_name]):
        return jsonify({
            "error": "At least one identifier (username, email, phone, or full_name) is required"
        }), 400

    try:
        # Run async search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        finder = DigitalFootprintFinder()

        results = loop.run_until_complete(
            finder.search_footprint(
                username=username,
                email=email,
                phone=phone,
                full_name=full_name,
                additional_identifiers=additional_identifiers,
                progress_callback=None
            )
        )

        loop.close()

        # Analyze findings
        analyzer = ExposureAnalyzer()
        analysis = analyzer.analyze_findings(results.get("findings", {}))

        # Combine results
        response = {
            "findings": results.get("findings", {}),
            "exposure_analysis": analysis,
            "summary": results.get("summary", {}),
            "recommendations": results.get("recommendations", []),
            "timestamp": results.get("timestamp", "")
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            "error": f"Search failed: {str(e)}"
        }), 500


@digital_footprint_bp.route('/api/search/stream', methods=['POST'])
def search_footprint_stream():
    """
    Real-time streaming digital footprint search with progress updates.

    Uses Server-Sent Events (SSE) to stream progress.

    Request JSON:
    {
        "username": "optional_username",
        "email": "optional@email.com",
        "phone": "555-123-4567",
        "full_name": "John Doe",
        "additional_identifiers": ["nickname", "handle"]
    }

    SSE Response Format:
    data: {"type": "progress", "message": "Searching...", "percent": 50}
    data: {"type": "result", "data": {...}}
    """

    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    phone = data.get('phone')
    full_name = data.get('full_name')
    additional_identifiers = data.get('additional_identifiers', [])

    # Validate
    if not any([username, email, phone, full_name]):
        return jsonify({
            "error": "At least one identifier is required"
        }), 400

    def generate_progress():
        """Generate SSE stream with progress updates"""

        progress_queue = queue.Queue()

        def progress_callback(message: str, percent: int):
            """Callback to send progress updates"""
            progress_queue.put({
                "type": "progress",
                "message": message,
                "percent": percent,
                "timestamp": time.time()
            })

        def run_search():
            """Run search in background thread"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                finder = DigitalFootprintFinder()

                results = loop.run_until_complete(
                    finder.search_footprint(
                        username=username,
                        email=email,
                        phone=phone,
                        full_name=full_name,
                        additional_identifiers=additional_identifiers,
                        progress_callback=progress_callback
                    )
                )

                loop.close()

                # Analyze findings
                analyzer = ExposureAnalyzer()
                analysis = analyzer.analyze_findings(results.get("findings", {}))

                # Send final result
                progress_queue.put({
                    "type": "result",
                    "data": {
                        "findings": results.get("findings", {}),
                        "exposure_analysis": analysis,
                        "summary": results.get("summary", {}),
                        "recommendations": results.get("recommendations", [])
                    }
                })

            except Exception as e:
                progress_queue.put({
                    "type": "error",
                    "error": str(e)
                })

        # Start search in background thread
        search_thread = threading.Thread(target=run_search)
        search_thread.daemon = True
        search_thread.start()

        # Stream progress updates
        while True:
            try:
                update = progress_queue.get(timeout=60)
                yield f"data: {json_lib.dumps(update)}\n\n"

                # Stop streaming after result or error
                if update['type'] in ['result', 'error']:
                    break

            except queue.Empty:
                # Timeout - send keepalive
                yield f"data: {json_lib.dumps({'type': 'keepalive'})}\n\n"

    return Response(
        stream_with_context(generate_progress()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@digital_footprint_bp.route('/api/analyze', methods=['POST'])
def analyze_exposure():
    """
    Analyze existing findings to generate recommendations.

    Request JSON:
    {
        "findings": {...}  # Findings from previous search
    }

    Response JSON:
    {
        "risk_score": 75,
        "risk_level": "HIGH",
        "prioritized_actions": [...],
        "cleanup_estimate": {...}
    }
    """

    data = request.get_json()
    findings = data.get('findings', {})

    if not findings:
        return jsonify({
            "error": "Findings data is required"
        }), 400

    try:
        analyzer = ExposureAnalyzer()
        analysis = analyzer.analyze_findings(findings)

        return jsonify(analysis)

    except Exception as e:
        return jsonify({
            "error": f"Analysis failed: {str(e)}"
        }), 500


@digital_footprint_bp.route('/api/removal-request', methods=['POST'])
def generate_removal_request():
    """
    Generate email template for removal request.

    Request JSON:
    {
        "finding": {
            "type": "public_mention",
            "email": "test@example.com",
            "url": "https://example.com/page",
            ...
        }
    }

    Response JSON:
    {
        "template": "Email template text..."
    }
    """

    data = request.get_json()
    finding = data.get('finding', {})

    if not finding:
        return jsonify({
            "error": "Finding data is required"
        }), 400

    try:
        analyzer = ExposureAnalyzer()
        template = analyzer.generate_removal_request(finding)

        return jsonify({
            "template": template,
            "finding": finding
        })

    except Exception as e:
        return jsonify({
            "error": f"Template generation failed: {str(e)}"
        }), 500


@digital_footprint_bp.route('/api/report', methods=['POST'])
def generate_cleanup_report():
    """
    Generate comprehensive cleanup report (PDF-ready text).

    Request JSON:
    {
        "findings": {...},
        "analysis": {...}
    }

    Response JSON:
    {
        "report": "Full report text...",
        "format": "text"
    }
    """

    data = request.get_json()
    findings = data.get('findings', {})
    analysis = data.get('analysis', {})

    if not findings or not analysis:
        return jsonify({
            "error": "Both findings and analysis data are required"
        }), 400

    try:
        analyzer = ExposureAnalyzer()
        report = analyzer.generate_cleanup_report(findings, analysis)

        return jsonify({
            "report": report,
            "format": "text",
            "timestamp": time.time()
        })

    except Exception as e:
        return jsonify({
            "error": f"Report generation failed: {str(e)}"
        }), 500


@digital_footprint_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    """
    return jsonify({
        "status": "healthy",
        "service": "digital_footprint_finder",
        "version": "1.0.0"
    })


# Error handlers
@digital_footprint_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found"
    }), 404


@digital_footprint_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error"
    }), 500
