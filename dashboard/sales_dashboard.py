"""
Entelech Sales Process Automation Dashboard
Interactive web interface for managing the end-to-end sales workflow
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import sqlite3
from datetime import datetime, timedelta, date
import sys
import os
from typing import Dict, List, Any

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from sales_automation_engine import SalesProcessAutomationEngine, DiscoveryCallData, QualificationStatus

app = Flask(__name__)
app.config['SECRET_KEY'] = 'entelech-sales-automation-2025'

# Initialize sales automation engine
sales_engine = SalesProcessAutomationEngine("../database/sales_automation.db")

# ================================
# MAIN DASHBOARD ROUTES
# ================================

@app.route('/')
def dashboard():
    """Main sales process dashboard"""
    return render_template('sales_dashboard.html')

@app.route('/discovery')
def discovery_calls():
    """Discovery calls management page"""
    return render_template('discovery_calls.html')

@app.route('/sows')
def sow_management():
    """SOW management page"""
    return render_template('sow_management.html')

@app.route('/contracts')
def contract_management():
    """Contract management page"""
    return render_template('contract_management.html')

@app.route('/projects')
def project_kickoffs():
    """Project kickoff management page"""
    return render_template('project_kickoffs.html')

# ================================
# API ENDPOINTS
# ================================

@app.route('/api/dashboard/overview')
def api_dashboard_overview():
    """Get dashboard overview metrics"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Get custom date range if provided
        if request.args.get('start_date'):
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        if request.args.get('end_date'):
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        
        # Get sales process analytics
        analytics = sales_engine.get_sales_process_analytics((start_date, end_date))
        
        # Get recent activity
        recent_activity = get_recent_sales_activity()
        
        # Get pending items requiring attention
        pending_items = get_pending_items()
        
        overview_data = {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "key_metrics": {
                "total_discovery_calls": analytics.get("discovery_calls", {}).get("total_calls", 0),
                "qualified_leads": analytics.get("discovery_calls", {}).get("qualified_count", 0),
                "sows_generated": analytics.get("sow_generation", {}).get("total_sows", 0),
                "contracts_executed": analytics.get("contract_execution", {}).get("executed_count", 0),
                "total_pipeline_value": f"${analytics.get('sow_generation', {}).get('total_pipeline_value', 0):,.2f}",
                "closed_revenue": f"${analytics.get('contract_execution', {}).get('closed_revenue', 0):,.2f}",
                "avg_deal_size": f"${analytics.get('sow_generation', {}).get('avg_project_value', 0):,.2f}"
            },
            "conversion_rates": analytics.get("conversion_rates", {}),
            "automation_efficiency": analytics.get("automation_efficiency", {}),
            "recent_activity": recent_activity,
            "pending_items": pending_items
        }
        
        return jsonify(overview_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/discovery/submit', methods=['POST'])
def api_submit_discovery_call():
    """Submit new discovery call data"""
    try:
        data = request.json
        
        # Create DiscoveryCallData object
        call_data = DiscoveryCallData(
            company_name=data['company_name'],
            company_size=data['company_size'],
            industry=data['industry'],
            annual_revenue=data.get('annual_revenue', 'not_disclosed'),
            primary_contact_name=data['primary_contact_name'],
            primary_contact_email=data['primary_contact_email'],
            primary_contact_title=data['primary_contact_title'],
            decision_maker_name=data.get('decision_maker_name'),
            decision_maker_title=data.get('decision_maker_title'),
            current_challenges=data['current_challenges'],
            manual_processes=data['manual_processes'],
            time_waste_hours_weekly=int(data.get('time_waste_hours_weekly', 0)),
            estimated_cost_inefficiency=float(data.get('estimated_cost_inefficiency', 0)),
            current_tools_systems=data.get('current_tools_systems', ''),
            team_size_affected=int(data.get('team_size_affected', 0)),
            primary_objectives=data['primary_objectives'],
            success_metrics=data.get('success_metrics', ''),
            automation_priorities=data.get('automation_priorities', ''),
            integration_requirements=data.get('integration_requirements', ''),
            compliance_requirements=data.get('compliance_requirements', ''),
            security_requirements=data.get('security_requirements', ''),
            budget_range=data.get('budget_range', 'not_disclosed'),
            timeline_urgency=data.get('timeline_urgency', '3_months'),
            decision_timeline=data.get('decision_timeline', '1_month'),
            roi_expectations=data.get('roi_expectations', ''),
            sales_rep=data.get('sales_rep', 'Unknown'),
            call_duration_minutes=int(data.get('call_duration_minutes', 60)),
            next_steps=data.get('next_steps', ''),
            call_notes=data.get('call_notes', '')
        )
        
        # Process discovery call
        call_id = sales_engine.process_discovery_call(
            prospect_id=data.get('prospect_id', 1),  # TODO: Get from prospect system
            call_data=call_data
        )
        
        return jsonify({
            "success": True,
            "call_id": call_id,
            "message": "Discovery call processed successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/discovery/calls')
def api_get_discovery_calls():
    """Get discovery calls with filtering and pagination"""
    try:
        # Query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status_filter = request.args.get('status')
        
        conn = sqlite3.connect("../database/sales_automation.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query with filters
        query = """
            SELECT call_id, company_name, primary_contact_name, industry, company_size,
                   overall_qualification_score, qualified_status, call_date, sales_rep,
                   budget_range, timeline_urgency, time_waste_hours_weekly,
                   estimated_cost_inefficiency
            FROM discovery_calls 
            WHERE 1=1
        """
        params = []
        
        if status_filter:
            query += " AND qualified_status = ?"
            params.append(status_filter)
        
        query += " ORDER BY call_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])
        
        cursor.execute(query, params)
        calls = cursor.fetchall()
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) as total FROM discovery_calls WHERE 1=1"
        count_params = []
        if status_filter:
            count_query += " AND qualified_status = ?"
            count_params.append(status_filter)
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['total']
        
        conn.close()
        
        return jsonify({
            "calls": [dict(call) for call in calls],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sows/list')
def api_get_sows():
    """Get generated SOWs with status and details"""
    try:
        conn = sqlite3.connect("../database/sales_automation.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.sow_id, s.project_title, s.total_project_cost, s.timeline_weeks,
                   s.sow_status, s.generated_at, s.sent_at, s.approved_at,
                   d.company_name, d.primary_contact_name
            FROM generated_sows s
            JOIN discovery_calls d ON s.discovery_call_id = d.call_id
            ORDER BY s.generated_at DESC
            LIMIT 50
        """)
        
        sows = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "sows": [dict(sow) for sow in sows]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sows/<int:sow_id>/approve', methods=['POST'])
def api_approve_sow(sow_id):
    """Approve SOW and trigger contract generation"""
    try:
        conn = sqlite3.connect("../database/sales_automation.db")
        cursor = conn.cursor()
        
        # Update SOW status
        cursor.execute("""
            UPDATE generated_sows 
            SET sow_status = 'approved', approved_at = CURRENT_TIMESTAMP
            WHERE sow_id = ?
        """, (sow_id,))
        
        conn.commit()
        
        # Trigger contract generation
        contract_id = sales_engine.generate_contract_from_sow(sow_id)
        
        conn.close()
        
        return jsonify({
            "success": True,
            "contract_id": contract_id,
            "message": "SOW approved and contract generated"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/contracts/list')
def api_get_contracts():
    """Get contracts with status and details"""
    try:
        conn = sqlite3.connect("../database/sales_automation.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.contract_id, c.contract_number, c.contract_title, 
                   c.total_contract_value, c.contract_status, c.created_at,
                   c.sent_for_signature_at, c.fully_executed_at,
                   c.client_legal_name, c.client_signatory_name
            FROM generated_contracts c
            ORDER BY c.created_at DESC
            LIMIT 50
        """)
        
        contracts = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "contracts": [dict(contract) for contract in contracts]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contracts/<int:contract_id>/send', methods=['POST'])
def api_send_contract(contract_id):
    """Send contract for e-signature"""
    try:
        conn = sqlite3.connect("../database/sales_automation.db")
        cursor = conn.cursor()
        
        # Update contract status
        cursor.execute("""
            UPDATE generated_contracts 
            SET contract_status = 'sent_for_signature', sent_for_signature_at = CURRENT_TIMESTAMP
            WHERE contract_id = ?
        """, (contract_id,))
        
        conn.commit()
        conn.close()
        
        # TODO: Integrate with DocuSign/HelloSign API
        
        return jsonify({
            "success": True,
            "message": "Contract sent for signature"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/contracts/<int:contract_id>/execute', methods=['POST'])
def api_execute_contract(contract_id):
    """Mark contract as fully executed and trigger payment setup"""
    try:
        conn = sqlite3.connect("../database/sales_automation.db")
        cursor = conn.cursor()
        
        # Update contract status
        cursor.execute("""
            UPDATE generated_contracts 
            SET contract_status = 'fully_executed', fully_executed_at = CURRENT_TIMESTAMP
            WHERE contract_id = ?
        """, (contract_id,))
        
        conn.commit()
        conn.close()
        
        # Setup payment processing
        config_id = sales_engine.setup_payment_processing(contract_id)
        
        # Trigger project kickoff
        kickoff_id = sales_engine.trigger_project_kickoff(contract_id)
        
        return jsonify({
            "success": True,
            "payment_config_id": config_id,
            "kickoff_id": kickoff_id,
            "message": "Contract executed, payment setup, and project kickoff initiated"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/projects/list')
def api_get_projects():
    """Get project kickoffs with status"""
    try:
        conn = sqlite3.connect("../database/sales_automation.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pk.kickoff_id, pk.project_code, pk.project_name, 
                   pk.project_manager, pk.kickoff_status, pk.created_at,
                   pk.kickoff_scheduled_date, pk.kickoff_completed_date,
                   c.total_contract_value, c.client_legal_name
            FROM project_kickoffs pk
            JOIN generated_contracts c ON pk.contract_id = c.contract_id
            ORDER BY pk.created_at DESC
            LIMIT 50
        """)
        
        projects = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "projects": [dict(project) for project in projects]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/workflow/status')
def api_get_workflow_status():
    """Get workflow automation status and logs"""
    try:
        process_type = request.args.get('process_type')
        status = request.args.get('status')
        
        workflow_logs = sales_engine.get_workflow_status(process_type, status)
        
        return jsonify({
            "workflow_logs": workflow_logs
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================
# HELPER FUNCTIONS
# ================================

def get_recent_sales_activity():
    """Get recent sales activity for dashboard"""
    try:
        conn = sqlite3.connect("../database/sales_automation.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        activities = []
        
        # Recent discovery calls
        cursor.execute("""
            SELECT 'discovery_call' as type, company_name as description, call_date as timestamp
            FROM discovery_calls 
            WHERE call_date >= datetime('now', '-7 days')
            ORDER BY call_date DESC
            LIMIT 5
        """)
        activities.extend(cursor.fetchall())
        
        # Recent SOW generations
        cursor.execute("""
            SELECT 'sow_generated' as type, 
                   'SOW generated for ' || d.company_name as description,
                   s.generated_at as timestamp
            FROM generated_sows s
            JOIN discovery_calls d ON s.discovery_call_id = d.call_id
            WHERE s.generated_at >= datetime('now', '-7 days')
            ORDER BY s.generated_at DESC
            LIMIT 5
        """)
        activities.extend(cursor.fetchall())
        
        # Recent contract executions
        cursor.execute("""
            SELECT 'contract_executed' as type,
                   'Contract executed for ' || client_legal_name as description,
                   fully_executed_at as timestamp
            FROM generated_contracts
            WHERE fully_executed_at >= datetime('now', '-7 days')
            ORDER BY fully_executed_at DESC
            LIMIT 5
        """)
        activities.extend(cursor.fetchall())
        
        conn.close()
        
        # Sort all activities by timestamp
        activities = sorted(activities, key=lambda x: x['timestamp'], reverse=True)
        
        return [dict(activity) for activity in activities[:10]]
        
    except Exception as e:
        return []

def get_pending_items():
    """Get items requiring attention"""
    try:
        conn = sqlite3.connect("../database/sales_automation.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        pending = {
            "sows_pending_review": 0,
            "contracts_pending_signature": 0,
            "projects_pending_kickoff": 0,
            "overdue_payments": 0
        }
        
        # SOWs pending review
        cursor.execute("SELECT COUNT(*) as count FROM generated_sows WHERE sow_status = 'review'")
        pending["sows_pending_review"] = cursor.fetchone()['count']
        
        # Contracts pending signature
        cursor.execute("SELECT COUNT(*) as count FROM generated_contracts WHERE contract_status = 'sent_for_signature'")
        pending["contracts_pending_signature"] = cursor.fetchone()['count']
        
        # Projects pending kickoff
        cursor.execute("SELECT COUNT(*) as count FROM project_kickoffs WHERE kickoff_status = 'pending'")
        pending["projects_pending_kickoff"] = cursor.fetchone()['count']
        
        # Overdue payments
        cursor.execute("""
            SELECT COUNT(*) as count FROM payment_transactions 
            WHERE transaction_status = 'pending' AND invoice_due_date < date('now')
        """)
        pending["overdue_payments"] = cursor.fetchone()['count']
        
        conn.close()
        return pending
        
    except Exception as e:
        return {}

# ================================
# ERROR HANDLERS
# ================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ================================
# MAIN APPLICATION
# ================================

if __name__ == '__main__':
    # Ensure database exists
    if not os.path.exists("../database/sales_automation.db"):
        print("Warning: Database not found. Please run database initialization first.")
    
    print("Starting Entelech Sales Process Automation Dashboard...")
    print("Dashboard will be available at: http://localhost:5002")
    print("Features: Discovery calls, SOW generation, Contract management, Project kickoffs")
    
    app.run(
        host='0.0.0.0',
        port=5002,
        debug=True,
        threaded=True
    )