"""
email_templates.py - Email Templates for DentSignal

Pre-built email templates for:
- Welcome emails (new clinic signup)
- Onboarding progress emails
- Weekly digest emails
- Milestone celebration emails

Usage:
    from email_templates import WelcomeEmail, WeeklyDigestEmail
    
    email = WelcomeEmail(clinic_name="Sunny Smiles", owner_name="Dr. Smith")
    html_content = email.render()
    plain_text = email.render_plain()
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass


# -----------------------------------------------------------------------------
# Base Email Template
# -----------------------------------------------------------------------------

@dataclass
class BaseEmail:
    """Base class for all email templates."""
    
    # Email styling constants
    PRIMARY_COLOR = "#10b981"  # Green
    TEXT_COLOR = "#1f2937"
    MUTED_COLOR = "#6b7280"
    BG_COLOR = "#f9fafb"
    
    def get_header(self) -> str:
        """Common email header with logo."""
        return f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: {self.BG_COLOR}; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(to bottom, #0a1628, #1e40af); padding: 24px; text-align: center;">
                                <img src="https://dentsignal.me/logo.png" alt="DentSignal" height="50" style="display: inline-block;">
                            </td>
                        </tr>
        """
    
    def get_footer(self) -> str:
        """Common email footer."""
        return f"""
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f3f4f6; padding: 24px; text-align: center;">
                                <p style="margin: 0 0 8px 0; color: {self.MUTED_COLOR}; font-size: 14px;">
                                    Need help? Reply to this email or visit our <a href="https://dentsignal.me/help" style="color: {self.PRIMARY_COLOR};">Help Center</a>
                                </p>
                                <p style="margin: 0; color: {self.MUTED_COLOR}; font-size: 12px;">
                                    © {datetime.now().year} DentSignal. All rights reserved.<br>
                                    <a href="https://dentsignal.me/unsubscribe" style="color: {self.MUTED_COLOR};">Unsubscribe</a>
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        """
    
    def render(self) -> str:
        """Render the full HTML email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.get_subject()}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: {self.TEXT_COLOR};">
            {self.get_header()}
            {self.get_body()}
            {self.get_footer()}
        </body>
        </html>
        """
    
    def render_plain(self) -> str:
        """Render plain text version of the email."""
        raise NotImplementedError("Subclasses must implement render_plain()")
    
    def get_subject(self) -> str:
        """Get email subject line."""
        raise NotImplementedError("Subclasses must implement get_subject()")
    
    def get_body(self) -> str:
        """Get email body content."""
        raise NotImplementedError("Subclasses must implement get_body()")


# -----------------------------------------------------------------------------
# Welcome Email
# -----------------------------------------------------------------------------

