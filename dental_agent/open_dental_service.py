"""
open_dental_service.py - Open Dental PMS Integration Service

Provides integration with Open Dental's REST API for:
- Patient lookup and creation
- Real-time appointment slot availability
- Appointment booking, updating, and cancellation
- Provider and operatory information
- Appointment confirmation status updates

Open Dental API Documentation: https://www.opendental.com/site/apispecification.html

Authentication:
    Authorization: ODFHIR {DeveloperKey}/{CustomerKey}

API Modes:
    - Remote: https://api.opendental.com/api/v1/ (cloud, any internet)
    - Service: http://{IP}:30223/api/v1/ (on-premise server)  # DevSkim: ignore DS137138
    - Local: http://localhost:30222/api/v1/ (workstation only)  # DevSkim: ignore DS137138

Pricing (per location/month):
    - Free: Read-only (1 req/5s throttle)
    - $15: + Comm, Documents, Queries
    - $30: + Appointments, Patients, most write ops
    - $35: + Payments, PayPlans
"""

import logging
import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration & Data Classes
# =============================================================================

class OpenDentalApiMode(str, Enum):
    """API connection modes for Open Dental."""
    REMOTE = "remote"    # Cloud-hosted at api.opendental.com
    SERVICE = "service"  # On-premise API service (port 30223)
    LOCAL = "local"      # Local workstation (port 30222)


@dataclass
class OpenDentalConfig:
    """Configuration for connecting to an Open Dental instance."""
    developer_key: str           # Unique to DentSignal (from developer portal)
    customer_key: str            # Unique per clinic (generated in portal)
    api_mode: OpenDentalApiMode = OpenDentalApiMode.REMOTE
    base_url: Optional[str] = None  # Override URL for Service/Local mode
    clinic_num: Optional[int] = None  # ClinicNum if multi-location practice
    
    @property
    def endpoint(self) -> str:
        """Get the API base URL based on mode."""
        if self.base_url:
            return self.base_url.rstrip("/")
        if self.api_mode == OpenDentalApiMode.REMOTE:
            return "https://api.opendental.com/api/v1"
        elif self.api_mode == OpenDentalApiMode.SERVICE:
            return "http://localhost:30223/api/v1"  # DevSkim: ignore DS137138 - Open Dental on-premise API requires HTTP
        else:  # LOCAL
            return "http://localhost:30222/api/v1"  # DevSkim: ignore DS137138 - Open Dental local workstation API
    
    @property
    def auth_header(self) -> str:
        """Build the Authorization header value."""
        return f"ODFHIR {self.developer_key}/{self.customer_key}"


@dataclass
class ODPatient:
    """Open Dental patient record."""
    pat_num: int
    first_name: str
    last_name: str
    birthdate: Optional[str] = None
    phone_home: Optional[str] = None
    phone_wireless: Optional[str] = None
    phone_work: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    is_new_patient: bool = False
    preferred_name: Optional[str] = None
    pat_status: str = "Patient"
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "ODPatient":
        """Create from Open Dental API response."""
        return cls(
            pat_num=data.get("PatNum", 0),
            first_name=data.get("FName", ""),
            last_name=data.get("LName", ""),
            birthdate=data.get("Birthdate"),
            phone_home=data.get("HmPhone", ""),
            phone_wireless=data.get("WirelessPhone", ""),
            phone_work=data.get("WkPhone", ""),
            email=data.get("Email", ""),
            address=data.get("Address", ""),
            city=data.get("City", ""),
            state=data.get("State", ""),
            zip_code=data.get("Zip", ""),
            preferred_name=data.get("Preferred", ""),
            pat_status=data.get("PatStatus", "Patient"),
        )
    
    @property
    def display_name(self) -> str:
        name = f"{self.first_name} {self.last_name}"
        if self.preferred_name:
            name = f"{self.preferred_name} ({name})"
        return name


@dataclass
class ODTimeSlot:
    """Open Dental available time slot."""
    start: datetime
    end: datetime
    provider_num: int
    operatory_num: int
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "ODTimeSlot":
        return cls(
            start=datetime.strptime(data["DateTimeStart"], "%Y-%m-%d %H:%M:%S"),
            end=datetime.strptime(data["DateTimeEnd"], "%Y-%m-%d %H:%M:%S"),
            provider_num=data.get("ProvNum", 0),
            operatory_num=data.get("OpNum", 0),
        )
    
    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "provider_num": self.provider_num,
            "operatory_num": self.operatory_num,
            "duration_minutes": self.duration_minutes,
        }


