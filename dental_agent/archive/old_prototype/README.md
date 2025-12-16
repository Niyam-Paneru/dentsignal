# Old Prototype Files - Archive Notice

This folder documents the original prototype files that were part of the initial 
`dental_agent/` structure before the production system was built.

## Archived Files (Previously Deleted)

The following files were part of an early prototype and have been superseded by 
the new production-ready system:

### `api_integration.py` (RETIRED)
- **Status**: Superseded by `agent_server.py` and `api_main.py`
- **Original Purpose**: Stub for Deepgram/Twilio integration
- **Issues**: Only contained `...` placeholders, no real implementation

### `call_flow.py` (RETIRED)  
- **Status**: Superseded by `agent_server.py`
- **Original Purpose**: FSM-based call flow
- **Issues**: CSV-based logging, synchronous blocking, incomplete

### `main.py` (RETIRED)
- **Status**: Superseded by `api_main.py`
- **Original Purpose**: CLI entry point
- **Issues**: No FastAPI endpoints, CLI-only

### `utils.py` (RETIRED → RECREATED)
- **Status**: Completely rewritten as new `utils.py`
- **Original Purpose**: Logging and CSV helpers
- **Issues**: No log rotation, PII in plaintext, no phone validation

## New Production System

The production system now consists of:

| New File | Purpose |
|----------|---------|
| `api_main.py` | FastAPI backend with JWT auth, all REST endpoints |
| `agent_server.py` | FSM-based agent worker with SIMULATED/REAL modes |
| `db.py` | SQLModel ORM with all database models |
| `telephony.py` | Telephony abstraction (SIMULATED/TWILIO) |
| `utils.py` | Phone validation (E.164), PII masking, log rotation |

## Why Files Were Retired

1. **No FastAPI endpoints** - Original had CLI only
2. **No database** - Used CSV files for persistence  
3. **No phone validation** - Accepted any format
4. **PII in logs** - Phone numbers logged in plaintext
5. **No log rotation** - Could fill disk
6. **Stub implementations** - `...` placeholders throughout

## Restoration

If you need to restore the original files for reference, check git history:
```bash
git log --all --full-history -- api_integration.py call_flow.py main.py utils.py
```