@dataclass
class WelcomeEmail(BaseEmail):
    """Welcome email sent when a new clinic signs up."""
    
    clinic_name: str
    owner_name: str
    twilio_number: Optional[str] = None
    dashboard_url: str = "https://dentsignal.me/dashboard"
    
    def get_subject(self) -> str:
        return f"🎉 Welcome to DentSignal, {self.owner_name}!"
    
    def get_body(self) -> str:
        phone_section = ""
        if self.twilio_number:
            phone_section = f"""
            <tr>
                <td style="padding: 16px; background-color: #f0fdf4; border-radius: 8px; margin-bottom: 16px;">
                    <p style="margin: 0 0 8px 0; font-size: 14px; color: {self.MUTED_COLOR};">Your AI Receptionist Number:</p>
                    <p style="margin: 0; font-size: 24px; font-weight: bold; color: {self.PRIMARY_COLOR};">{self.twilio_number}</p>
                </td>
            </tr>
            <tr><td style="height: 16px;"></td></tr>
            """
        
        return f"""
        <!-- Body Content -->
        <tr>
            <td style="padding: 40px;">
                <h1 style="margin: 0 0 16px 0; font-size: 28px; font-weight: bold; color: {self.TEXT_COLOR};">
                    Welcome to DentSignal! 🦷
                </h1>
                
                <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 1.6; color: {self.TEXT_COLOR};">
                    Hi {self.owner_name},
                </p>
                
                <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 1.6; color: {self.TEXT_COLOR};">
                    Thank you for choosing DentSignal for <strong>{self.clinic_name}</strong>! 
                    Your AI receptionist is ready to start answering calls 24/7.
                </p>
                
                {phone_section}
                
                <h2 style="margin: 24px 0 16px 0; font-size: 20px; font-weight: bold; color: {self.TEXT_COLOR};">
                    Getting Started (5 minutes)
                </h2>
                
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                            <table cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="width: 32px; vertical-align: top;">
                                        <span style="display: inline-block; width: 24px; height: 24px; background-color: {self.PRIMARY_COLOR}; color: white; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; font-weight: bold;">1</span>
                                    </td>
                                    <td>
                                        <p style="margin: 0; font-size: 16px; font-weight: 600;">Complete your clinic profile</p>
                                        <p style="margin: 4px 0 0 0; font-size: 14px; color: {self.MUTED_COLOR};">Add business hours, services, and customize your AI greeting</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #e5e7eb;">
                            <table cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="width: 32px; vertical-align: top;">
                                        <span style="display: inline-block; width: 24px; height: 24px; background-color: {self.PRIMARY_COLOR}; color: white; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; font-weight: bold;">2</span>
                                    </td>
                                    <td>
                                        <p style="margin: 0; font-size: 16px; font-weight: 600;">Set up call forwarding</p>
                                        <p style="margin: 4px 0 0 0; font-size: 14px; color: {self.MUTED_COLOR};">Forward your main line to your AI number when you're busy</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0;">
                            <table cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="width: 32px; vertical-align: top;">
                                        <span style="display: inline-block; width: 24px; height: 24px; background-color: {self.PRIMARY_COLOR}; color: white; border-radius: 50%; text-align: center; line-height: 24px; font-size: 12px; font-weight: bold;">3</span>
                                    </td>
                                    <td>
                                        <p style="margin: 0; font-size: 16px; font-weight: 600;">Make a test call</p>
                                        <p style="margin: 4px 0 0 0; font-size: 14px; color: {self.MUTED_COLOR};">Call your AI number to see how patients experience it</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
                
                <div style="text-align: center; margin-top: 32px;">
                    <a href="{self.dashboard_url}" style="display: inline-block; padding: 14px 32px; background-color: {self.PRIMARY_COLOR}; color: white; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                        Go to Dashboard →
                    </a>
                </div>
                
                <p style="margin: 32px 0 0 0; font-size: 14px; color: {self.MUTED_COLOR}; text-align: center;">
                    Questions? Reply to this email - we read every message!
                </p>
            </td>
        </tr>
        """
    
    def render_plain(self) -> str:
        phone_line = f"\nYour AI Receptionist Number: {self.twilio_number}\n" if self.twilio_number else ""
        
        return f"""
Welcome to DentSignal! 🦷

Hi {self.owner_name},

Thank you for choosing DentSignal for {self.clinic_name}! 
Your AI receptionist is ready to start answering calls 24/7.
{phone_line}
GETTING STARTED (5 minutes):

1. Complete your clinic profile
   Add business hours, services, and customize your AI greeting

2. Set up call forwarding
   Forward your main line to your AI number when you're busy

3. Make a test call
   Call your AI number to see how patients experience it

Go to Dashboard: {self.dashboard_url}

Questions? Reply to this email - we read every message!

---
© {datetime.now().year} DentSignal. All rights reserved.
        """.strip()


# -----------------------------------------------------------------------------
# Onboarding Progress Email
# -----------------------------------------------------------------------------

