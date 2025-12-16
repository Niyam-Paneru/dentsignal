"""
test_call_flow.py - Unit Tests for Call Flow FSM

Tests the FSM logic used in agent_server simulated conversation.
Uses deterministic inputs to verify state transitions and transcript format.
"""

import pytest
from datetime import datetime, timedelta

# Import FSM components
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_server import (
    CallState,
    CallResult,
    ConversationContext,
    ConversationFSM,
    run_simulated_conversation,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def fsm():
    """Create a ConversationFSM instance."""
    return ConversationFSM()


@pytest.fixture
def context():
    """Create a basic ConversationContext."""
    return ConversationContext(
        call_id=1,
        lead_name="John Doe",
        lead_phone="+15551234567",
    )


# -----------------------------------------------------------------------------
# State Transition Tests
# -----------------------------------------------------------------------------

class TestStateTransitions:
    """Test FSM state transitions."""
    
    def test_initial_state_is_greeting(self, context):
        """Context should start in GREETING state."""
        assert context.state == CallState.GREETING
    
    def test_greeting_to_qualify_on_confirmation(self, fsm, context):
        """Saying 'yes' in greeting should transition to QUALIFY."""
        fsm.transition(context, "Yes, this is John")
        assert context.state == CallState.QUALIFY
    
    def test_greeting_to_end_on_wrong_person(self, fsm, context):
        """Saying 'no' in greeting should transition to END."""
        fsm.transition(context, "No, wrong number")
        assert context.state == CallState.END
        assert context.result == CallResult.FAILED
    
    def test_qualify_to_offer_slot(self, fsm, context):
        """Answering qualifying question should transition to OFFER_SLOT."""
        # First get to QUALIFY state
        fsm.transition(context, "Yes, speaking")
        assert context.state == CallState.QUALIFY
        
        # Answer qualifying question
        fsm.transition(context, "I'm a returning patient")
        assert context.state == CallState.OFFER_SLOT
    
    def test_offer_slot_to_confirm_on_acceptance(self, fsm, context):
        """Accepting offered slot should transition to CONFIRM."""
        fsm.transition(context, "Yes, this is John")
        fsm.transition(context, "Returning patient, mornings work")
        fsm.transition(context, "Yes, that works perfectly")
        assert context.state == CallState.CONFIRM
        assert context.booked_slot is not None
    
    def test_offer_slot_to_end_on_reschedule(self, fsm, context):
        """Declining slot should transition to END with RESCHEDULE result."""
        fsm.transition(context, "Yes, speaking")
        fsm.transition(context, "New patient")
        fsm.transition(context, "No, I can't do that time")
        assert context.state == CallState.END
        assert context.result == CallResult.RESCHEDULE
    
    def test_confirm_to_end(self, fsm, context):
        """Confirmation should transition to END with BOOKED result."""
        fsm.transition(context, "Yes")
        fsm.transition(context, "Returning patient")
        fsm.transition(context, "Yes, book it")
        fsm.transition(context, "No, that's all")
        assert context.state == CallState.END
        assert context.result == CallResult.BOOKED


# -----------------------------------------------------------------------------
# Fallback Tests
# -----------------------------------------------------------------------------

class TestFallbacks:
    """Test fallback/retry behavior."""
    
    def test_no_response_increments_retry(self, fsm, context):
        """Empty input should increment retry count."""
        assert context.retry_count == 0
        fsm.transition(context, "")
        assert context.retry_count == 1
    
    def test_silence_increments_retry(self, fsm, context):
        """Silence marker should increment retry count."""
        fsm.transition(context, "[silence]")
        assert context.retry_count == 1
    
    def test_max_retries_ends_call(self, fsm, context):
        """Exceeding max retries should end call with NO_ANSWER."""
        context.max_retries = 2
        
        fsm.transition(context, "")  # retry 1
        assert context.state == CallState.GREETING
        
        fsm.transition(context, "")  # retry 2, should end
        assert context.state == CallState.END
        assert context.result == CallResult.NO_ANSWER
    
    def test_valid_input_resets_retry(self, fsm, context):
        """Valid input should reset retry count."""
        fsm.transition(context, "")  # increment retry
        assert context.retry_count == 1
        
        fsm.transition(context, "Yes, speaking")  # valid input
        assert context.retry_count == 0


# -----------------------------------------------------------------------------
# Context Data Tests
# -----------------------------------------------------------------------------

class TestContextData:
    """Test context data collection."""
    
    def test_patient_type_new(self, fsm, context):
        """Should detect new patient."""
        fsm.transition(context, "Yes")
        fsm.transition(context, "I'm a new patient")
        assert context.patient_type == "new"
    
    def test_patient_type_returning(self, fsm, context):
        """Should detect returning patient."""
        fsm.transition(context, "Yes")
        fsm.transition(context, "I'm a returning patient")
        assert context.patient_type == "returning"
    
    def test_urgent_pain_detection(self, fsm, context):
        """Should detect urgent pain mention."""
        fsm.transition(context, "Yes")
        fsm.transition(context, "I have some tooth pain")
        assert context.has_pain is True
    
    def test_booked_slot_set(self, fsm, context):
        """Booking should set booked_slot datetime."""
        fsm.transition(context, "Yes")
        fsm.transition(context, "Returning patient")
        fsm.transition(context, "Yes, that works")
        
        assert context.booked_slot is not None
        assert isinstance(context.booked_slot, datetime)


# -----------------------------------------------------------------------------
# Transcript Tests
# -----------------------------------------------------------------------------

class TestTranscript:
    """Test transcript generation."""
    
    def test_transcript_records_exchanges(self, fsm, context):
        """Transcript should record agent and patient lines."""
        fsm.transition(context, "Yes, speaking")
        
        assert len(context.transcript) >= 2
        assert any("Patient:" in line for line in context.transcript)
        assert any("Agent:" in line for line in context.transcript)
    
    def test_transcript_order(self, fsm, context):
        """Transcript should maintain chronological order."""
        fsm.transition(context, "Yes")
        fsm.transition(context, "New patient")
        
        # Find indices of patient and agent lines
        patient_indices = [i for i, line in enumerate(context.transcript) if "Patient:" in line]
        agent_indices = [i for i, line in enumerate(context.transcript) if "Agent:" in line]
        
        # Agent responses should follow patient inputs
        for pi in patient_indices:
            next_agent = min([ai for ai in agent_indices if ai > pi], default=None)
            assert next_agent is not None or pi == max(patient_indices)


# -----------------------------------------------------------------------------
# Simulated Conversation Tests
# -----------------------------------------------------------------------------

class TestSimulatedConversation:
    """Test full simulated conversation runs."""
    
    def test_deterministic_with_seed(self, fsm):
        """Same seed should produce same result."""
        context1 = ConversationContext(call_id=1, lead_name="Test", lead_phone="+15551234567")
        context2 = ConversationContext(call_id=1, lead_name="Test", lead_phone="+15551234567")
        
        result1, transcript1, slot1 = run_simulated_conversation(context1, fsm, seed=42)
        result2, transcript2, slot2 = run_simulated_conversation(context2, fsm, seed=42)
        
        assert result1 == result2
        assert transcript1 == transcript2
    
    def test_different_seeds_may_differ(self, fsm):
        """Different seeds may produce different results."""
        results = set()
        for seed in range(10):
            context = ConversationContext(call_id=seed, lead_name="Test", lead_phone="+15551234567")
            result, _, _ = run_simulated_conversation(context, fsm, seed=seed)
            results.add(result)
        
        # With enough seeds, we should see variation (though not guaranteed)
        # Just check we get valid results
        for result in results:
            assert result in CallResult
    
    def test_conversation_completes(self, fsm):
        """Simulated conversation should reach END state."""
        context = ConversationContext(call_id=123, lead_name="Jane Doe", lead_phone="+15559876543")
        result, transcript, slot = run_simulated_conversation(context, fsm, seed=100)
        
        assert context.state == CallState.END
        assert result in CallResult
        assert isinstance(transcript, str)
        assert len(transcript) > 0
    
    def test_booked_result_has_slot(self, fsm):
        """BOOKED result should have a booked_slot."""
        # Find a seed that produces BOOKED
        for seed in range(100):
            context = ConversationContext(call_id=seed, lead_name="Test", lead_phone="+15551234567")
            result, _, slot = run_simulated_conversation(context, fsm, seed=seed)
            if result == CallResult.BOOKED:
                assert slot is not None
                assert isinstance(slot, datetime)
                break


# -----------------------------------------------------------------------------
# FSM Config Tests
# -----------------------------------------------------------------------------

class TestFSMConfig:
    """Test FSM configuration loading."""
    
    def test_default_config_loads(self):
        """FSM should load with default config."""
        fsm = ConversationFSM()
        assert fsm.config is not None
        assert "greeting" in fsm.config
    
    def test_custom_config_path(self, tmp_path):
        """FSM should load custom config from path."""
        config = {
            "greeting": ["Custom greeting for {name}"],
            "qualifying_questions": ["Custom question?"]
        }
        
        config_file = tmp_path / "custom_config.json"
        import json
        config_file.write_text(json.dumps(config))
        
        fsm = ConversationFSM(str(config_file))
        assert "Custom greeting" in fsm.config["greeting"][0]
    
    def test_missing_config_uses_defaults(self):
        """Missing config file should use defaults."""
        fsm = ConversationFSM("/nonexistent/path.json")
        assert fsm.config is not None
        assert "greeting" in fsm.config


# -----------------------------------------------------------------------------
# Run Tests
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