@dataclass
class ODAppointment:
    """Open Dental appointment record."""
    apt_num: int
    pat_num: int
    status: str  # Scheduled, Complete, Broken, etc.
    apt_datetime: datetime
    provider_num: int
    provider_abbr: str
    operatory_num: int
    is_new_patient: bool
    proc_description: str
    note: str
    confirmed: str
    pattern: str  # Time pattern in 5-min increments (X = provider time, / = other)
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "ODAppointment":
        apt_dt = data.get("AptDateTime", "0001-01-01 00:00:00")
        try:
            parsed_dt = datetime.strptime(apt_dt, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            parsed_dt = datetime.min
        
        return cls(
            apt_num=data.get("AptNum", 0),
            pat_num=data.get("PatNum", 0),
            status=data.get("AptStatus", ""),
            apt_datetime=parsed_dt,
            provider_num=data.get("ProvNum", 0),
            provider_abbr=data.get("provAbbr", ""),
            operatory_num=data.get("Op", 0),
            is_new_patient=data.get("IsNewPatient", "false") == "true",
            proc_description=data.get("ProcDescript", ""),
            note=data.get("Note", ""),
            confirmed=data.get("confirmed", "Not Called"),
            pattern=data.get("Pattern", "/XX/"),
        )
    
    @property
    def duration_minutes(self) -> int:
        """Calculate duration from pattern (each char = 5 minutes)."""
        return len(self.pattern) * 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "apt_num": self.apt_num,
            "pat_num": self.pat_num,
            "status": self.status,
            "datetime": self.apt_datetime.isoformat(),
            "provider": self.provider_abbr,
            "duration_minutes": self.duration_minutes,
            "procedures": self.proc_description,
            "note": self.note,
            "confirmed": self.confirmed,
            "is_new_patient": self.is_new_patient,
        }


@dataclass
class ODProvider:
    """Open Dental provider (dentist/hygienist)."""
    prov_num: int
    abbr: str
    first_name: str
    last_name: str
    is_secondary: bool  # True = hygienist
    specialty: str
    is_hidden: bool
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "ODProvider":
        return cls(
            prov_num=data.get("ProvNum", 0),
            abbr=data.get("Abbr", ""),
            first_name=data.get("FName", ""),
            last_name=data.get("LName", ""),
            is_secondary=data.get("IsSecondary", "false") == "true",
            specialty=str(data.get("Specialty", "")),
            is_hidden=data.get("IsHidden", "false") == "true",
        )
    
    @property
    def display_name(self) -> str:
        prefix = "Dr." if not self.is_secondary else ""
        return f"{prefix} {self.first_name} {self.last_name}".strip()


@dataclass
class ODOperatory:
    """Open Dental operatory (treatment room/chair)."""
    op_num: int
    name: str
    abbrev: str
    provider_dentist: int
    provider_hygienist: int
    is_hygiene: bool
    is_hidden: bool
    clinic_num: int
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "ODOperatory":
        return cls(
            op_num=data.get("OperatoryNum", 0),
            name=data.get("OpName", ""),
            abbrev=data.get("Abbrev", ""),
            provider_dentist=data.get("ProvDentist", 0),
            provider_hygienist=data.get("ProvHygienist", 0),
            is_hygiene=data.get("IsHygiene", "false") == "true",
            is_hidden=data.get("IsHidden", "false") == "true",
            clinic_num=data.get("ClinicNum", 0),
        )


# =============================================================================
# Main Service Class
# =============================================================================