@dataclass
class OnboardingProgressEmail(BaseEmail):
    """Email sent when user completes onboarding steps."""
    
    owner_name: str
    clinic_name: str
    step_completed: str
    next_step: str
    progress_percent: int
    
    def get_subject(self) -> str:
        return f"✅ {self.step_completed} - You're {self.progress_percent}% done!"
    
    def get_body(self) -> str:
        return f"""
        <tr>
            <td style="padding: 40px;">
                <h1 style="margin: 0 0 16px 0; font-size: 24px; font-weight: bold; color: {self.TEXT_COLOR};">
                    Great progress, {self.owner_name}! 🎯
                </h1>
                
                <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 1.6; color: {self.TEXT_COLOR};">
                    You just completed: <strong>{self.step_completed}</strong>
                </p>
                
                <!-- Progress Bar -->
                <div style="background-color: #e5e7eb; border-radius: 8px; height: 12px; margin-bottom: 24px;">
                    <div style="background-color: {self.PRIMARY_COLOR}; border-radius: 8px; height: 12px; width: {self.progress_percent}%;"></div>
                </div>
                <p style="margin: 0 0 24px 0; font-size: 14px; color: {self.MUTED_COLOR}; text-align: center;">
                    {self.progress_percent}% complete
                </p>
                
                <div style="background-color: #f0fdf4; border-left: 4px solid {self.PRIMARY_COLOR}; padding: 16px; margin-bottom: 24px;">
                    <p style="margin: 0 0 8px 0; font-size: 14px; color: {self.MUTED_COLOR};">Next step:</p>
                    <p style="margin: 0; font-size: 18px; font-weight: 600; color: {self.TEXT_COLOR};">{self.next_step}</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="https://dentsignal.me/dashboard" style="display: inline-block; padding: 14px 32px; background-color: {self.PRIMARY_COLOR}; color: white; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                        Continue Setup →
                    </a>
                </div>
            </td>
        </tr>
        """
    
    def render_plain(self) -> str:
        return f"""
Great progress, {self.owner_name}! 🎯

You just completed: {self.step_completed}

Progress: {self.progress_percent}% complete

NEXT STEP:
{self.next_step}

Continue Setup: https://dentsignal.me/dashboard

---
© {datetime.now().year} DentSignal
        """.strip()


# -----------------------------------------------------------------------------
# Weekly Digest Email
# -----------------------------------------------------------------------------

# Celebration messages for email subject lines and closings
WEEKLY_EMAIL_CELEBRATIONS = [
    {
        "subject": "Your team just saved ${revenue} this week 💰",
        "closing": "Go check your dashboard. You've earned the victory lap. 🏆",
    },
    {
        "subject": "Your AI handled {calls} calls. You handled zero stress. 🎯",
        "closing": "See the full breakdown. Your practice is crushing it. 🚀",
    },
    {
        "subject": "Week summary: More patients, more revenue, same schedule. ⚡",
        "closing": "Check the dashboard. Your numbers are worth celebrating. 🎉",
    },
    {
        "subject": "Your AI worked 168 hours. Never called in sick. 🤖",
        "closing": "Review what your team accomplished. The data is beautiful. ✨",
    },
    {
        "subject": "{calls} calls answered. {appointments} appointments booked. Zero burnout. 👑",
        "closing": "See your weekly wins in the dashboard. You deserve this. 💎",
    },
    {
        "subject": "Your practice just recovered ${revenue} in missed revenue. 📈",
        "closing": "View the full report. Numbers don't lie. They celebrate. ✅",
    },
    {
        "subject": "Your team's weekly performance: Legendary. (Your AI agrees.) 🌟",
        "closing": "Check out what you built. Take a moment to breathe. 💙",
    },
    {
        "subject": "Weekly reality check: Your AI is earning its keep. 💪",
        "closing": "Dashboard has all the proof. Go take a look. 🔥",
    },
]


