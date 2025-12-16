"""
prompt_builder.py - Per-Clinic System Prompt Builder

Builds customized system prompts for Deepgram Voice Agent based on
clinic configuration stored in the database.

The prompt includes:
- CARES Framework (Connect, Acknowledge, Respond, Empathize, Summarize)
- Professional dental receptionist conversation patterns
- Clinic-specific information and branding
- Function calling schemas for appointment booking
- Objection handling and patient care scripts

Research-Based Implementation (December 2025):
- Real dental receptionist communication patterns
- Deepgram Voice Agent best practices
- Twilio Media Streams optimization
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from db import Client

# Import the research-based dental scripts
from dental_scripts import build_dental_system_prompt, GREETINGS

# -----------------------------------------------------------------------------
# Available Deepgram Voices (Aura-2)
# Recommended: Female voices for dental receptionist (Asteria, Luna tested best)
# -----------------------------------------------------------------------------

DEEPGRAM_VOICES = {
    # American English - Female (Recommended for dental)
    "aura-asteria-en": {"name": "Asteria", "gender": "female", "accent": "American", "warmth": "high"},
    "aura-luna-en": {"name": "Luna", "gender": "female", "accent": "American", "warmth": "medium"},
    "aura-stella-en": {"name": "Stella", "gender": "female", "accent": "American", "warmth": "medium"},
    # American English - Male
    "aura-orion-en": {"name": "Orion", "gender": "male", "accent": "American", "warmth": "medium"},
    "aura-arcas-en": {"name": "Arcas", "gender": "male", "accent": "American", "warmth": "medium"},
    # British English
    "aura-athena-en": {"name": "Athena", "gender": "female", "accent": "British", "warmth": "high"},
    "aura-hera-en": {"name": "Hera", "gender": "female", "accent": "British", "warmth": "medium"},
    "aura-perseus-en": {"name": "Perseus", "gender": "male", "accent": "British", "warmth": "medium"},
}

# Default voice - Asteria is warm and professional, ideal for dental
DEFAULT_VOICE = "aura-asteria-en"


# -----------------------------------------------------------------------------
# Time-Based Greeting Selection
# -----------------------------------------------------------------------------

def get_time_of_day() -> str:
    """Get current time of day for greeting selection."""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    else:
        return "evening"


# Available slots template (in production, fetch from scheduling system)
DEFAULT_AVAILABLE_SLOTS = """For scheduling, offer these specific times (always give 2-3 options):
- Today: Limited - check for urgent/emergency slots
- Tomorrow: 9:00 AM, 10:30 AM, 2:00 PM, 3:30 PM
- Day after: 9:00 AM, 11:00 AM, 1:00 PM, 4:00 PM

