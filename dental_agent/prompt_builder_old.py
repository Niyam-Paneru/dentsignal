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
# Prompt Templates
# -----------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are {agent_name}, a friendly and professional AI receptionist for {clinic_name}.

## Your Role
You answer incoming calls from patients and help them with:
- Scheduling appointments
- Answering questions about services, hours, and location
- Taking messages for the dental team
- Handling appointment cancellations and reschedules

## Clinic Information
- **Name**: {clinic_name}
- **Address**: {address}
- **Phone**: {phone_display}
- **Hours**: {hours}
- **Services**: {services}
{insurance_info}

## Your Personality
- Warm, friendly, and professional
- Patient and understanding
- Clear and concise in your responses
- Helpful without being pushy

## Conversation Guidelines

### Opening
When the call connects, greet the caller warmly:
"Hello! Thank you for calling {clinic_name}, this is {agent_name}. How may I help you today?"

### Scheduling Appointments
1. Ask if they are a new or existing patient
2. Ask about the reason for their visit (cleaning, checkup, pain, etc.)
3. Ask about their preferred days/times
4. Offer available appointment slots
5. Confirm the appointment details
6. Collect/confirm their contact information

### Handling Questions
- Answer questions about services, hours, and location clearly
- If you don't know something specific, offer to have a team member call them back
- Never make up information about pricing or specific treatments

### Ending the Call
- Summarize what was accomplished
- Confirm any appointments made
- Thank them for calling
- Say goodbye warmly

## Available Appointment Slots
{available_slots}

## Important Rules
1. NEVER provide specific pricing - say "Our team will discuss costs during your visit"
2. NEVER diagnose or give medical advice - say "I'd recommend scheduling with Dr. [dentist] to take a look"
3. If someone is in severe pain, express concern and try to find the earliest available slot
4. If asked about emergencies, say "For dental emergencies, we do our best to see you same-day. Let me check our availability."
5. Be understanding if someone needs to reschedule or cancel
6. If the caller seems confused or frustrated, offer to transfer to a human team member

{custom_instructions}

## Response Style
- Keep responses conversational and natural
- Use the caller's name once you know it
- Don't be robotic - vary your phrasing
- It's okay to use filler words like "let me check" or "one moment" to sound natural
- If you need to look something up, say so naturally
"""

GREETING_TEMPLATE = "Hello! Thank you for calling {clinic_name}, this is {agent_name}. How may I help you today?"

# Available slots template (in production, fetch from scheduling system)
DEFAULT_AVAILABLE_SLOTS = """For scheduling purposes, assume availability as follows:
- Today: Limited availability, offer afternoon if urgent
- Tomorrow: 9:00 AM, 10:30 AM, 2:00 PM, 3:30 PM
- Day after tomorrow: 9:00 AM, 11:00 AM, 1:00 PM, 4:00 PM
- Later this week: Generally flexible, ask for preference

Note: In production, these would be fetched from the clinic's scheduling system."""


# -----------------------------------------------------------------------------
# Function Calling Schemas (for Deepgram Voice Agent)
# -----------------------------------------------------------------------------

FUNCTION_SCHEMAS = [
    {
        "name": "book_appointment",
        "description": "Book an appointment for a patient",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "Full name of the patient"
                },
                "phone_number": {
                    "type": "string", 
                    "description": "Patient's phone number"
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
                    "description": "Reason for the appointment (cleaning, checkup, pain, etc.)"
                },
                "is_new_patient": {
                    "type": "boolean",
                    "description": "Whether this is a new patient"
                }
            },
            "required": ["patient_name", "date", "time", "reason"]
        }
    },
    {
        "name": "check_availability",
        "description": "Check available appointment slots for a given date",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to check in YYYY-MM-DD format"
                },
                "time_preference": {
                    "type": "string",
                    "enum": ["morning", "afternoon", "any"],
                    "description": "Preferred time of day"
                }
            },
            "required": ["date"]
        }
    },
    {
        "name": "transfer_to_human",
        "description": "Transfer the call to a human team member",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for the transfer"
                }
            },
            "required": ["reason"]
        }
    },
    {
        "name": "take_message",
        "description": "Take a message for the dental team",
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
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Urgency level of the message"
                }
            },
            "required": ["caller_name", "message"]
        }
    }
]


# -----------------------------------------------------------------------------
# Prompt Builder Class
# -----------------------------------------------------------------------------

class PromptBuilder:
    """Builds customized prompts for each clinic."""
    
    def __init__(self, clinic: "Client"):
        """
        Initialize with a clinic/client record.
        
        Args:
            clinic: Client model from database
        """
        self.clinic = clinic
    
    def build_system_prompt(self, available_slots: Optional[str] = None) -> str:
        """
        Build the complete system prompt for Deepgram Voice Agent.
        
        Args:
            available_slots: Optional formatted string of available slots.
                           If None, uses default template.
        
        Returns:
            Formatted system prompt string
        """
        # Format insurance info if available
        insurance_info = ""
        if self.clinic.insurance_accepted:
            insurance_info = f"- **Insurance Accepted**: {self.clinic.insurance_accepted}"
        
        # Format custom instructions if available
        custom_instructions = ""
        if self.clinic.custom_instructions:
            custom_instructions = f"\n## Additional Instructions\n{self.clinic.custom_instructions}"
        
        # Build the prompt
        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            agent_name=self.clinic.agent_name or "Sarah",
            clinic_name=self.clinic.name,
            address=self.clinic.address or "Please ask our team for directions",
            phone_display=self.clinic.phone_display or self.clinic.twilio_number or "our main line",
            hours=self.clinic.hours or "Monday through Friday, 9 AM to 5 PM",
            services=self.clinic.services or "general dentistry, cleanings, and exams",
            insurance_info=insurance_info,
            available_slots=available_slots or DEFAULT_AVAILABLE_SLOTS,
            custom_instructions=custom_instructions,
        )
        
        return prompt
    
    def build_greeting(self) -> str:
        """Build the initial greeting message."""
        return GREETING_TEMPLATE.format(
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
    
    lines = ["Available appointment slots:"]
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
        name = "Sunshine Dental"
        agent_name = "Sarah"
        agent_voice = "aura-asteria-en"
        address = "123 Main Street, Suite 100, Jacksonville, FL 32256"
        phone_display = "(904) 555-1234"
        hours = "Monday-Friday 8am-5pm, Saturday 9am-1pm"
        services = "general dentistry, cleanings, fillings, crowns, whitening"
        insurance_accepted = "Delta Dental, Cigna, Aetna, MetLife"
        twilio_number = "+19048679643"
        custom_instructions = "Our office is closed for lunch from 12pm-1pm."
    
    clinic = MockClinic()
    builder = PromptBuilder(clinic)
    
    print("=" * 80)
    print("SYSTEM PROMPT")
    print("=" * 80)
    print(builder.build_system_prompt())
    print()
    print("=" * 80)
    print("GREETING")
    print("=" * 80)
    print(builder.build_greeting())
    print()
    print("=" * 80)
    print("VOICE")
    print("=" * 80)
    print(f"Voice ID: {builder.get_voice_id()}")
    print(f"Voice Info: {builder.get_voice_info()}")
    print()
    print("=" * 80)
    print("FUNCTION SCHEMAS")
    print("=" * 80)
    print(json.dumps(builder.get_function_schemas(), indent=2))