def get_celebration_pair(
    week_number: int,
    total_calls: int = 0,
    appointments_booked: int = 0,
    revenue_recovered: float = 0
) -> dict:
    """Get a celebration subject/closing pair for the week."""
    import random
    
    # Use week number to rotate through pairs (or randomize)
    pair = WEEKLY_EMAIL_CELEBRATIONS[(week_number - 1) % len(WEEKLY_EMAIL_CELEBRATIONS)]
    
    # Format the subject with actual values
    subject = pair["subject"].format(
        revenue=f"{revenue_recovered:,.0f}",
        calls=total_calls,
        appointments=appointments_booked
    )
    
    return {
        "subject": subject,
        "closing": pair["closing"]
    }


@dataclass
class WeeklyDigestEmail(BaseEmail):
    """Weekly performance digest email."""
    
    owner_name: str
    clinic_name: str
    week_start: str
    week_end: str
    total_calls: int
    calls_change: int  # Percentage change from last week
    appointments_booked: int
    revenue_recovered: float
    avg_call_duration: str
    top_hours: list  # e.g., ["10am", "2pm", "4pm"]
    missed_calls: int = 0
    week_number: int = 1  # For celebration rotation
    use_celebration_subject: bool = True
    
    def get_celebration_pair(self) -> dict:
        """Get the celebration messages for this email."""
        return get_celebration_pair(
            self.week_number,
            self.total_calls,
            self.appointments_booked,
            self.revenue_recovered
        )
    
    def get_subject(self) -> str:
        if self.use_celebration_subject:
            return self.get_celebration_pair()["subject"]
        
        # Fallback to standard subject
        emoji = "🎉" if self.calls_change > 0 else "📊"
        return f"{emoji} Your Weekly AI Receptionist Report - {self.total_calls} calls handled"
    
    def get_body(self) -> str:
        change_color = "#22c55e" if self.calls_change >= 0 else "#ef4444"
        change_arrow = "↑" if self.calls_change >= 0 else "↓"
        
        peak_hours = ", ".join(self.top_hours) if self.top_hours else "N/A"
        
        return f"""
        <tr>
            <td style="padding: 40px;">
                <h1 style="margin: 0 0 8px 0; font-size: 24px; font-weight: bold; color: {self.TEXT_COLOR};">
                    Weekly Report for {self.clinic_name}
                </h1>
                <p style="margin: 0 0 24px 0; font-size: 14px; color: {self.MUTED_COLOR};">
                    {self.week_start} - {self.week_end}
                </p>
                
                <!-- Stats Grid -->
                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                    <tr>
                        <td style="width: 50%; padding: 16px; background-color: #f3f4f6; border-radius: 8px 0 0 8px;">
                            <p style="margin: 0 0 4px 0; font-size: 14px; color: {self.MUTED_COLOR};">Total Calls</p>
                            <p style="margin: 0; font-size: 32px; font-weight: bold; color: {self.TEXT_COLOR};">{self.total_calls}</p>
                            <p style="margin: 4px 0 0 0; font-size: 14px; color: {change_color};">
                                {change_arrow} {abs(self.calls_change)}% vs last week
                            </p>
                        </td>
                        <td style="width: 50%; padding: 16px; background-color: #f0fdf4; border-radius: 0 8px 8px 0;">
                            <p style="margin: 0 0 4px 0; font-size: 14px; color: {self.MUTED_COLOR};">Revenue Recovered</p>
                            <p style="margin: 0; font-size: 32px; font-weight: bold; color: {self.PRIMARY_COLOR};">${self.revenue_recovered:,.0f}</p>
                            <p style="margin: 4px 0 0 0; font-size: 14px; color: {self.MUTED_COLOR};">
                                {self.appointments_booked} appointments booked
                            </p>
                        </td>
                    </tr>
                </table>
                
                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                    <tr>
                        <td style="width: 33%; padding: 16px; background-color: #f3f4f6; border-radius: 8px;">
                            <p style="margin: 0 0 4px 0; font-size: 12px; color: {self.MUTED_COLOR};">Avg Duration</p>
                            <p style="margin: 0; font-size: 20px; font-weight: bold; color: {self.TEXT_COLOR};">{self.avg_call_duration}</p>
                        </td>
                        <td style="width: 8px;"></td>
                        <td style="width: 33%; padding: 16px; background-color: #f3f4f6; border-radius: 8px;">
                            <p style="margin: 0 0 4px 0; font-size: 12px; color: {self.MUTED_COLOR};">Peak Hours</p>
                            <p style="margin: 0; font-size: 20px; font-weight: bold; color: {self.TEXT_COLOR};">{peak_hours}</p>
                        </td>
                        <td style="width: 8px;"></td>
                        <td style="width: 33%; padding: 16px; background-color: #fef2f2; border-radius: 8px;">
                            <p style="margin: 0 0 4px 0; font-size: 12px; color: {self.MUTED_COLOR};">Missed Calls</p>
                            <p style="margin: 0; font-size: 20px; font-weight: bold; color: #ef4444;">{self.missed_calls}</p>
                        </td>
                    </tr>
                </table>
                
                <!-- Celebration Closing -->
                <p style="text-align: center; margin: 24px 0; font-size: 16px; color: {self.TEXT_COLOR}; font-weight: 500;">
                    {self.get_celebration_pair()["closing"]}
                </p>
                
                <div style="text-align: center; margin-top: 32px;">
                    <a href="https://dentsignal.me/analytics" style="display: inline-block; padding: 14px 32px; background-color: {self.PRIMARY_COLOR}; color: white; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                        View Full Analytics →
                    </a>
                </div>
            </td>
        </tr>
        """
    
    def render_plain(self) -> str:
        change_arrow = "↑" if self.calls_change >= 0 else "↓"
        peak_hours = ", ".join(self.top_hours) if self.top_hours else "N/A"
        
        return f"""
Weekly Report for {self.clinic_name}
{self.week_start} - {self.week_end}

HIGHLIGHTS:
• Total Calls: {self.total_calls} ({change_arrow} {abs(self.calls_change)}% vs last week)
• Appointments Booked: {self.appointments_booked}
• Revenue Recovered: ${self.revenue_recovered:,.0f}
• Avg Call Duration: {self.avg_call_duration}
• Peak Hours: {peak_hours}
• Missed Calls: {self.missed_calls}

View Full Analytics: https://dentsignal.me/analytics

---
© {datetime.now().year} DentSignal
        """.strip()