Remember: Never ask "when would you like to come in?" - always offer specific options."""


# -----------------------------------------------------------------------------
# Enhanced Function Calling Schemas
# -----------------------------------------------------------------------------

FUNCTION_SCHEMAS = [
    {
        "name": "book_appointment",
        "description": "Book a dental appointment for a patient. Use this when you have collected all necessary information.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "Full name of the patient"
                },
                "phone_number": {
                    "type": "string", 
                    "description": "Patient's phone number for confirmation texts"
                },
                "date": {
                    "type": "string",
                    "description": "Appointment date in YYYY-MM-DD format"
                },
                "time": {
                    "type": "string",
                    "description": "Appointment time in HH:MM format (24-hour)"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for visit: cleaning, checkup, toothache, crown, filling, emergency, consultation, other"
                },
                "is_new_patient": {
                    "type": "boolean",
                    "description": "True if this is a new patient to the practice"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["routine", "soon", "urgent", "emergency"],
                    "description": "How urgent is the appointment need"
                },
                "notes": {
                    "type": "string",
                    "description": "Any special notes or concerns from the patient"
                }
            },
            "required": ["patient_name", "date", "time", "reason"]
        }
    },
    {
        "name": "check_availability",
        "description": "Check available appointment slots. Call this before offering specific times to the patient.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to check in YYYY-MM-DD format"
                },
                "time_preference": {
                    "type": "string",
                    "enum": ["early_morning", "morning", "afternoon", "evening", "any"],
                    "description": "Patient's preferred time of day"
                },
                "appointment_type": {
                    "type": "string",
                    "enum": ["cleaning", "checkup", "procedure", "emergency", "consultation"],
                    "description": "Type of appointment (affects duration)"
                },
                "is_new_patient": {
                    "type": "boolean",
                    "description": "New patients need longer slots (60-90 min vs 30-45 min)"
                }
            },
            "required": ["date"]
        }
    },
    {
        "name": "lookup_patient",
        "description": "Look up an existing patient by name or phone to access their history",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "Patient's full name"
                },
                "phone_number": {
                    "type": "string",
                    "description": "Patient's phone number"
                },
                "date_of_birth": {
                    "type": "string",
                    "description": "Patient's date of birth for verification"
                }
            },
            "required": []
        }
    },
    {
        "name": "cancel_appointment",
        "description": "Cancel an existing appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "Patient's name"
                },
                "appointment_date": {
                    "type": "string",
                    "description": "Date of appointment to cancel"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for cancellation"
                },
                "reschedule": {
                    "type": "boolean",
                    "description": "Whether the patient wants to reschedule"
                }
            },
            "required": ["patient_name"]
        }
    },
    {
        "name": "transfer_to_human",
        "description": "Transfer the call to a human team member. Use when: patient explicitly asks, complex billing issues, complaints, or you cannot help.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for the transfer"
                },
                "department": {
                    "type": "string",
                    "enum": ["front_desk", "billing", "clinical", "manager"],
                    "description": "Which department to transfer to"
                },
                "priority": {
                    "type": "string",
                    "enum": ["normal", "high"],
                    "description": "Priority level of the transfer"
                }
            },
            "required": ["reason"]
        }
    },
    {
        "name": "take_message",
        "description": "Take a message when staff is unavailable or for non-urgent matters",
        "parameters": {
            "type": "object",
            "properties": {
                "caller_name": {
                    "type": "string",
                    "description": "Name of the caller"
                },
                "phone_number": {
                    "type": "string",
                    "description": "Callback phone number"
                },
                "message": {
                    "type": "string",
                    "description": "The message content"
                },
                "regarding": {
                    "type": "string",
                    "enum": ["appointment", "billing", "prescription", "results", "other"],
                    "description": "What the message is regarding"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Urgency level"
                },
                "best_callback_time": {
                    "type": "string",
                    "description": "Best time to call back"
                }
            },
            "required": ["caller_name", "message"]
        }
    },
    {
        "name": "verify_insurance",
        "description": "Record insurance information for verification",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "Patient's name"
                },
                "insurance_provider": {
                    "type": "string",
                    "description": "Name of insurance company"
                },
                "member_id": {
                    "type": "string",
                    "description": "Insurance member ID"
                },
                "group_number": {
                    "type": "string",
                    "description": "Group number if applicable"
                }
            },
            "required": ["patient_name", "insurance_provider"]
        }
    }
]


# -----------------------------------------------------------------------------
# Prompt Builder Class
# -----------------------------------------------------------------------------

class PromptBuilder:
    """Builds customized prompts for each clinic using research-based patterns."""
    
    def __init__(self, clinic: "Client"):
        """
        Initialize with a clinic/client record.
        
        Args:
            clinic: Client model from database
        """
        self.clinic = clinic
    
    def build_system_prompt(self, available_slots: Optional[str] = None) -> str:
        """
        Build the complete system prompt using research-based dental scripts.
        
        This uses the CARES framework and professional dental receptionist
        patterns from our research.
        
        Args:
            available_slots: Optional formatted string of available slots.
                           If None, uses default template.
        
        Returns:
            Formatted system prompt string
        """
        # Extract dentist names from clinic if available
        dentist_names = []
        if hasattr(self.clinic, 'dentist_names') and self.clinic.dentist_names:
            dentist_names = self.clinic.dentist_names
        elif hasattr(self.clinic, 'primary_dentist') and self.clinic.primary_dentist:
            dentist_names = [self.clinic.primary_dentist]
        else:
            dentist_names = ["our dentist"]
        
        # Use the research-based prompt builder
        prompt = build_dental_system_prompt(
            clinic_name=self.clinic.name,
            agent_name=self.clinic.agent_name or "Sarah",
            address=self.clinic.address or "",
            phone=self.clinic.phone_display or self.clinic.twilio_number or "",
            hours=self.clinic.hours or "Monday through Friday, 9 AM to 5 PM",
            services=self.clinic.services or "general dentistry, cleanings, and exams",
            insurance=self.clinic.insurance_accepted or "",
            dentist_names=dentist_names,
            custom_instructions=self.clinic.custom_instructions or "",
            available_slots=available_slots or DEFAULT_AVAILABLE_SLOTS,
        )
        
        return prompt
    
    def build_greeting(self) -> str:
        """
        Build the initial greeting message based on time of day.
        
        Uses appropriate morning/afternoon/evening greeting for natural
        conversational flow.
        """
        time_of_day = get_time_of_day()
        greeting_template = GREETINGS.get(time_of_day, GREETINGS["default"])
        
        return greeting_template.format(
            clinic_name=self.clinic.name,
            agent_name=self.clinic.agent_name or "Sarah",
        )
    
    def get_voice_id(self) -> str:
        """Get the Deepgram voice ID for this clinic."""
        voice = self.clinic.agent_voice
        if voice and voice in DEEPGRAM_VOICES:
            return voice
        return DEFAULT_VOICE
    
    def get_voice_info(self) -> dict:
        """Get information about the configured voice."""
        voice_id = self.get_voice_id()
        return DEEPGRAM_VOICES.get(voice_id, DEEPGRAM_VOICES[DEFAULT_VOICE])
    
    def get_function_schemas(self) -> list:
        """Get function calling schemas for this clinic."""
        # In production, you might customize these per clinic
        return FUNCTION_SCHEMAS
    
    def build_agent_config(self) -> dict:
        """
        Build complete configuration for Deepgram Voice Agent.
        
        Returns:
            Dict containing all agent configuration
        """
        return {
            "system_prompt": self.build_system_prompt(),
            "greeting_message": self.build_greeting(),
            "voice_id": self.get_voice_id(),
            "voice_info": self.get_voice_info(),
            "functions": self.get_function_schemas(),
            "clinic_id": self.clinic.id,
            "clinic_name": self.clinic.name,
        }


# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def build_prompt_for_clinic(clinic: "Client") -> str:
    """
    Convenience function to build a system prompt for a clinic.
    
    Args:
        clinic: Client model from database
        
    Returns:
        Formatted system prompt string
    """
    builder = PromptBuilder(clinic)
    return builder.build_system_prompt()


def get_available_voices() -> dict:
    """Get all available Deepgram voices."""
    return DEEPGRAM_VOICES.copy()


def format_available_slots(slots: list[dict]) -> str:
    """
    Format a list of available slots for the prompt.
    
    Args:
        slots: List of slot dicts with 'date', 'time', 'available' keys
        
    Returns:
        Formatted string for the prompt
    """
    if not slots:
        return DEFAULT_AVAILABLE_SLOTS
    
    lines = ["Available appointment slots (offer 2-3 specific options):"]
    for slot in slots:
        date_str = slot.get("date", "")
        time_str = slot.get("time", "")
        if slot.get("available", True):
            lines.append(f"- {date_str} at {time_str}")
    
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Demo / Testing
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Create a mock clinic for testing
    class MockClinic:
        id = 1
        name = "Sunshine Dental Care"
        agent_name = "Sarah"
        agent_voice = "aura-asteria-en"
        address = "123 Main Street, Suite 100, Jacksonville, FL 32256"
        phone_display = "(904) 555-1234"
        hours = "Monday-Friday 8am-5pm, Saturday 9am-1pm"
        services = "general dentistry, cleanings, fillings, crowns, whitening, implants"
        insurance_accepted = "Delta Dental, Cigna, Aetna, MetLife"
        twilio_number = "+19048679643"
        custom_instructions = "Our office is closed for lunch from 12pm-1pm. We also offer sedation dentistry for anxious patients."
        dentist_names = ["Dr. Smith", "Dr. Johnson"]
    
    clinic = MockClinic()
    builder = PromptBuilder(clinic)
    
    print("=" * 80)
    print("GENERATED SYSTEM PROMPT (Research-Based)")
    print("=" * 80)
    prompt = builder.build_system_prompt()
    print(prompt[:4000])  # Print first 4000 chars
    print(f"\n... (total length: {len(prompt)} characters)")
    print()
    print("=" * 80)
    print("TIME-BASED GREETING")
    print("=" * 80)
    print(f"Time of day: {get_time_of_day()}")
    print(f"Greeting: {builder.build_greeting()}")
    print()
    print("=" * 80)
    print("VOICE")
    print("=" * 80)
    print(f"Voice ID: {builder.get_voice_id()}")
    print(f"Voice Info: {builder.get_voice_info()}")
    print()
    print("=" * 80)
    print("FUNCTION SCHEMAS ({} functions)".format(len(builder.get_function_schemas())))
    print("=" * 80)
    for func in builder.get_function_schemas():
        print(f"- {func['name']}: {func['description'][:60]}...")
