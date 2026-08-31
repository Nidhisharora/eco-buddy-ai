"""
Personal Sustainability Intelligence & Recommendation Platform - Database Operations
Database handlers for intelligence data.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from intelligence.models import (
    SustainabilityProfile, Recommendation, RecommendationFeedback
)

logger = logging.getLogger(__name__)


class IntelligenceDatabase:
    """
    Database handler for intelligence operations.
    """
    
    def __init__(self, db_path: str = 'ecobuddy.db'):
        """Initialize the database handler."""
        self.db_path = db_path
        self._initialize_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
    
    def _initialize_tables(self) -> None:
        """Create intelligence tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intelligence_profiles (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    household_id TEXT,
                    overall_sustainability_score REAL,
                    overall_efficiency_score REAL,
                    energy_score REAL,
                    water_score REAL,
                    food_score REAL,
                    waste_score REAL,
                    transport_score REAL,
                    shopping_score REAL,
                    strengths TEXT,
                    weaknesses TEXT,
                    active_goals TEXT,
                    completed_goals TEXT,
                    active_habits TEXT,
                    habit_consistency REAL,
                    roadmap_progress REAL,
                    roadmap_stage INTEGER,
                    benchmark_comparison TEXT,
                    preferences TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    last_analysis_date TEXT,
                    profile_version INTEGER,
                    notes TEXT
                )
            ''')
            
            # Recommendations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intelligence_recommendations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    impact_score REAL,
                    cost_estimate REAL,
                    savings_estimate REAL,
                    difficulty_score REAL,
                    effort_score REAL,
                    benefit_score REAL,
                    relevance_score REAL,
                    overall_priority REAL,
                    based_on_goals TEXT,
                    based_on_habits TEXT,
                    based_on_weakness TEXT,
                    based_on_benchmark TEXT,
                    based_on_roadmap TEXT,
                    explanation TEXT,
                    why_matters TEXT,
                    how_to_implement TEXT,
                    resources TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    snoozed_until TEXT,
                    acceptance_count INTEGER,
                    completion_count INTEGER,
                    is_duplicate INTEGER,
                    is_conflicting INTEGER,
                    conflicting_with TEXT,
                    tags TEXT,
                    version INTEGER
                )
            ''')
            
            # Feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intelligence_feedback (
                    id TEXT PRIMARY KEY,
                    recommendation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    notes TEXT,
                    rating INTEGER,
                    actual_impact REAL,
                    FOREIGN KEY (recommendation_id) REFERENCES intelligence_recommendations (id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_intel_profiles_user ON intelligence_profiles(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_intel_recs_user ON intelligence_recommendations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_intel_recs_status ON intelligence_recommendations(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_intel_feedback_rec ON intelligence_feedback(recommendation_id)')
            
            conn.commit()
            logger.info("Intelligence tables initialized successfully")
    
    def save_profile(self, profile: SustainabilityProfile) -> str:
        """Save a profile to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO intelligence_profiles (
                    id, user_id, household_id, overall_sustainability_score,
                    overall_efficiency_score, energy_score, water_score,
                    food_score, waste_score, transport_score, shopping_score,
                    strengths, weaknesses, active_goals, completed_goals,
                    active_habits, habit_consistency, roadmap_progress,
                    roadmap_stage, benchmark_comparison, preferences,
                    created_at, updated_at, last_analysis_date,
                    profile_version, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile.id, profile.user_id, profile.household_id,
                profile.overall_sustainability_score, profile.overall_efficiency_score,
                profile.energy_score, profile.water_score, profile.food_score,
                profile.waste_score, profile.transport_score, profile.shopping_score,
                json.dumps([{'category': s.category, 'score': s.score, 'description': s.description} for s in profile.strengths]),
                json.dumps([{'category': w.category, 'score': w.score, 'description': w.description, 'improvement_potential': w.improvement_potential} for w in profile.weaknesses]),
                json.dumps(profile.active_goals), json.dumps(profile.completed_goals),
                json.dumps(profile.active_habits), profile.habit_consistency,
                profile.roadmap_progress, profile.roadmap_stage,
                json.dumps(profile.benchmark_comparison),
                json.dumps(profile.preferences.__dict__),
                profile.created_at.isoformat(), profile.updated_at.isoformat(),
                profile.last_analysis_date.isoformat() if profile.last_analysis_date else None,
                profile.profile_version, profile.notes
            ))
            
            conn.commit()
            return profile.id
    
    def save_recommendation(self, recommendation: Recommendation) -> str:
        """Save a recommendation to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO intelligence_recommendations (
                    id, user_id, title, description, category, priority,
                    status, impact_score, cost_estimate, savings_estimate,
                    difficulty_score, effort_score, benefit_score,
                    relevance_score, overall_priority, based_on_goals,
                    based_on_habits, based_on_weakness, based_on_benchmark,
                    based_on_roadmap, explanation, why_matters,
                    how_to_implement, resources, created_at, expires_at,
                    snoozed_until, acceptance_count, completion_count,
                    is_duplicate, is_conflicting, conflicting_with, tags, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recommendation.id, recommendation.user_id, recommendation.title,
                recommendation.description, recommendation.category.value,
                recommendation.priority.value, recommendation.status.value,
                recommendation.impact_score, recommendation.cost_estimate,
                recommendation.savings_estimate, recommendation.difficulty_score,
                recommendation.effort_score, recommendation.benefit_score,
                recommendation.relevance_score, recommendation.overall_priority,
                json.dumps(recommendation.based_on_goals),
                json.dumps(recommendation.based_on_habits),
                recommendation.based_on_weakness,
                recommendation.based_on_benchmark,
                recommendation.based_on_roadmap,
                recommendation.explanation, recommendation.why_matters,
                recommendation.how_to_implement,
                json.dumps(recommendation.resources),
                recommendation.created_at.isoformat(),
                recommendation.expires_at.isoformat() if recommendation.expires_at else None,
                recommendation.snoozed_until.isoformat() if recommendation.snoozed_until else None,
                recommendation.acceptance_count, recommendation.completion_count,
                1 if recommendation.is_duplicate else 0,
                1 if recommendation.is_conflicting else 0,
                json.dumps(recommendation.conflicting_with),
                json.dumps(recommendation.tags), recommendation.version
            ))
            
            conn.commit()
            return recommendation.id