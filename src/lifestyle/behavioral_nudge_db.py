"""
Catalog and dataset for behavioral psychology nudges, framing rules, and social benchmarks.
"""

NUDGE_TEMPLATE_CATALOG = [
    {
        "nudge_id": "nudge_streak_loss",
        "category": "habit",
        "framing": "loss_aversion",
        "trigger": lambda ctx: ctx.get("streak_days", 0) >= 3 and ctx.get("current_weekly_carbon_kg", 0) > ctx.get("target_weekly_carbon_kg", 0),
        "headline_template": "Don't break your {streak_days}-day eco streak!",
        "message_template": "You are currently exceeding your target by {excess_carbon:.1f} kg CO2. Skipping today's public transit log will erase your streak bonus.",
        "carbon_saving_factor": 2.5,
        "cost_saving_factor": 1.2,
    },
    {
        "nudge_id": "nudge_budget_waste",
        "category": "finance",
        "framing": "loss_aversion",
        "trigger": lambda ctx: ctx.get("monthly_budget_spent", 0) > ctx.get("monthly_budget_limit", 0) * 0.85,
        "headline_template": "You are losing ${money_at_risk:.2f} in potential carbon tax rebates!",
        "message_template": "Your monthly eco footprint spending is near the limit. Switch 2 meat meals to plant-based this week to protect your end-of-month rebate.",
        "carbon_saving_factor": 4.1,
        "cost_saving_factor": 8.5,
    },
    {
        "nudge_id": "nudge_social_comparison",
        "category": "community",
        "framing": "social_proof",
        "trigger": lambda ctx: ctx.get("current_weekly_carbon_kg", 0) > 40.0,
        "headline_template": "82% of neighbors in your area emit less carbon",
        "message_template": "Top eco-buddies in your district carpool or cycle twice a week, reducing their emissions by 18 kg CO2 below your current usage.",
        "carbon_saving_factor": 5.0,
        "cost_saving_factor": 3.0,
    },
    {
        "nudge_id": "nudge_precommitment_pledge",
        "category": "lifestyle",
        "framing": "commitment_device",
        "trigger": lambda ctx: ctx.get("primary_transport_mode") == "gasoline_car",
        "headline_template": "Lock in your weekend green commitment",
        "message_template": "Pledge now to take electric transit or walk for weekend errands and save up to {potential_carbon:.1f} kg CO2.",
        "carbon_saving_factor": 6.2,
        "cost_saving_factor": 4.5,
    }
]