class OpenDentalService:
    """
    Open Dental PMS integration service.
    
    Provides methods matching DentSignal's voice agent function calling:
    - check_availability → GET /appointments/Slots
    - book_appointment → POST /appointments
    - cancel_appointment → PUT /appointments/{id}/Break
    - lookup_patient → GET /patients?LName=...&FName=...
    - create_patient → POST /patients
    
    Usage:
        config = OpenDentalConfig(
            developer_key="NFF6i0KrXrxDkZHt",
            customer_key="VzkmZEaUWOjnQX2z",
        )
        service = OpenDentalService(config)
        
        # Check slots
        slots = await service.get_available_slots(date.today())
        
        # Book appointment
        apt = await service.create_appointment(
            pat_num=48, op_num=1, 
            apt_datetime=datetime(2025, 2, 15, 9, 0)
        )
    """
    
    # Throttle limits from Open Dental
    THROTTLE_FREE = 5.0     # 1 request per 5 seconds (Read-only)
    THROTTLE_PAID = 1.0     # 1 request per 1 second (Paid tiers)
    THROTTLE_ENTERPRISE = 0.5  # Enterprise tier
    
    def __init__(self, config: OpenDentalConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        
        # Cache providers and operatories (they rarely change)
        self._providers_cache: Optional[List[ODProvider]] = None
        self._operatories_cache: Optional[List[ODOperatory]] = None
        self._cache_expiry: Optional[datetime] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.endpoint,
                headers={
                    "Authorization": self.config.auth_header,
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def _request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> httpx.Response:
        """Make an authenticated request to Open Dental API."""
        client = await self._get_client()
        
        try:
            response = await client.request(
                method=method,
                url=path,
                params=params,
                json=json_data,
            )
            
            if response.status_code >= 400:
                error_text = response.text
                logger.error(
                    f"Open Dental API error: {method} {path} → "
                    f"{response.status_code}: {error_text}"
                )
            
            return response
            
        except httpx.TimeoutException:
            logger.error(f"Open Dental API timeout: {method} {path}")
            raise
        except httpx.ConnectError as e:
            logger.error(f"Open Dental connection error: {e}")
            raise

    # -------------------------------------------------------------------------
    # Connection Test
    # -------------------------------------------------------------------------
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the API connection and credentials.
        Uses read-only endpoint (free tier).
        
        Returns:
            Dict with "success", "message", and optional "data"
        """
        try:
            response = await self._request("GET", "/providers")
            
            if response.status_code == 200:
                providers = response.json()
                count = len(providers) if isinstance(providers, list) else 0
                return {
                    "success": True,
                    "message": f"Connected! Found {count} providers.",
                    "provider_count": count,
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "Invalid API keys. Check Developer Key and Customer Key.",
                }
            else:
                return {
                    "success": False,
                    "message": f"API error: {response.status_code}",
                }
        except httpx.ConnectError:
            return {
                "success": False,
                "message": f"Cannot connect to {self.config.endpoint}. Check API mode and network.",
            }
        except Exception as e:
            logger.error(f"Open Dental connection test failed: {e}")
            return {
                "success": False,
                "message": "Connection test failed. Please check credentials and network.",
            }

    # -------------------------------------------------------------------------
    # Providers
    # -------------------------------------------------------------------------
    
    async def get_providers(self, force_refresh: bool = False) -> List[ODProvider]:
        """
        Get all active providers (dentists & hygienists).
        Results are cached for 1 hour.
        """
        now = datetime.utcnow()
        if (
            not force_refresh 
            and self._providers_cache is not None 
            and self._cache_expiry 
            and now < self._cache_expiry
        ):
            return self._providers_cache
        
        params = {}
        if self.config.clinic_num is not None:
            params["ClinicNum"] = self.config.clinic_num
        
        response = await self._request("GET", "/providers", params=params or None)
        
        if response.status_code != 200:
            logger.error(f"Failed to get providers: {response.text}")
            return self._providers_cache or []
        
        all_providers = [ODProvider.from_api(p) for p in response.json()]
        # Filter out hidden providers
        active = [p for p in all_providers if not p.is_hidden]
        
        self._providers_cache = active
        self._cache_expiry = now + timedelta(hours=1)
        
        return active

    # -------------------------------------------------------------------------
    # Operatories
    # -------------------------------------------------------------------------
    
    async def get_operatories(self, force_refresh: bool = False) -> List[ODOperatory]:
        """
        Get all operatories (treatment rooms).
        Results are cached for 1 hour.
        """
        now = datetime.utcnow()
        if (
            not force_refresh 
            and self._operatories_cache is not None
            and self._cache_expiry
            and now < self._cache_expiry
        ):
            return self._operatories_cache
        
        params = {}
        if self.config.clinic_num is not None:
            params["ClinicNum"] = self.config.clinic_num
        
        response = await self._request("GET", "/operatories", params=params or None)
        
        if response.status_code != 200:
            logger.error(f"Failed to get operatories: {response.text}")
            return self._operatories_cache or []
        
        all_ops = [ODOperatory.from_api(o) for o in response.json()]
        active = [o for o in all_ops if not o.is_hidden]
        
        self._operatories_cache = active
        self._cache_expiry = now + timedelta(hours=1)
        
        return active

    # -------------------------------------------------------------------------
    # Patients
    # -------------------------------------------------------------------------
    
    async def search_patients(
        self,
        last_name: Optional[str] = None,
        first_name: Optional[str] = None,
        phone: Optional[str] = None,
        birthdate: Optional[str] = None,  # yyyy-MM-dd
        email: Optional[str] = None,
    ) -> List[ODPatient]:
        """
        Search for patients by name, phone, birthdate, or email.
        Supports partial matching (case-insensitive).
        
        Maps to: GET /patients?LName=...&FName=...
        """
        params: Dict[str, str] = {}
        if last_name:
            params["LName"] = last_name
        if first_name:
            params["FName"] = first_name
        if phone:
            params["Phone"] = phone
        if birthdate:
            params["Birthdate"] = birthdate
        if email:
            params["Email"] = email
        
        if not params:
            logger.warning("search_patients called with no search criteria")
            return []
        
        # Use hideInactive to filter out old patients
        params["hideInactive"] = "true"
        
        response = await self._request("GET", "/patients", params=params)
        
        if response.status_code != 200:
            logger.error(f"Patient search failed: {response.text}")
            return []
        
        data = response.json()
        if not isinstance(data, list):
            return []
        
        return [ODPatient.from_api(p) for p in data]
    
    async def get_patient(self, pat_num: int) -> Optional[ODPatient]:
        """Get a single patient by PatNum."""
        response = await self._request("GET", f"/patients/{pat_num}")
        
        if response.status_code != 200:
            return None
        
        return ODPatient.from_api(response.json())
    
    async def create_patient(
        self,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        birthdate: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        is_new_patient: bool = True,
    ) -> Optional[ODPatient]:
        """
        Create a new patient in Open Dental.
        
        Requires Patients permission ($30/month tier).
        Open Dental checks for duplicates (LName, FName, Birthdate, Email/Phone).
        
        Maps to: POST /patients
        """
        payload: Dict[str, Any] = {
            "FName": first_name,
            "LName": last_name,
        }
        
        if phone:
            # Store in WirelessPhone (most common for new patients calling in)
            payload["WirelessPhone"] = phone
            payload["TxtMsgOk"] = "Yes"
        if email:
            payload["Email"] = email
        if birthdate:
            payload["Birthdate"] = birthdate
        if address:
            payload["Address"] = address
        if city:
            payload["City"] = city
        if state:
            payload["State"] = state
        if zip_code:
            payload["Zip"] = zip_code
        
        # Set preferred contact to wireless phone (they just called us)
        payload["PreferContactMethod"] = "WirelessPh"
        payload["PreferConfirmMethod"] = "TextMessage"
        
        if self.config.clinic_num:
            payload["ClinicNum"] = self.config.clinic_num
        
        response = await self._request("POST", "/patients", json_data=payload)
        
        if response.status_code == 201:
            patient = ODPatient.from_api(response.json())
            patient.is_new_patient = True
            logger.info(f"Created Open Dental patient: {patient.pat_num} - {patient.display_name}")
            return patient
        
        logger.error(f"Failed to create patient: {response.status_code} - {response.text}")
        return None

    # -------------------------------------------------------------------------
    # Availability (Slots)
    # -------------------------------------------------------------------------
    
    async def get_available_slots(
        self,
        target_date: Optional[date] = None,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        provider_num: Optional[int] = None,
        operatory_num: Optional[int] = None,
        length_minutes: Optional[int] = None,
    ) -> List[ODTimeSlot]:
        """
        Get available appointment slots from Open Dental.
        
        This is a READ-ONLY operation (free tier).
        
        Maps to: GET /appointments/Slots
        
        Args:
            target_date: Single day to check (default: next 14 days)
            date_start/date_end: Date range (inclusive)
            provider_num: Specific provider to check
            operatory_num: Specific operatory/room
            length_minutes: Minimum slot duration
        """
        params: Dict[str, Any] = {}
        
        if target_date:
            params["date"] = target_date.strftime("%Y-%m-%d")
        elif date_start and date_end:
            params["dateStart"] = date_start.strftime("%Y-%m-%d")
            params["dateEnd"] = date_end.strftime("%Y-%m-%d")
        
        if provider_num:
            params["ProvNum"] = provider_num
        if operatory_num:
            params["OpNum"] = operatory_num
        if length_minutes:
            params["lengthMinutes"] = length_minutes
        
        response = await self._request("GET", "/appointments/Slots", params=params or None)
        
        if response.status_code != 200:
            logger.error(f"Failed to get slots: {response.text}")
            return []
        
        data = response.json()
        if not isinstance(data, list):
            return []
        
        return [ODTimeSlot.from_api(s) for s in data]
    
    async def get_available_slots_formatted(
        self,
        target_date: Optional[date] = None,
        days_ahead: int = 7,
        length_minutes: int = 30,
    ) -> str:
        """
        Get available slots formatted for the AI voice agent prompt.
        
        Returns human-readable string of available times for the AI to offer.
        """
        if target_date is None:
            target_date = date.today()
        
        date_end = target_date + timedelta(days=days_ahead)
        
        slots = await self.get_available_slots(
            date_start=target_date,
            date_end=date_end,
            length_minutes=length_minutes,
        )
        
        if not slots:
            return "No available slots found for the requested period. Please check with the office."
        
        # Get provider names for context
        providers = await self.get_providers()
        prov_map = {p.prov_num: p.display_name for p in providers}
        
        # Group slots by date
        slots_by_date: Dict[str, List[ODTimeSlot]] = {}
        for slot in slots:
            day_key = slot.start.strftime("%A, %B %d")
            if day_key not in slots_by_date:
                slots_by_date[day_key] = []
            slots_by_date[day_key].append(slot)
        
        lines = ["Available appointment slots (from Open Dental PMS):"]
        for day, day_slots in list(slots_by_date.items())[:5]:  # Limit to 5 days
            times = []
            for s in day_slots[:6]:  # Limit to 6 slots per day
                time_str = s.start.strftime("%I:%M %p").lstrip("0")
                prov = prov_map.get(s.provider_num, "")
                if prov:
                    times.append(f"{time_str} (with {prov})")
                else:
                    times.append(time_str)
            lines.append(f"- {day}: {', '.join(times)}")
        
        lines.append("\nOffer 2-3 specific options from above. Never ask 'when would you like to come in?'")
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Appointments
    # -------------------------------------------------------------------------
    
    async def get_appointments(
        self,
        pat_num: Optional[int] = None,
        target_date: Optional[date] = None,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        status: Optional[str] = None,
    ) -> List[ODAppointment]:
        """
        Get appointments with optional filters.
        
        Maps to: GET /appointments
        """
        params: Dict[str, Any] = {}
        
        if pat_num:
            params["PatNum"] = pat_num
        if target_date:
            params["date"] = target_date.strftime("%Y-%m-%d")
        elif date_start and date_end:
            params["dateStart"] = date_start.strftime("%Y-%m-%d")
            params["dateEnd"] = date_end.strftime("%Y-%m-%d")
        if status:
            params["AptStatus"] = status
        
        response = await self._request("GET", "/appointments", params=params or None)
        
        if response.status_code != 200:
            logger.error(f"Failed to get appointments: {response.text}")
            return []
        
        data = response.json()
        if not isinstance(data, list):
            return []
        
        return [ODAppointment.from_api(a) for a in data]
    
    async def get_appointment(self, apt_num: int) -> Optional[ODAppointment]:
        """Get a single appointment by AptNum."""
        response = await self._request("GET", f"/appointments/{apt_num}")
        
        if response.status_code != 200:
            return None
        
        return ODAppointment.from_api(response.json())
    
    async def create_appointment(
        self,
        pat_num: int,
        op_num: int,
        apt_datetime: datetime,
        provider_num: Optional[int] = None,
        pattern: Optional[str] = None,
        note: Optional[str] = None,
        is_new_patient: bool = False,
        appointment_type_num: Optional[int] = None,
        clinic_num: Optional[int] = None,
    ) -> Optional[ODAppointment]:
        """
        Create an appointment in Open Dental.
        
        Requires Appointments permission ($30/month tier).
        
        Maps to: POST /appointments
        
        Args:
            pat_num: Patient number (required)
            op_num: Operatory number (required) - from GET /appointments/Slots
            apt_datetime: Appointment date/time (required)
            provider_num: Provider to assign
            pattern: Time pattern (/XX/ = 20min, //XXXX// = 40min provider time)
            note: Appointment note
            is_new_patient: Flag for new patients
            appointment_type_num: FK to AppointmentType
        """
        payload: Dict[str, Any] = {
            "PatNum": pat_num,
            "Op": op_num,
            "AptDateTime": apt_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        if provider_num:
            payload["ProvNum"] = provider_num
        if pattern:
            payload["Pattern"] = pattern
        if note:
            payload["Note"] = note
        if is_new_patient:
            payload["IsNewPatient"] = "true"
        if appointment_type_num:
            payload["AppointmentTypeNum"] = appointment_type_num
        if clinic_num or self.config.clinic_num:
            payload["ClinicNum"] = clinic_num or self.config.clinic_num
        
        response = await self._request("POST", "/appointments", json_data=payload)
        
        if response.status_code == 201:
            apt = ODAppointment.from_api(response.json())
            logger.info(
                f"Created Open Dental appointment: AptNum={apt.apt_num} "
                f"PatNum={apt.pat_num} at {apt.apt_datetime}"
            )
            return apt
        
        logger.error(f"Failed to create appointment: {response.status_code} - {response.text}")
        return None
    
    async def update_appointment(
        self,
        apt_num: int,
        note: Optional[str] = None,
        confirmed: Optional[str] = None,
        apt_datetime: Optional[datetime] = None,
        op_num: Optional[int] = None,
        status: Optional[str] = None,
    ) -> bool:
        """
        Update an existing appointment.
        
        Maps to: PUT /appointments/{apt_num}
        """
        payload: Dict[str, Any] = {}
        
        if note is not None:
            payload["Note"] = note
        if apt_datetime:
            payload["AptDateTime"] = apt_datetime.strftime("%Y-%m-%d %H:%M:%S")
        if op_num:
            payload["Op"] = op_num
        if status:
            payload["AptStatus"] = status
        
        if not payload:
            return True  # Nothing to update
        
        response = await self._request("PUT", f"/appointments/{apt_num}", json_data=payload)
        
        if response.status_code == 200:
            logger.info(f"Updated Open Dental appointment {apt_num}")
            return True
        
        logger.error(f"Failed to update appointment {apt_num}: {response.text}")
        return False
    
    async def confirm_appointment(
        self,
        apt_num: int,
        confirm_value: str = "Confirmed",
    ) -> bool:
        """
        Confirm an appointment.
        
        Maps to: PUT /appointments/{apt_num}/Confirm
        
        Args:
            confirm_value: "None", "Sent", "Confirmed", "Not Accepted", "Failed"
        """
        response = await self._request(
            "PUT", 
            f"/appointments/{apt_num}/Confirm",
            json_data={"confirmVal": confirm_value},
        )
        
        if response.status_code == 200:
            logger.info(f"Confirmed appointment {apt_num}: {confirm_value}")
            return True
        
        logger.error(f"Failed to confirm appointment {apt_num}: {response.text}")
        return False
    
    async def append_appointment_note(self, apt_num: int, note: str) -> bool:
        """
        Append a note to an appointment (doesn't overwrite).
        
        Maps to: PUT /appointments/{apt_num}/Note
        """
        response = await self._request(
            "PUT",
            f"/appointments/{apt_num}/Note",
            json_data={"Note": note},
        )
        
        if response.status_code == 200:
            return True
        
        logger.error(f"Failed to append note to appointment {apt_num}: {response.text}")
        return False
    
    async def break_appointment(
        self,
        apt_num: int,
        send_to_unscheduled: bool = True,
        break_type: Optional[str] = None,
    ) -> bool:
        """
        Break (cancel) a scheduled appointment.
        
        Maps to: PUT /appointments/{apt_num}/Break
        
        Args:
            send_to_unscheduled: Usually True to keep on unscheduled list
            break_type: Optional "Missed" or "Cancelled" (adds procedure code)
        """
        payload: Dict[str, Any] = {
            "sendToUnscheduledList": "true" if send_to_unscheduled else "false",
        }
        if break_type:
            payload["breakType"] = break_type
        
        response = await self._request(
            "PUT",
            f"/appointments/{apt_num}/Break",
            json_data=payload,
        )
        
        if response.status_code == 200:
            logger.info(f"Broke appointment {apt_num}")
            return True
        
        logger.error(f"Failed to break appointment {apt_num}: {response.text}")
        return False

    # -------------------------------------------------------------------------
    # Helper: Duration Pattern Builder
    # -------------------------------------------------------------------------
    
    @staticmethod
    def build_pattern(duration_minutes: int) -> str:
        """
        Build an Open Dental time pattern for a given duration.
        
        Pattern uses 5-minute increments:
        - 'X' = provider time (colored on schedule)
        - '/' = other time (hygiene check, etc.)
        
        Common patterns:
        - 20 min: /XX/
        - 30 min: /XXXX/
        - 45 min: /XXXXXX//
        - 60 min: //XXXXXXXX//
        - 90 min: //XXXXXXXXXXXX////
        """
        total_slots = max(duration_minutes // 5, 4)  # Min 4 slots (20 min)
        
        # Pattern: buffer + provider time + buffer
        buffer = max(total_slots // 6, 1)
        provider_time = total_slots - (buffer * 2)
        
        return "/" * buffer + "X" * provider_time + "/" * buffer

    # -------------------------------------------------------------------------
    # High-Level Methods for Voice Agent Integration
    # -------------------------------------------------------------------------
    
    async def voice_check_availability(
        self,
        date_str: str,
        time_preference: Optional[str] = None,
        appointment_type: Optional[str] = None,
        is_new_patient: bool = False,
    ) -> Dict[str, Any]:
        """
        Check availability - designed for voice agent function calling.
        
        This mirrors the check_availability function schema in prompt_builder.py.
        
        Returns formatted result the AI can read to the patient.
        """
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "message": "Invalid date format. Use YYYY-MM-DD."}
        
        if target < date.today():
            return {"success": False, "message": "Cannot check availability for past dates."}
        
        # Determine minimum slot length based on appointment type
        duration_map = {
            "cleaning": 60,
            "checkup": 30,
            "procedure": 60,
            "emergency": 45,
            "consultation": 30,
        }
        length = duration_map.get(appointment_type or "checkup", 30)
        if is_new_patient:
            length = max(length, 60)  # New patients get longer slots
        
        slots = await self.get_available_slots(
            target_date=target,
            length_minutes=length,
        )
        
        if not slots:
            # Check next few days
            extended = await self.get_available_slots(
                date_start=target,
                date_end=target + timedelta(days=3),
                length_minutes=length,
            )
            if extended:
                return {
                    "success": True,
                    "message": f"No slots on {date_str}, but I found openings on nearby dates.",
                    "slots": [s.to_dict() for s in extended[:10]],
                }
            return {
                "success": False,
                "message": f"No available slots found around {date_str}. The schedule may be full.",
            }
        
        # Filter by time preference
        if time_preference:
            filtered = self._filter_by_preference(slots, time_preference)
            if filtered:
                slots = filtered
        
        # Get provider names
        providers = await self.get_providers()
        prov_map = {p.prov_num: p.display_name for p in providers}
        
        # Format for AI
        slot_list = []
        for s in slots[:8]:
            slot_info = s.to_dict()
            slot_info["provider_name"] = prov_map.get(s.provider_num, "")
            slot_info["formatted_time"] = s.start.strftime("%I:%M %p").lstrip("0")
            slot_list.append(slot_info)
        
        return {
            "success": True,
            "message": f"Found {len(slots)} available slots on {date_str}.",
            "slots": slot_list,
            "date": date_str,
        }
    
    async def voice_book_appointment(
        self,
        patient_name: str,
        date_str: str,
        time_str: str,
        reason: str,
        phone_number: Optional[str] = None,
        is_new_patient: bool = False,
        urgency: str = "routine",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Book an appointment - designed for voice agent function calling.
        
        This mirrors the book_appointment function schema in prompt_builder.py.
        Handles patient lookup/creation and appointment creation in one flow.
        """
        # Parse date and time
        try:
            apt_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return {"success": False, "message": "Invalid date or time format."}
        
        if apt_datetime < datetime.now():
            return {"success": False, "message": "Cannot book appointments in the past."}
        
        # Step 1: Find or create patient
        name_parts = patient_name.strip().split()
        first_name = name_parts[0] if name_parts else patient_name
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        
        pat_num = None
        
        if not is_new_patient:
            # Try to find existing patient
            patients = await self.search_patients(
                last_name=last_name,
                first_name=first_name,
            )
            if patients:
                # Use the first match (best match)
                pat_num = patients[0].pat_num
                logger.info(f"Found existing patient: {patients[0].display_name} (PatNum={pat_num})")
        
        if pat_num is None:
            # Create new patient
            new_patient = await self.create_patient(
                first_name=first_name,
                last_name=last_name or first_name,  # Fallback if no last name
                phone=phone_number,
                is_new_patient=True,
            )
            if not new_patient:
                return {
                    "success": False,
                    "message": "Could not create patient record. Please try again.",
                }
            pat_num = new_patient.pat_num
            is_new_patient = True
        
        # Step 2: Find a matching slot to get the operatory
        slots = await self.get_available_slots(
            target_date=apt_datetime.date(),
        )
        
        # Find the closest slot to requested time
        best_slot = None
        min_diff = float("inf")
        for slot in slots:
            diff = abs((slot.start - apt_datetime).total_seconds())
            if diff < min_diff and slot.start >= apt_datetime - timedelta(minutes=15):
                min_diff = diff
                best_slot = slot
        
        if not best_slot:
            return {
                "success": False,
                "message": f"The requested time ({time_str}) is not available on {date_str}. Please check availability first.",
            }
        
        # Step 3: Determine pattern (duration) based on appointment type
        duration_map = {
            "cleaning": 60,
            "checkup": 30,
            "toothache": 45,
            "crown": 90,
            "filling": 60,
            "emergency": 45,
            "consultation": 30,
            "root_canal": 120,
            "extraction": 60,
            "whitening": 90,
        }
        duration = duration_map.get(reason.lower(), 60)
        if is_new_patient:
            duration = max(duration, 60)
        
        pattern = self.build_pattern(duration)
        
        # Step 4: Build note
        note_parts = [f"Booked via DentSignal AI Voice Agent"]
        if reason:
            note_parts.append(f"Reason: {reason}")
        if urgency and urgency != "routine":
            note_parts.append(f"Urgency: {urgency}")
        if notes:
            note_parts.append(f"Patient notes: {notes}")
        if phone_number:
            note_parts.append(f"Phone: {phone_number}")
        
        # Step 5: Create appointment
        apt = await self.create_appointment(
            pat_num=pat_num,
            op_num=best_slot.operatory_num,
            apt_datetime=best_slot.start,
            provider_num=best_slot.provider_num,
            pattern=pattern,
            note="\n".join(note_parts),
            is_new_patient=is_new_patient,
        )
        
        if not apt:
            return {
                "success": False,
                "message": "Failed to create the appointment in the system. Please try again.",
            }
        
        # Get provider name for confirmation
        providers = await self.get_providers()
        prov_name = ""
        for p in providers:
            if p.prov_num == best_slot.provider_num:
                prov_name = p.display_name
                break
        
        return {
            "success": True,
            "message": "Appointment booked successfully!",
            "appointment": {
                "apt_num": apt.apt_num,
                "datetime": apt.apt_datetime.isoformat(),
                "formatted_time": apt.apt_datetime.strftime("%A, %B %d at %I:%M %p").replace(" 0", " "),
                "provider": prov_name or apt.provider_abbr,
                "duration_minutes": duration,
                "is_new_patient": is_new_patient,
                "reason": reason,
            },
        }
    
    async def voice_cancel_appointment(
        self,
        patient_name: str,
        appointment_date: Optional[str] = None,
        reason: Optional[str] = None,
        reschedule: bool = False,
    ) -> Dict[str, Any]:
        """
        Cancel an appointment - designed for voice agent function calling.
        
        Mirrors the cancel_appointment function schema in prompt_builder.py.
        """
        # Find patient
        name_parts = patient_name.strip().split()
        first_name = name_parts[0] if name_parts else patient_name
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        
        patients = await self.search_patients(
            last_name=last_name,
            first_name=first_name,
        )
        
        if not patients:
            return {
                "success": False,
                "message": f"Could not find a patient named {patient_name}.",
            }
        
        # Find their upcoming appointments
        pat_num = patients[0].pat_num
        appointments = await self.get_appointments(
            pat_num=pat_num,
            status="Scheduled",
        )
        
        # Filter to future appointments
        now = datetime.now()
        future_apts = [a for a in appointments if a.apt_datetime > now]
        
        if not future_apts:
            return {
                "success": False,
                "message": f"No upcoming appointments found for {patient_name}.",
            }
        
        # If date specified, find matching appointment
        target_apt = None
        if appointment_date:
            try:
                target = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                target_apt = next(
                    (a for a in future_apts if a.apt_datetime.date() == target),
                    None
                )
            except ValueError:
                pass
        
        if not target_apt:
            # Use the soonest upcoming appointment
            target_apt = min(future_apts, key=lambda a: a.apt_datetime)
        
        # Determine break type based on timing
        hours_until = (target_apt.apt_datetime - now).total_seconds() / 3600
        break_type = None
        if hours_until < 24 and reason != "emergency":
            break_type = "Cancelled"  # Less than 24h notice
        
        # Add cancellation note
        note = f"Cancelled via DentSignal AI"
        if reason:
            note += f" - Reason: {reason}"
        if reschedule:
            note += " - Patient wants to reschedule"
        
        await self.append_appointment_note(target_apt.apt_num, note)
        
        # Break the appointment
        success = await self.break_appointment(
            apt_num=target_apt.apt_num,
            send_to_unscheduled=reschedule,
            break_type=break_type,
        )
        
        if success:
            result: Dict[str, Any] = {
                "success": True,
                "message": f"Appointment on {target_apt.apt_datetime.strftime('%A, %B %d at %I:%M %p')} has been cancelled.",
            }
            if reschedule:
                result["message"] += " Would you like to schedule a new appointment?"
                result["reschedule_requested"] = True
            return result
        
        return {
            "success": False,
            "message": "Failed to cancel the appointment. Please try again or call the office directly.",
        }
    
    async def voice_lookup_patient(
        self,
        patient_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        date_of_birth: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Look up a patient - designed for voice agent function calling.
        
        Mirrors the lookup_patient function schema in prompt_builder.py.
        """
        # Parse name
        first_name = None
        last_name = None
        if patient_name:
            parts = patient_name.strip().split()
            first_name = parts[0] if parts else None
            last_name = parts[-1] if len(parts) > 1 else None
        
        patients = await self.search_patients(
            last_name=last_name,
            first_name=first_name,
            phone=phone_number,
            birthdate=date_of_birth,
        )
        
        if not patients:
            return {
                "success": False,
                "is_new_patient": True,
                "message": "No matching patient found. This appears to be a new patient.",
            }
        
        patient = patients[0]
        
        # Get their upcoming appointments
        appointments = await self.get_appointments(
            pat_num=patient.pat_num,
            status="Scheduled",
        )
        future_apts = [a for a in appointments if a.apt_datetime > datetime.now()]
        
        result: Dict[str, Any] = {
            "success": True,
            "is_new_patient": False,
            "patient": {
                "pat_num": patient.pat_num,
                "name": patient.display_name,
                "phone": patient.phone_wireless or patient.phone_home,
                "email": patient.email,
            },
            "upcoming_appointments": [a.to_dict() for a in future_apts[:3]],
        }
        
        if future_apts:
            next_apt = min(future_apts, key=lambda a: a.apt_datetime)
            result["next_appointment"] = (
                f"{next_apt.apt_datetime.strftime('%A, %B %d at %I:%M %p')} "
                f"with {next_apt.provider_abbr} for {next_apt.proc_description or 'appointment'}"
            )
        
        return result
    
    def _filter_by_preference(
        self, 
        slots: List[ODTimeSlot], 
        preference: str,
    ) -> List[ODTimeSlot]:
        """Filter slots by time-of-day preference."""
        filters = {
            "early_morning": (7, 9),
            "morning": (9, 12),
            "afternoon": (12, 17),
            "evening": (17, 20),
        }
        
        if preference not in filters:
            return slots
        
        start_hour, end_hour = filters[preference]
        return [
            s for s in slots 
            if start_hour <= s.start.hour < end_hour
        ]


# =============================================================================
# Factory Function
# =============================================================================

def create_open_dental_service(
    developer_key: str,
    customer_key: str,
    api_mode: str = "remote",
    base_url: Optional[str] = None,
    clinic_num: Optional[int] = None,
) -> OpenDentalService:
    """
    Factory function to create an OpenDentalService instance.
    
    Args:
        developer_key: DentSignal's developer API key
        customer_key: Clinic's customer API key
        api_mode: "remote", "service", or "local"
        base_url: Override URL for service/local mode
        clinic_num: ClinicNum for multi-location practices
    """
    mode_map = {
        "remote": OpenDentalApiMode.REMOTE,
        "service": OpenDentalApiMode.SERVICE,
        "local": OpenDentalApiMode.LOCAL,
    }
    
    config = OpenDentalConfig(
        developer_key=developer_key,
        customer_key=customer_key,
        api_mode=mode_map.get(api_mode, OpenDentalApiMode.REMOTE),
        base_url=base_url,
        clinic_num=clinic_num,
    )
    
    return OpenDentalService(config)