# -----------------------------------------------------------------------------
# Milestone Email (First Call, 100 Calls, etc.)
# -----------------------------------------------------------------------------

@dataclass
class MilestoneEmail(BaseEmail):
    """Celebration email for reaching milestones."""
    
    owner_name: str
    clinic_name: str
    milestone: str  # e.g., "first_call", "100_calls", "1000_calls"
    milestone_value: int
    
    MILESTONES = {
        "first_call": ("🎉", "Your First AI Call!", "Your AI receptionist just handled their first call!"),
        "first_booking": ("📅", "First Appointment Booked!", "Your AI just booked their first appointment!"),
        "100_calls": ("💯", "100 Calls Handled!", "Your AI has now helped 100 patients!"),
        "500_calls": ("🏆", "500 Calls Milestone!", "Half a thousand calls and counting!"),
        "1000_calls": ("🚀", "1,000 Calls!", "Your AI is a patient communication superstar!"),
    }
    
    def get_subject(self) -> str:
        emoji, title, _ = self.MILESTONES.get(self.milestone, ("🎯", f"{self.milestone_value} Calls!", ""))
        return f"{emoji} {title}"
    
    def get_body(self) -> str:
        emoji, title, description = self.MILESTONES.get(self.milestone, ("🎯", f"{self.milestone_value} Calls!", "Amazing progress!"))
        
        return f"""
        <tr>
            <td style="padding: 40px; text-align: center;">
                <div style="font-size: 64px; margin-bottom: 16px;">{emoji}</div>
                
                <h1 style="margin: 0 0 16px 0; font-size: 28px; font-weight: bold; color: {self.TEXT_COLOR};">
                    {title}
                </h1>
                
                <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 1.6; color: {self.TEXT_COLOR};">
                    {description}
                </p>
                
                <p style="margin: 0 0 32px 0; font-size: 14px; color: {self.MUTED_COLOR};">
                    Keep up the great work, {self.owner_name}!<br>
                    {self.clinic_name} is on fire 🔥
                </p>
                
                <a href="https://dentsignal.me/dashboard" style="display: inline-block; padding: 14px 32px; background-color: {self.PRIMARY_COLOR}; color: white; text-decoration: none; font-size: 16px; font-weight: 600; border-radius: 8px;">
                    View Dashboard →
                </a>
            </td>
        </tr>
        """
    
    def render_plain(self) -> str:
        emoji, title, description = self.MILESTONES.get(self.milestone, ("🎯", f"{self.milestone_value} Calls!", "Amazing progress!"))
        
        return f"""
{emoji} {title}

{description}

Keep up the great work, {self.owner_name}!
{self.clinic_name} is on fire 🔥

View Dashboard: https://dentsignal.me/dashboard

---
© {datetime.now().year} DentSignal
        """.strip()


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def get_welcome_email(clinic_name: str, owner_name: str, twilio_number: str = None) -> WelcomeEmail:
    """Create a welcome email for a new clinic."""
    return WelcomeEmail(
        clinic_name=clinic_name,
        owner_name=owner_name,
        twilio_number=twilio_number
    )


