"""
Entelech Sales Process Automation Engine
End-to-end sales workflow automation from discovery to project kickoff
"""

import sqlite3
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import hashlib
from decimal import Decimal
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QualificationStatus(Enum):
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    NURTURE = "nurture"
    PENDING_REVIEW = "pending_review"

class SOWStatus(Enum):
    DRAFT = "draft"
    REVIEW = "review"
    SENT = "sent"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ContractStatus(Enum):
    DRAFT = "draft"
    REVIEW = "review"
    SENT_FOR_SIGNATURE = "sent_for_signature"
    PARTIALLY_SIGNED = "partially_signed"
    FULLY_EXECUTED = "fully_executed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class DiscoveryCallData:
    """Data structure for discovery call information"""
    # Company Information
    company_name: str
    company_size: str
    industry: str
    annual_revenue: str
    
    # Contact Information
    primary_contact_name: str
    primary_contact_email: str
    primary_contact_title: str
    decision_maker_name: Optional[str] = None
    decision_maker_title: Optional[str] = None
    
    # Current State Analysis
    current_challenges: str = ""
    manual_processes: str = ""
    time_waste_hours_weekly: int = 0
    estimated_cost_inefficiency: float = 0.0
    current_tools_systems: str = ""
    team_size_affected: int = 0
    
    # Requirements & Goals
    primary_objectives: str = ""
    success_metrics: str = ""
    automation_priorities: str = ""
    integration_requirements: str = ""
    compliance_requirements: str = ""
    security_requirements: str = ""
    
    # Business Case
    budget_range: str = "not_disclosed"
    timeline_urgency: str = "3_months"
    decision_timeline: str = "1_month"
    roi_expectations: str = ""
    
    # Call Details
    sales_rep: str = ""
    call_duration_minutes: int = 60
    next_steps: str = ""
    call_notes: str = ""

@dataclass
class ServiceConfiguration:
    """Configuration for a service in the catalog"""
    service_id: int
    service_name: str
    service_category: str
    base_price: float
    base_hours_required: int
    quantity: int = 1
    customizations: Dict[str, Any] = None

@dataclass
class PricingBreakdown:
    """Detailed pricing breakdown for SOW"""
    base_services_cost: float
    additional_services_cost: float
    complexity_adjustments: float
    discounts_applied: float
    total_project_cost: float
    estimated_hours: int
    effective_hourly_rate: float

