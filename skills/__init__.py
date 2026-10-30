"""
skills/__init__.py

Auto-discovers and registers all skill modules in this package.
Each module uses the @skill decorator from core.skill_registry.
"""
import importlib
import os

def load_all_skills():
    """Import every .py file in the skills/ directory (except __init__)."""
    skills_dir = os.path.dirname(__file__)
    for filename in os.listdir(skills_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"skills.{filename[:-3]}"
            try:
                importlib.import_module(module_name)
            except Exception as e:
                print(f"⚠️ Could not load skill '{module_name}': {e}")