def get_weekly_digest(
    owner_name: str,
    clinic_name: str,
    total_calls: int,
    appointments_booked: int,
    revenue_recovered: float,
    avg_call_duration: str = "3:24",
    calls_change: int = 0,
    top_hours: list = None,
    week_number: int = None,
    use_celebration_subject: bool = True
) -> WeeklyDigestEmail:
    """Create a weekly digest email with celebration messages."""
    from datetime import timedelta
    
    today = datetime.now()
    week_start = (today - timedelta(days=7)).strftime("%b %d")
    week_end = today.strftime("%b %d, %Y")
    
    # Calculate week number if not provided (week of the year)
    if week_number is None:
        week_number = today.isocalendar()[1]
    
    return WeeklyDigestEmail(
        owner_name=owner_name,
        clinic_name=clinic_name,
        week_start=week_start,
        week_end=week_end,
        total_calls=total_calls,
        calls_change=calls_change,
        appointments_booked=appointments_booked,
        revenue_recovered=revenue_recovered,
        avg_call_duration=avg_call_duration,
        top_hours=top_hours or ["10am", "2pm"],
        week_number=week_number,
        use_celebration_subject=use_celebration_subject
    )


# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Test welcome email
    welcome = WelcomeEmail(
        clinic_name="Sunny Smiles Dental",
        owner_name="Dr. Smith",
        twilio_number="+1 (555) 123-4567"
    )
    
    print("=== Welcome Email Subject ===")
    print(welcome.get_subject())
    print("\n=== Plain Text Version ===")
    print(welcome.render_plain()[:200] + "...")
    
    # Verify HTML renders without errors (don't write to disk with sensitive data)
    html_content = welcome.render()
    print(f"\nHTML rendered successfully ({len(html_content)} chars)")
    
    # Test weekly digest
    digest = get_weekly_digest(
        owner_name="Dr. Smith",
        clinic_name="Sunny Smiles Dental",
        total_calls=156,
        appointments_booked=48,
        revenue_recovered=16800,
        calls_change=12,
        top_hours=["10am", "2pm", "4pm"]
    )
    
    print("\n=== Weekly Digest ===")
    print(f"Digest rendered successfully ({len(digest.render())} chars)")