class SalesProcessAutomationEngine:
    """Core engine for automating the sales process from discovery to project kickoff"""
    
    def __init__(self, db_path: str = "sales_automation.db"):
        """Initialize the sales automation engine"""
        self.db_path = db_path
        self.conn = None
        self._connect_database()
        
    def _connect_database(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to sales automation database: {self.db_path}")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close_connection(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    # ================================
    # DISCOVERY CALL PROCESSING
    # ================================
    
    def process_discovery_call(self, prospect_id: int, call_data: DiscoveryCallData) -> int:
        """
        Process and store discovery call data with automatic qualification scoring
        
        Args:
            prospect_id: ID of the prospect
            call_data: Discovery call information
            
        Returns:
            call_id: ID of the created discovery call record
        """
        try:
            cursor = self.conn.cursor()
            
            # Calculate qualification scores
            qualification_scores = self._calculate_qualification_scores(call_data)
            
            # Insert discovery call record
            cursor.execute("""
                INSERT INTO discovery_calls (
                    prospect_id, sales_rep, company_name, company_size, industry, annual_revenue,
                    primary_contact_name, primary_contact_email, primary_contact_title,
                    decision_maker_name, decision_maker_title,
                    current_challenges, manual_processes, time_waste_hours_weekly, 
                    estimated_cost_inefficiency, current_tools_systems, team_size_affected,
                    primary_objectives, success_metrics, automation_priorities,
                    integration_requirements, compliance_requirements, security_requirements,
                    budget_range, timeline_urgency, decision_timeline, roi_expectations,
                    pain_level_score, budget_authority_score, timeline_urgency_score,
                    technical_fit_score, overall_qualification_score,
                    call_duration_minutes, next_steps, call_notes,
                    qualified_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prospect_id, call_data.sales_rep, call_data.company_name, call_data.company_size,
                call_data.industry, call_data.annual_revenue,
                call_data.primary_contact_name, call_data.primary_contact_email, call_data.primary_contact_title,
                call_data.decision_maker_name, call_data.decision_maker_title,
                call_data.current_challenges, call_data.manual_processes, call_data.time_waste_hours_weekly,
                call_data.estimated_cost_inefficiency, call_data.current_tools_systems, call_data.team_size_affected,
                call_data.primary_objectives, call_data.success_metrics, call_data.automation_priorities,
                call_data.integration_requirements, call_data.compliance_requirements, call_data.security_requirements,
                call_data.budget_range, call_data.timeline_urgency, call_data.decision_timeline, call_data.roi_expectations,
                qualification_scores['pain_level'], qualification_scores['budget_authority'], qualification_scores['timeline_urgency'],
                qualification_scores['technical_fit'], qualification_scores['overall_score'],
                call_data.call_duration_minutes, call_data.next_steps, call_data.call_notes,
                qualification_scores['status'].value
            ))
            
            call_id = cursor.lastrowid
            self.conn.commit()
            
            # Log automation trigger
            self._log_workflow_automation(
                "discovery_to_sow", call_id, None, "discovery_call_processed",
                f"Discovery call processed with qualification score: {qualification_scores['overall_score']}"
            )
            
            # Trigger automatic SOW generation if qualified
            if qualification_scores['status'] == QualificationStatus.QUALIFIED:
                logger.info(f"Discovery call {call_id} qualified - triggering SOW generation")
                sow_id = self.generate_sow_from_discovery(call_id)
                if sow_id:
                    logger.info(f"SOW {sow_id} automatically generated for discovery call {call_id}")
            
            logger.info(f"Discovery call {call_id} processed successfully")
            return call_id
            
        except Exception as e:
            logger.error(f"Error processing discovery call: {e}")
            raise
    
    def _calculate_qualification_scores(self, call_data: DiscoveryCallData) -> Dict[str, Any]:
        """Calculate qualification scores based on discovery call data"""
        
        # Pain Level Score (0-10)
        pain_score = 0
        if call_data.time_waste_hours_weekly > 20:
            pain_score += 4
        elif call_data.time_waste_hours_weekly > 10:
            pain_score += 2
        elif call_data.time_waste_hours_weekly > 5:
            pain_score += 1
            
        if call_data.estimated_cost_inefficiency > 100000:
            pain_score += 4
        elif call_data.estimated_cost_inefficiency > 50000:
            pain_score += 3
        elif call_data.estimated_cost_inefficiency > 25000:
            pain_score += 2
        elif call_data.estimated_cost_inefficiency > 10000:
            pain_score += 1
            
        if call_data.team_size_affected > 10:
            pain_score += 2
        elif call_data.team_size_affected > 5:
            pain_score += 1
        
        pain_score = min(pain_score, 10)
        
        # Budget Authority Score (0-10)
        budget_score = 0
        budget_mapping = {
            "under_25k": 2,
            "25k_50k": 4,
            "50k_100k": 6,
            "100k_250k": 8,
            "250k_plus": 10,
            "not_disclosed": 3
        }
        budget_score = budget_mapping.get(call_data.budget_range, 3)
        
        if call_data.decision_maker_name:
            budget_score += 2
        
        budget_score = min(budget_score, 10)
        
        # Timeline Urgency Score (0-10)
        timeline_score = 0
        urgency_mapping = {
            "immediate": 10,
            "1_month": 8,
            "3_months": 6,
            "6_months": 4,
            "12_months": 2
        }
        timeline_score = urgency_mapping.get(call_data.timeline_urgency, 3)
        
        # Technical Fit Score (0-10)
        technical_score = 5  # Base score
        
        # Adjust based on company size (better fit for mid-market)
        size_scoring = {
            "11-50": 2,
            "51-200": 3,
            "201-500": 2,
            "501-1000": 1,
            "1000+": 1,
            "1-10": 1
        }
        technical_score += size_scoring.get(call_data.company_size, 1)
        
        # Industry fit scoring
        high_fit_industries = ["technology", "professional services", "healthcare", "finance", "real estate"]
        if call_data.industry.lower() in high_fit_industries:
            technical_score += 2
        
        technical_score = min(technical_score, 10)
        
        # Overall Score (0-100)
        overall_score = int((pain_score * 0.3 + budget_score * 0.3 + timeline_score * 0.2 + technical_score * 0.2) * 10)
        
        # Determine qualification status
        if overall_score >= 70:
            status = QualificationStatus.QUALIFIED
        elif overall_score >= 50:
            status = QualificationStatus.NURTURE
        elif overall_score >= 30:
            status = QualificationStatus.PENDING_REVIEW
        else:
            status = QualificationStatus.DISQUALIFIED
        
        return {
            "pain_level": pain_score,
            "budget_authority": budget_score,
            "timeline_urgency": timeline_score,
            "technical_fit": technical_score,
            "overall_score": overall_score,
            "status": status
        }
    
    # ================================
    # SOW GENERATION
    # ================================
    
    def generate_sow_from_discovery(self, call_id: int) -> Optional[int]:
        """
        Generate Statement of Work based on discovery call data
        
        Args:
            call_id: ID of the discovery call
            
        Returns:
            sow_id: ID of the generated SOW, or None if generation failed
        """
        try:
            cursor = self.conn.cursor()
            
            # Get discovery call data
            cursor.execute("SELECT * FROM discovery_calls WHERE call_id = ?", (call_id,))
            call_data = cursor.fetchone()
            
            if not call_data:
                logger.error(f"Discovery call {call_id} not found")
                return None
            
            # Analyze requirements and recommend services
            recommended_services = self._analyze_requirements_and_recommend_services(call_data)
            
            # Calculate pricing
            pricing = self._calculate_project_pricing(call_data, recommended_services)
            
            # Generate SOW content
            sow_content = self._generate_sow_content(call_data, recommended_services, pricing)
            
            # Create payment schedule
            payment_schedule = self._create_payment_schedule(pricing.total_project_cost, len(recommended_services))
            
            # Insert SOW record
            cursor.execute("""
                INSERT INTO generated_sows (
                    discovery_call_id, project_title, project_description,
                    business_objectives, success_criteria, included_services,
                    deliverables, timeline_weeks, project_phases,
                    base_services_cost, additional_services_cost, complexity_adjustments,
                    discounts_applied, total_project_cost, payment_schedule,
                    exclusions, assumptions, change_request_process, acceptance_criteria,
                    expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                call_id, sow_content['title'], sow_content['description'],
                sow_content['objectives'], sow_content['success_criteria'], json.dumps(recommended_services),
                sow_content['deliverables'], pricing.estimated_hours // 40 + 1, json.dumps(sow_content['phases']),
                pricing.base_services_cost, pricing.additional_services_cost, pricing.complexity_adjustments,
                pricing.discounts_applied, pricing.total_project_cost, json.dumps(payment_schedule),
                sow_content['exclusions'], sow_content['assumptions'], 
                sow_content['change_request_process'], sow_content['acceptance_criteria'],
                datetime.now() + timedelta(days=30)  # Expires in 30 days
            ))
            
            sow_id = cursor.lastrowid
            self.conn.commit()
            
            # Log workflow automation
            self._log_workflow_automation(
                "discovery_to_sow", call_id, sow_id, "sow_generated",
                f"SOW automatically generated with total cost: ${pricing.total_project_cost:,.2f}"
            )
            
            logger.info(f"SOW {sow_id} generated for discovery call {call_id}")
            return sow_id
            
        except Exception as e:
            logger.error(f"Error generating SOW for call {call_id}: {e}")
            return None
    
    def _analyze_requirements_and_recommend_services(self, call_data: sqlite3.Row) -> List[ServiceConfiguration]:
        """Analyze discovery call data and recommend appropriate services"""
        
        # Get available services from catalog
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM service_catalog WHERE is_active = 1")
        services = cursor.fetchall()
        
        recommended = []
        
        # Automation Development (Core Service)
        automation_service = next((s for s in services if 'automation_development' in s['service_category']), None)
        if automation_service:
            # Determine complexity based on requirements
            complexity_factors = 1.0
            
            if call_data['integration_requirements'] and len(call_data['integration_requirements']) > 100:
                complexity_factors += 0.3
            if call_data['compliance_requirements'] and len(call_data['compliance_requirements']) > 50:
                complexity_factors += 0.2
            if call_data['security_requirements'] and len(call_data['security_requirements']) > 50:
                complexity_factors += 0.2
            if call_data['team_size_affected'] > 20:
                complexity_factors += 0.3
            
            recommended.append(ServiceConfiguration(
                service_id=automation_service['service_id'],
                service_name=automation_service['service_name'],
                service_category=automation_service['service_category'],
                base_price=automation_service['base_price'] * complexity_factors,
                base_hours_required=int(automation_service['base_hours_required'] * complexity_factors),
                quantity=1,
                customizations={'complexity_multiplier': complexity_factors}
            ))
        
        # Process Optimization (if significant manual processes)
        if call_data['time_waste_hours_weekly'] > 10:
            process_service = next((s for s in services if 'process_optimization' in s['service_category']), None)
            if process_service:
                recommended.append(ServiceConfiguration(
                    service_id=process_service['service_id'],
                    service_name=process_service['service_name'],
                    service_category=process_service['service_category'],
                    base_price=process_service['base_price'],
                    base_hours_required=process_service['base_hours_required'],
                    quantity=1
                ))
        
        # Integration Setup (if multiple integrations needed)
        if call_data['integration_requirements'] and 'integration' in call_data['integration_requirements'].lower():
            integration_service = next((s for s in services if 'integration_setup' in s['service_category']), None)
            if integration_service:
                # Estimate number of integrations
                integration_count = call_data['integration_requirements'].lower().count('api') + \
                                  call_data['integration_requirements'].lower().count('system') + 1
                
                recommended.append(ServiceConfiguration(
                    service_id=integration_service['service_id'],
                    service_name=integration_service['service_name'],
                    service_category=integration_service['service_category'],
                    base_price=integration_service['base_price'],
                    base_hours_required=integration_service['base_hours_required'],
                    quantity=min(integration_count, 5)  # Cap at 5 integrations
                ))
        
        # Ongoing Management (for larger companies)
        company_size_scores = {'201-500': 1, '501-1000': 1, '1000+': 1}
        if call_data['company_size'] in company_size_scores:
            ongoing_service = next((s for s in services if 'ongoing_management' in s['service_category']), None)
            if ongoing_service:
                recommended.append(ServiceConfiguration(
                    service_id=ongoing_service['service_id'],
                    service_name=ongoing_service['service_name'],
                    service_category=ongoing_service['service_category'],
                    base_price=ongoing_service['base_price'],
                    base_hours_required=ongoing_service['base_hours_required'],
                    quantity=1
                ))
        
        # Training (if large team affected)
        if call_data['team_size_affected'] > 10:
            training_service = next((s for s in services if 'training' in s['service_category']), None)
            if training_service:
                recommended.append(ServiceConfiguration(
                    service_id=training_service['service_id'],
                    service_name=training_service['service_name'],
                    service_category=training_service['service_category'],
                    base_price=training_service['base_price'],
                    base_hours_required=training_service['base_hours_required'],
                    quantity=1
                ))
        
        return recommended
    
    def _calculate_project_pricing(self, call_data: sqlite3.Row, services: List[ServiceConfiguration]) -> PricingBreakdown:
        """Calculate detailed project pricing with all adjustments"""
        
        base_cost = sum(service.base_price * service.quantity for service in services)
        total_hours = sum(service.base_hours_required * service.quantity for service in services)
        
        # Complexity adjustments
        complexity_adjustment = 0.0
        
        # Company size adjustments
        size_adjustments = {
            '1-10': -0.15,      # 15% discount for small companies
            '11-50': -0.05,     # 5% discount
            '51-200': 0.0,      # Standard pricing
            '201-500': 0.1,     # 10% premium
            '501-1000': 0.15,   # 15% premium
            '1000+': 0.2        # 20% premium
        }
        complexity_adjustment += base_cost * size_adjustments.get(call_data['company_size'], 0.0)
        
        # Industry adjustments
        industry_premiums = {
            'healthcare': 0.15,
            'finance': 0.20,
            'government': 0.25
        }
        if call_data['industry'].lower() in industry_premiums:
            complexity_adjustment += base_cost * industry_premiums[call_data['industry'].lower()]
        
        # Timeline urgency adjustments
        urgency_premiums = {
            'immediate': 0.25,
            '1_month': 0.15,
            '3_months': 0.05,
            '6_months': 0.0,
            '12_months': -0.05
        }
        complexity_adjustment += base_cost * urgency_premiums.get(call_data['timeline_urgency'], 0.0)
        
        # Apply discounts
        discounts = 0.0
        
        # Volume discount for large projects
        if base_cost > 200000:
            discounts += base_cost * 0.1  # 10% discount for projects > $200K
        elif base_cost > 100000:
            discounts += base_cost * 0.05  # 5% discount for projects > $100K
        
        # First-time client discount
        discounts += base_cost * 0.05  # 5% new client discount
        
        # Calculate totals
        additional_services_cost = 0.0  # For any additional services added later
        total_cost = base_cost + additional_services_cost + complexity_adjustment - discounts
        
        # Ensure minimum project value
        total_cost = max(total_cost, 25000.0)
        
        return PricingBreakdown(
            base_services_cost=base_cost,
            additional_services_cost=additional_services_cost,
            complexity_adjustments=complexity_adjustment,
            discounts_applied=discounts,
            total_project_cost=total_cost,
            estimated_hours=total_hours,
            effective_hourly_rate=total_cost / total_hours if total_hours > 0 else 0
        )
    
    def _generate_sow_content(self, call_data: sqlite3.Row, services: List[ServiceConfiguration], 
                            pricing: PricingBreakdown) -> Dict[str, str]:
        """Generate detailed SOW content based on discovery call and services"""
        
        content = {}
        
        # Project Title
        content['title'] = f"{call_data['company_name']} - Business Process Automation & Optimization"
        
        # Project Description
        content['description'] = f"""
        This project will deliver comprehensive business process automation and optimization solutions 
        for {call_data['company_name']}, addressing their current challenges with manual processes and 
        inefficiencies. Our solution will automate key workflows, integrate existing systems, and 
        optimize operations to achieve significant time savings and cost reductions.
        
        Current State: {call_data['current_challenges']}
        
        Proposed Solution: Custom automation platform integrating with existing systems to eliminate 
        manual processes and optimize workflow efficiency.
        """
        
        # Business Objectives
        content['objectives'] = call_data['primary_objectives'] or f"""
        - Eliminate {call_data['time_waste_hours_weekly']} hours of weekly manual work
        - Reduce operational costs by ${call_data['estimated_cost_inefficiency']:,.2f} annually
        - Improve process efficiency and consistency across {call_data['team_size_affected']} team members
        - Enable scalable growth through automated workflows
        """
        
        # Success Criteria
        content['success_criteria'] = call_data['success_metrics'] or """
        - 80% reduction in manual processing time
        - 95% accuracy in automated processes
        - ROI achievement within 12 months
        - Full team adoption and utilization
        - Seamless integration with existing systems
        """
        
        # Deliverables
        deliverables_list = []
        for service in services:
            if 'automation_development' in service.service_category:
                deliverables_list.extend([
                    "Custom automation workflows and business logic",
                    "User interface for process management",
                    "System integration and API connections",
                    "Data migration and cleanup processes"
                ])
            elif 'process_optimization' in service.service_category:
                deliverables_list.extend([
                    "Process analysis and optimization recommendations",
                    "Workflow redesign and efficiency improvements",
                    "Standard operating procedures documentation"
                ])
            elif 'integration_setup' in service.service_category:
                deliverables_list.extend([
                    "API integrations with existing systems",
                    "Data synchronization and mapping",
                    "Integration testing and validation"
                ])
            elif 'training' in service.service_category:
                deliverables_list.extend([
                    "User training materials and documentation",
                    "Live training sessions for team members",
                    "Ongoing support and knowledge transfer"
                ])
        
        content['deliverables'] = "\\n".join(f"• {item}" for item in deliverables_list)
        
        # Project Phases
        phases = [
            {
                "phase": 1,
                "name": "Discovery & Planning",
                "duration_weeks": 1,
                "description": "Detailed requirements analysis, system architecture design, and project planning"
            },
            {
                "phase": 2,
                "name": "Development & Integration", 
                "duration_weeks": pricing.estimated_hours // 40,
                "description": "Core automation development, system integrations, and testing"
            },
            {
                "phase": 3,
                "name": "Testing & Training",
                "duration_weeks": 1,
                "description": "User acceptance testing, team training, and knowledge transfer"
            },
            {
                "phase": 4,
                "name": "Launch & Support",
                "duration_weeks": 1,
                "description": "Production deployment, go-live support, and transition to operations"
            }
        ]
        content['phases'] = phases
        
        # Exclusions
        content['exclusions'] = """
        • Third-party software licensing costs (client responsibility)
        • Hardware or infrastructure costs beyond software development
        • Ongoing maintenance beyond 30-day warranty period
        • Changes to original scope without formal change request approval
        • Training for more than 10 users (additional training available separately)
        """
        
        # Assumptions
        content['assumptions'] = f"""
        • Client will provide timely access to required systems and stakeholders
        • Existing systems have available APIs or integration capabilities
        • Client technical team will be available for collaboration and testing
        • Project timeline assumes standard business hours (M-F, 9-5 {call_data['company_name']} timezone)
        • No major system changes will occur during project implementation
        """
        
        # Change Request Process
        content['change_request_process'] = """
        All changes to project scope must be documented in writing and approved by both parties. 
        Change requests will be evaluated for impact on timeline, cost, and deliverables. 
        Additional work will be billed at standard hourly rates with prior approval.
        """
        
        # Acceptance Criteria
        content['acceptance_criteria'] = """
        Each deliverable will be considered complete upon successful demonstration of functionality, 
        passing of all defined tests, and written acceptance by client project stakeholder. 
        Final project acceptance requires successful completion of all deliverables and 
        30-day production stability period.
        """
        
        return content
    
    def _create_payment_schedule(self, total_cost: float, num_services: int) -> List[Dict[str, Any]]:
        """Create milestone-based payment schedule"""
        
        # Standard payment schedule based on project phases
        if total_cost < 50000:
            # Small projects: 50% upfront, 50% on completion
            schedule = [
                {
                    "milestone": "Project Start",
                    "percentage": 50.0,
                    "amount": total_cost * 0.5,
                    "description": "Initial payment to begin project development"
                },
                {
                    "milestone": "Project Completion",
                    "percentage": 50.0,
                    "amount": total_cost * 0.5,
                    "description": "Final payment upon successful project delivery"
                }
            ]
        elif total_cost < 150000:
            # Medium projects: 30% / 40% / 30%
            schedule = [
                {
                    "milestone": "Project Start",
                    "percentage": 30.0,
                    "amount": total_cost * 0.3,
                    "description": "Initial payment to begin project development"
                },
                {
                    "milestone": "Development Milestone",
                    "percentage": 40.0,
                    "amount": total_cost * 0.4,
                    "description": "Payment upon completion of core development"
                },
                {
                    "milestone": "Project Completion",
                    "percentage": 30.0,
                    "amount": total_cost * 0.3,
                    "description": "Final payment upon successful project delivery"
                }
            ]
        else:
            # Large projects: 25% / 25% / 25% / 25%
            schedule = [
                {
                    "milestone": "Project Start",
                    "percentage": 25.0,
                    "amount": total_cost * 0.25,
                    "description": "Initial payment to begin project development"
                },
                {
                    "milestone": "Development Phase 1",
                    "percentage": 25.0,
                    "amount": total_cost * 0.25,
                    "description": "Payment upon completion of phase 1 development"
                },
                {
                    "milestone": "Development Phase 2",
                    "percentage": 25.0,
                    "amount": total_cost * 0.25,
                    "description": "Payment upon completion of phase 2 development"
                },
                {
                    "milestone": "Project Completion",
                    "percentage": 25.0,
                    "amount": total_cost * 0.25,
                    "description": "Final payment upon successful project delivery"
                }
            ]
        
        return schedule
    
    # ================================
    # CONTRACT GENERATION
    # ================================
    
    def generate_contract_from_sow(self, sow_id: int, template_id: int = 1) -> Optional[int]:
        """
        Generate contract from approved SOW
        
        Args:
            sow_id: ID of the approved SOW
            template_id: ID of the contract template to use
            
        Returns:
            contract_id: ID of the generated contract, or None if generation failed
        """
        try:
            cursor = self.conn.cursor()
            
            # Get SOW data
            cursor.execute("""
                SELECT s.*, d.* FROM generated_sows s 
                JOIN discovery_calls d ON s.discovery_call_id = d.call_id 
                WHERE s.sow_id = ?
            """, (sow_id,))
            sow_data = cursor.fetchone()
            
            if not sow_data or sow_data['sow_status'] != 'approved':
                logger.error(f"SOW {sow_id} not found or not approved")
                return None
            
            # Get contract template
            cursor.execute("SELECT * FROM contract_templates WHERE template_id = ?", (template_id,))
            template = cursor.fetchone()
            
            if not template:
                logger.error(f"Contract template {template_id} not found")
                return None
            
            # Generate contract content
            contract_content = self._generate_contract_content(sow_data, template)
            contract_number = f"ENT-{datetime.now().strftime('%Y%m')}-{sow_id:04d}"
            
            # Calculate contract dates
            project_start = datetime.now().date() + timedelta(days=14)  # 2 weeks from now
            project_duration_weeks = sow_data['timeline_weeks']
            project_end = project_start + timedelta(weeks=project_duration_weeks)
            contract_expiration = datetime.now().date() + timedelta(days=365)  # 1 year contract
            
            # Insert contract record
            cursor.execute("""
                INSERT INTO generated_contracts (
                    sow_id, template_id, contract_number, contract_title,
                    client_legal_name, client_address, client_signatory_name,
                    client_signatory_title, client_signatory_email,
                    provider_signatory_name, provider_signatory_title,
                    total_contract_value, payment_schedule,
                    project_start_date, project_end_date, contract_effective_date, contract_expiration_date,
                    contract_content, contract_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sow_id, template_id, contract_number, sow_data['project_title'],
                sow_data['company_name'], f"{sow_data['company_name']} Address", # TODO: Get actual address
                sow_data['primary_contact_name'], sow_data['primary_contact_title'], sow_data['primary_contact_email'],
                "Jordan Martinez", "CEO",  # Default Entelech signatory
                sow_data['total_project_cost'], sow_data['payment_schedule'],
                project_start, project_end, datetime.now().date(), contract_expiration,
                contract_content, hashlib.sha256(contract_content.encode()).hexdigest()
            ))
            
            contract_id = cursor.lastrowid
            self.conn.commit()
            
            # Log workflow automation
            self._log_workflow_automation(
                "sow_to_contract", sow_id, contract_id, "contract_generated",
                f"Contract {contract_number} generated from SOW {sow_id}"
            )
            
            logger.info(f"Contract {contract_id} generated for SOW {sow_id}")
            return contract_id
            
        except Exception as e:
            logger.error(f"Error generating contract for SOW {sow_id}: {e}")
            return None
    
    def _generate_contract_content(self, sow_data: sqlite3.Row, template: sqlite3.Row) -> str:
        """Generate complete contract content from template and SOW data"""
        
        content = template['template_content']
        
        # Contract-specific variables
        variables = {
            "{{CONTRACT_NUMBER}}": f"ENT-{datetime.now().strftime('%Y%m')}-{sow_data['sow_id']:04d}",
            "{{CONTRACT_DATE}}": datetime.now().strftime('%B %d, %Y'),
            "{{CLIENT_COMPANY_NAME}}": sow_data['company_name'],
            "{{CLIENT_CONTACT_NAME}}": sow_data['primary_contact_name'],
            "{{CLIENT_CONTACT_TITLE}}": sow_data['primary_contact_title'],
            "{{CLIENT_EMAIL}}": sow_data['primary_contact_email'],
            "{{PROJECT_TITLE}}": sow_data['project_title'],
            "{{PROJECT_DESCRIPTION}}": sow_data['project_description'],
            "{{TOTAL_CONTRACT_VALUE}}": f"${sow_data['total_project_cost']:,.2f}",
            "{{PROJECT_TIMELINE}}": f"{sow_data['timeline_weeks']} weeks",
            "{{DELIVERABLES}}": sow_data['deliverables'],
            "{{PAYMENT_TERMS}}": sow_data.get('payment_terms', '30 days'),
            "{{GOVERNING_LAW}}": template['governing_law'],
            "{{LIABILITY_CAP}}": f"{template['liability_cap_percentage']}% of contract value",
            "{{WARRANTY_PERIOD}}": f"{template['warranty_period_months']} months",
            "{{PROVIDER_SIGNATORY}}": "Jordan Martinez, CEO"
        }
        
        # Replace all variables
        for variable, value in variables.items():
            content = content.replace(variable, str(value))
        
        return content
    
    # ================================
    # PAYMENT PROCESSING SETUP
    # ================================
    
    def setup_payment_processing(self, contract_id: int, payment_provider: str = "stripe") -> Optional[int]:
        """
        Setup automated payment processing for signed contract
        
        Args:
            contract_id: ID of the signed contract
            payment_provider: Payment processor to use
            
        Returns:
            config_id: ID of the payment configuration, or None if setup failed
        """
        try:
            cursor = self.conn.cursor()
            
            # Get contract data
            cursor.execute("""
                SELECT c.*, s.payment_schedule FROM generated_contracts c
                JOIN generated_sows s ON c.sow_id = s.sow_id
                WHERE c.contract_id = ? AND c.contract_status = 'fully_executed'
            """, (contract_id,))
            contract_data = cursor.fetchone()
            
            if not contract_data:
                logger.error(f"Contract {contract_id} not found or not fully executed")
                return None
            
            # Parse payment schedule
            payment_schedule = json.loads(contract_data['payment_schedule'])
            
            # Create payment configuration
            cursor.execute("""
                INSERT INTO payment_configurations (
                    contract_id, payment_provider, payment_type, total_amount,
                    currency, payment_schedule, auto_invoice_enabled, late_fee_enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id, payment_provider, "milestone_based", contract_data['total_contract_value'],
                "USD", json.dumps(payment_schedule), True, True
            ))
            
            config_id = cursor.lastrowid
            
            # Generate initial invoices for immediate milestones
            self._generate_milestone_invoices(config_id, payment_schedule)
            
            self.conn.commit()
            
            # Log workflow automation
            self._log_workflow_automation(
                "contract_to_payment", contract_id, config_id, "payment_setup",
                f"Payment processing configured for contract {contract_data['contract_number']}"
            )
            
            logger.info(f"Payment processing configured for contract {contract_id}")
            return config_id
            
        except Exception as e:
            logger.error(f"Error setting up payment processing for contract {contract_id}: {e}")
            return None
    
    def _generate_milestone_invoices(self, config_id: int, payment_schedule: List[Dict[str, Any]]):
        """Generate invoices for immediate payment milestones"""
        
        cursor = self.conn.cursor()
        
        for milestone in payment_schedule:
            # Generate invoice for "Project Start" milestone immediately
            if milestone['milestone'] == "Project Start":
                invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{config_id:04d}"
                due_date = datetime.now().date() + timedelta(days=7)  # Due in 7 days
                
                cursor.execute("""
                    INSERT INTO payment_transactions (
                        config_id, transaction_type, amount, invoice_number,
                        invoice_due_date, milestone_description, payment_method,
                        transaction_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    config_id, "invoice", milestone['amount'], invoice_number,
                    due_date, milestone['description'], "credit_card", "pending"
                ))
                
                logger.info(f"Invoice {invoice_number} generated for milestone: {milestone['milestone']}")
    
    # ================================
    # PROJECT KICKOFF AUTOMATION
    # ================================
    
    def trigger_project_kickoff(self, contract_id: int) -> Optional[int]:
        """
        Trigger automated project kickoff after first payment received
        
        Args:
            contract_id: ID of the contract with received payment
            
        Returns:
            kickoff_id: ID of the project kickoff record, or None if failed
        """
        try:
            cursor = self.conn.cursor()
            
            # Get contract and payment data
            cursor.execute("""
                SELECT c.*, s.project_title, s.included_services 
                FROM generated_contracts c
                JOIN generated_sows s ON c.sow_id = s.sow_id
                WHERE c.contract_id = ?
            """, (contract_id,))
            contract_data = cursor.fetchone()
            
            if not contract_data:
                logger.error(f"Contract {contract_id} not found")
                return None
            
            # Verify first payment received
            cursor.execute("""
                SELECT COUNT(*) as payment_count FROM payment_configurations pc
                JOIN payment_transactions pt ON pc.config_id = pt.config_id
                WHERE pc.contract_id = ? AND pt.transaction_status = 'completed'
                AND pt.transaction_type = 'payment'
            """, (contract_id,))
            
            payment_check = cursor.fetchone()
            if payment_check['payment_count'] == 0:
                logger.warning(f"No payments received for contract {contract_id} - kickoff not triggered")
                return None
            
            # Determine appropriate kickoff template
            services = json.loads(contract_data['included_services'])
            template_id = self._select_kickoff_template(services)
            
            # Generate unique project code
            project_code = f"ENT{datetime.now().strftime('%y%m')}{contract_id:03d}"
            
            # Create project kickoff record
            cursor.execute("""
                INSERT INTO project_kickoffs (
                    contract_id, template_id, project_code, project_name,
                    project_manager, kickoff_scheduled_date
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                contract_id, template_id, project_code, contract_data['project_title'],
                "Alex Thompson",  # Default PM - should be configurable
                datetime.now() + timedelta(days=3)  # Schedule kickoff in 3 days
            ))
            
            kickoff_id = cursor.lastrowid
            
            # Initialize kickoff checklist and tasks
            self._initialize_project_kickoff_tasks(kickoff_id, template_id)
            
            self.conn.commit()
            
            # Log workflow automation
            self._log_workflow_automation(
                "payment_to_kickoff", contract_id, kickoff_id, "kickoff_triggered",
                f"Project kickoff initiated for project {project_code}"
            )
            
            logger.info(f"Project kickoff {kickoff_id} triggered for contract {contract_id}")
            return kickoff_id
            
        except Exception as e:
            logger.error(f"Error triggering project kickoff for contract {contract_id}: {e}")
            return None
    
    def _select_kickoff_template(self, services: List[Dict[str, Any]]) -> int:
        """Select appropriate kickoff template based on included services"""
        
        # Analyze service categories to determine best template
        categories = [service.get('service_category', '') for service in services]
        
        if 'automation_development' in categories and len(categories) > 2:
            return 1  # Complex automation template
        elif 'automation_development' in categories:
            return 2  # Standard automation template
        else:
            return 3  # Basic services template
    
    def _initialize_project_kickoff_tasks(self, kickoff_id: int, template_id: int):
        """Initialize project kickoff tasks based on template"""
        
        cursor = self.conn.cursor()
        
        # Get template data
        cursor.execute("SELECT * FROM kickoff_templates WHERE template_id = ?", (template_id,))
        template = cursor.fetchone()
        
        if template:
            # Initialize kickoff deliverables from template
            deliverables = json.loads(template['initial_deliverables'])
            
            cursor.execute("""
                UPDATE project_kickoffs 
                SET kickoff_deliverables = ?
                WHERE kickoff_id = ?
            """, (json.dumps(deliverables), kickoff_id))
            
            logger.info(f"Initialized {len(deliverables)} kickoff tasks for project {kickoff_id}")
    
    # ================================
    # WORKFLOW AUTOMATION HELPERS
    # ================================
    
    def _log_workflow_automation(self, process_type: str, source_id: int, target_id: Optional[int],
                                action: str, description: str, user: str = "system"):
        """Log workflow automation events for tracking and debugging"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO workflow_automation_log (
                process_type, source_record_id, target_record_id, automation_trigger,
                automation_action, automation_status, automation_result, triggered_by_user
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            process_type, source_id, target_id, "automatic_trigger", action,
            "completed", json.dumps({"description": description, "timestamp": datetime.now().isoformat()}),
            user
        ))
        
        self.conn.commit()
    
    def get_workflow_status(self, process_type: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get workflow automation status and history"""
        
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM workflow_automation_log WHERE 1=1"
        params = []
        
        if process_type:
            query += " AND process_type = ?"
            params.append(process_type)
        
        if status:
            query += " AND automation_status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT 100"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        return [dict(row) for row in results]
    
    # ================================
    # SALES PROCESS ANALYTICS
    # ================================
    
    def get_sales_process_analytics(self, date_range: Tuple[date, date]) -> Dict[str, Any]:
        """Get comprehensive analytics on the sales process performance"""
        
        cursor = self.conn.cursor()
        
        analytics = {
            "discovery_calls": {},
            "sow_generation": {},
            "contract_execution": {},
            "payment_processing": {},
            "project_kickoffs": {},
            "automation_efficiency": {}
        }
        
        # Discovery call analytics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_calls,
                AVG(overall_qualification_score) as avg_qualification_score,
                SUM(CASE WHEN qualified_status = 'qualified' THEN 1 ELSE 0 END) as qualified_count,
                AVG(call_duration_minutes) as avg_call_duration,
                AVG(time_waste_hours_weekly) as avg_time_waste,
                AVG(estimated_cost_inefficiency) as avg_cost_inefficiency
            FROM discovery_calls 
            WHERE call_date BETWEEN ? AND ?
        """, (date_range[0], date_range[1]))
        
        discovery_stats = cursor.fetchone()
        analytics["discovery_calls"] = dict(discovery_stats) if discovery_stats else {}
        
        # SOW generation analytics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sows,
                SUM(CASE WHEN sow_status = 'approved' THEN 1 ELSE 0 END) as approved_count,
                AVG(total_project_cost) as avg_project_value,
                SUM(total_project_cost) as total_pipeline_value,
                AVG(timeline_weeks) as avg_timeline_weeks
            FROM generated_sows s
            JOIN discovery_calls d ON s.discovery_call_id = d.call_id
            WHERE d.call_date BETWEEN ? AND ?
        """, (date_range[0], date_range[1]))
        
        sow_stats = cursor.fetchone()
        analytics["sow_generation"] = dict(sow_stats) if sow_stats else {}
        
        # Contract execution analytics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_contracts,
                SUM(CASE WHEN contract_status = 'fully_executed' THEN 1 ELSE 0 END) as executed_count,
                SUM(CASE WHEN contract_status = 'fully_executed' THEN total_contract_value ELSE 0 END) as closed_revenue,
                AVG(CASE WHEN fully_executed_at IS NOT NULL 
                    THEN DATEDIFF(fully_executed_at, sent_for_signature_at) ELSE NULL END) as avg_signing_days
            FROM generated_contracts c
            JOIN generated_sows s ON c.sow_id = s.sow_id
            JOIN discovery_calls d ON s.discovery_call_id = d.call_id
            WHERE d.call_date BETWEEN ? AND ?
        """, (date_range[0], date_range[1]))
        
        contract_stats = cursor.fetchone()
        analytics["contract_execution"] = dict(contract_stats) if contract_stats else {}
        
        # Calculate conversion rates
        total_calls = analytics["discovery_calls"].get("total_calls", 0)
        qualified_calls = analytics["discovery_calls"].get("qualified_count", 0)
        approved_sows = analytics["sow_generation"].get("approved_count", 0)
        executed_contracts = analytics["contract_execution"].get("executed_count", 0)
        
        analytics["conversion_rates"] = {
            "call_to_qualified": (qualified_calls / total_calls * 100) if total_calls > 0 else 0,
            "qualified_to_sow": (approved_sows / qualified_calls * 100) if qualified_calls > 0 else 0,
            "sow_to_contract": (executed_contracts / approved_sows * 100) if approved_sows > 0 else 0,
            "overall_conversion": (executed_contracts / total_calls * 100) if total_calls > 0 else 0
        }
        
        # Automation efficiency
        cursor.execute("""
            SELECT 
                process_type,
                COUNT(*) as total_automations,
                SUM(CASE WHEN automation_status = 'completed' THEN 1 ELSE 0 END) as successful_automations,
                AVG(processing_duration_seconds) as avg_processing_time
            FROM workflow_automation_log 
            WHERE processing_start_time BETWEEN ? AND ?
            GROUP BY process_type
        """, (date_range[0], date_range[1]))
        
        automation_stats = cursor.fetchall()
        analytics["automation_efficiency"] = {
            row["process_type"]: {
                "total": row["total_automations"],
                "successful": row["successful_automations"],
                "success_rate": (row["successful_automations"] / row["total_automations"] * 100) if row["total_automations"] > 0 else 0,
                "avg_processing_time": row["avg_processing_time"]
            } for row in automation_stats
        }
        
        return analytics