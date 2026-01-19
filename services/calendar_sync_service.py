"""
Calendar Sync Service - P33

Handles Google Calendar and Outlook Calendar integration for booking sync.
Provides OAuth flow, free/busy checking, and bidirectional event sync.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urlencode

import requests

from database import (
    get_db, CalendarIntegration, CalendarEvent, Booking, BookingSlot, Staff
)

logger = logging.getLogger(__name__)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CALENDAR_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_CALENDAR_REDIRECT_URI', 'http://localhost:5001/api/calendar/google/callback')

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_CALENDAR_API = 'https://www.googleapis.com/calendar/v3'

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

# Outlook OAuth Configuration (Microsoft Graph)
OUTLOOK_CLIENT_ID = os.getenv('OUTLOOK_CALENDAR_CLIENT_ID', '')
OUTLOOK_CLIENT_SECRET = os.getenv('OUTLOOK_CALENDAR_CLIENT_SECRET', '')
OUTLOOK_REDIRECT_URI = os.getenv('OUTLOOK_CALENDAR_REDIRECT_URI', 'http://localhost:5001/api/calendar/outlook/callback')
OUTLOOK_TENANT = os.getenv('OUTLOOK_TENANT', 'common')  # 'common' for multi-tenant

OUTLOOK_AUTH_URL = f'https://login.microsoftonline.com/{OUTLOOK_TENANT}/oauth2/v2.0/authorize'
OUTLOOK_TOKEN_URL = f'https://login.microsoftonline.com/{OUTLOOK_TENANT}/oauth2/v2.0/token'
OUTLOOK_GRAPH_API = 'https://graph.microsoft.com/v1.0'

OUTLOOK_SCOPES = [
    'Calendars.ReadWrite',
    'offline_access',
]


class CalendarSyncService:
    """Service for managing calendar integrations and syncing events"""

    def __init__(self, db=None):
        self.db = db or get_db()

    # ==================== OAuth Flow ====================

    def get_google_auth_url(self, staff_id: int, state: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL"""
        if not GOOGLE_CLIENT_ID:
            raise ValueError("Google Calendar client ID not configured")

        params = {
            'client_id': GOOGLE_CLIENT_ID,
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'response_type': 'code',
            'scope': ' '.join(GOOGLE_SCOPES),
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state or str(staff_id),
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    def get_outlook_auth_url(self, staff_id: int, state: Optional[str] = None) -> str:
        """Generate Outlook OAuth authorization URL"""
        if not OUTLOOK_CLIENT_ID:
            raise ValueError("Outlook Calendar client ID not configured")

        params = {
            'client_id': OUTLOOK_CLIENT_ID,
            'redirect_uri': OUTLOOK_REDIRECT_URI,
            'response_type': 'code',
            'scope': ' '.join(OUTLOOK_SCOPES),
            'state': state or str(staff_id),
        }
        return f"{OUTLOOK_AUTH_URL}?{urlencode(params)}"

    def exchange_google_code(self, code: str, staff_id: int) -> CalendarIntegration:
        """Exchange Google authorization code for tokens and create integration"""
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise ValueError("Google Calendar credentials not configured")

        # Exchange code for tokens
        response = requests.post(GOOGLE_TOKEN_URL, data={
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': GOOGLE_REDIRECT_URI,
        })

        if response.status_code != 200:
            logger.error(f"Google token exchange failed: {response.text}")
            raise Exception(f"Failed to exchange code: {response.text}")

        tokens = response.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in', 3600)

        # Get user's calendars to select primary
        calendars = self._google_list_calendars(access_token)
        primary_calendar = next((c for c in calendars if c.get('primary')), calendars[0] if calendars else None)

        # Check if integration already exists
        existing = self.db.query(CalendarIntegration).filter_by(
            staff_id=staff_id,
            provider='google'
        ).first()

        if existing:
            # Update existing
            existing.access_token = access_token
            existing.refresh_token = refresh_token or existing.refresh_token
            existing.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            existing.is_active = True
            existing.connected_at = datetime.utcnow()
            existing.disconnected_at = None
            if primary_calendar:
                existing.calendar_id = primary_calendar.get('id')
                existing.calendar_name = primary_calendar.get('summary')
            integration = existing
        else:
            # Create new
            integration = CalendarIntegration(
                staff_id=staff_id,
                provider='google',
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                calendar_id=primary_calendar.get('id') if primary_calendar else None,
                calendar_name=primary_calendar.get('summary') if primary_calendar else None,
                is_active=True,
            )
            self.db.add(integration)

        self.db.commit()
        logger.info(f"Google Calendar connected for staff {staff_id}")
        return integration

    def exchange_outlook_code(self, code: str, staff_id: int) -> CalendarIntegration:
        """Exchange Outlook authorization code for tokens and create integration"""
        if not OUTLOOK_CLIENT_ID or not OUTLOOK_CLIENT_SECRET:
            raise ValueError("Outlook Calendar credentials not configured")

        # Exchange code for tokens
        response = requests.post(OUTLOOK_TOKEN_URL, data={
            'client_id': OUTLOOK_CLIENT_ID,
            'client_secret': OUTLOOK_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': OUTLOOK_REDIRECT_URI,
            'scope': ' '.join(OUTLOOK_SCOPES),
        })

        if response.status_code != 200:
            logger.error(f"Outlook token exchange failed: {response.text}")
            raise Exception(f"Failed to exchange code: {response.text}")

        tokens = response.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in', 3600)

        # Get user's calendars
        calendars = self._outlook_list_calendars(access_token)
        default_calendar = next((c for c in calendars if c.get('isDefaultCalendar')), calendars[0] if calendars else None)

        # Check if integration already exists
        existing = self.db.query(CalendarIntegration).filter_by(
            staff_id=staff_id,
            provider='outlook'
        ).first()

        if existing:
            existing.access_token = access_token
            existing.refresh_token = refresh_token or existing.refresh_token
            existing.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            existing.is_active = True
            existing.connected_at = datetime.utcnow()
            existing.disconnected_at = None
            if default_calendar:
                existing.calendar_id = default_calendar.get('id')
                existing.calendar_name = default_calendar.get('name')
            integration = existing
        else:
            integration = CalendarIntegration(
                staff_id=staff_id,
                provider='outlook',
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                calendar_id=default_calendar.get('id') if default_calendar else None,
                calendar_name=default_calendar.get('name') if default_calendar else None,
                is_active=True,
            )
            self.db.add(integration)

        self.db.commit()
        logger.info(f"Outlook Calendar connected for staff {staff_id}")
        return integration

    def refresh_tokens(self, integration: CalendarIntegration) -> bool:
        """Refresh OAuth tokens if expired"""
        if not integration.refresh_token:
            return False

        if integration.token_expires_at and integration.token_expires_at > datetime.utcnow():
            return True  # Not expired yet

        try:
            if integration.provider == 'google':
                response = requests.post(GOOGLE_TOKEN_URL, data={
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET,
                    'refresh_token': integration.refresh_token,
                    'grant_type': 'refresh_token',
                })
            elif integration.provider == 'outlook':
                response = requests.post(OUTLOOK_TOKEN_URL, data={
                    'client_id': OUTLOOK_CLIENT_ID,
                    'client_secret': OUTLOOK_CLIENT_SECRET,
                    'refresh_token': integration.refresh_token,
                    'grant_type': 'refresh_token',
                    'scope': ' '.join(OUTLOOK_SCOPES),
                })
            else:
                return False

            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                return False

            tokens = response.json()
            integration.access_token = tokens.get('access_token')
            if tokens.get('refresh_token'):
                integration.refresh_token = tokens.get('refresh_token')
            integration.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 3600))
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False

    # ==================== Calendar Operations ====================

    def get_integration(self, staff_id: int, provider: Optional[str] = None) -> Optional[CalendarIntegration]:
        """Get active calendar integration for staff"""
        query = self.db.query(CalendarIntegration).filter_by(
            staff_id=staff_id,
            is_active=True
        )
        if provider:
            query = query.filter_by(provider=provider)
        return query.first()

    def get_integrations(self, staff_id: int) -> List[CalendarIntegration]:
        """Get all calendar integrations for staff"""
        return self.db.query(CalendarIntegration).filter_by(staff_id=staff_id).all()

    def disconnect(self, integration_id: int, staff_id: int) -> bool:
        """Disconnect a calendar integration"""
        integration = self.db.query(CalendarIntegration).filter_by(
            id=integration_id,
            staff_id=staff_id
        ).first()

        if not integration:
            return False

        integration.is_active = False
        integration.disconnected_at = datetime.utcnow()
        integration.access_token = None
        self.db.commit()
        logger.info(f"Calendar integration {integration_id} disconnected")
        return True

    def list_calendars(self, integration: CalendarIntegration) -> List[Dict]:
        """List available calendars for an integration"""
        if not self.refresh_tokens(integration):
            raise Exception("Failed to refresh tokens")

        if integration.provider == 'google':
            return self._google_list_calendars(integration.access_token)
        elif integration.provider == 'outlook':
            return self._outlook_list_calendars(integration.access_token)
        return []

    def set_calendar(self, integration_id: int, staff_id: int, calendar_id: str, calendar_name: str) -> bool:
        """Set which calendar to sync with"""
        integration = self.db.query(CalendarIntegration).filter_by(
            id=integration_id,
            staff_id=staff_id
        ).first()

        if not integration:
            return False

        integration.calendar_id = calendar_id
        integration.calendar_name = calendar_name
        self.db.commit()
        return True

    def _google_list_calendars(self, access_token: str) -> List[Dict]:
        """List Google calendars"""
        response = requests.get(
            f"{GOOGLE_CALENDAR_API}/users/me/calendarList",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if response.status_code != 200:
            return []
        data = response.json()
        return [
            {
                'id': cal.get('id'),
                'summary': cal.get('summary'),
                'primary': cal.get('primary', False),
                'accessRole': cal.get('accessRole'),
            }
            for cal in data.get('items', [])
        ]

    def _outlook_list_calendars(self, access_token: str) -> List[Dict]:
        """List Outlook calendars"""
        response = requests.get(
            f"{OUTLOOK_GRAPH_API}/me/calendars",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if response.status_code != 200:
            return []
        data = response.json()
        return [
            {
                'id': cal.get('id'),
                'name': cal.get('name'),
                'isDefaultCalendar': cal.get('isDefaultCalendar', False),
                'canEdit': cal.get('canEdit', True),
            }
            for cal in data.get('value', [])
        ]

    # ==================== Free/Busy Checking ====================

    def get_free_busy(
        self,
        staff_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get busy times for staff from their connected calendars"""
        busy_times = []

        integrations = self.db.query(CalendarIntegration).filter_by(
            staff_id=staff_id,
            is_active=True,
            check_free_busy=True
        ).all()

        for integration in integrations:
            if not self.refresh_tokens(integration):
                continue

            try:
                if integration.provider == 'google':
                    busy = self._google_get_free_busy(integration, start_time, end_time)
                elif integration.provider == 'outlook':
                    busy = self._outlook_get_free_busy(integration, start_time, end_time)
                else:
                    continue
                busy_times.extend(busy)
            except Exception as e:
                logger.error(f"Free/busy check failed for integration {integration.id}: {e}")

        return busy_times

    def _google_get_free_busy(
        self,
        integration: CalendarIntegration,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get free/busy from Google Calendar"""
        response = requests.post(
            f"{GOOGLE_CALENDAR_API}/freeBusy",
            headers={
                'Authorization': f'Bearer {integration.access_token}',
                'Content-Type': 'application/json'
            },
            json={
                'timeMin': start_time.isoformat() + 'Z',
                'timeMax': end_time.isoformat() + 'Z',
                'items': [{'id': integration.calendar_id or 'primary'}]
            }
        )

        if response.status_code != 200:
            return []

        data = response.json()
        calendars = data.get('calendars', {})
        calendar_data = calendars.get(integration.calendar_id or 'primary', {})

        return [
            {
                'start': busy.get('start'),
                'end': busy.get('end'),
                'provider': 'google'
            }
            for busy in calendar_data.get('busy', [])
        ]

    def _outlook_get_free_busy(
        self,
        integration: CalendarIntegration,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get free/busy from Outlook Calendar"""
        # Use calendarView to get events in time range
        params = {
            'startDateTime': start_time.isoformat() + 'Z',
            'endDateTime': end_time.isoformat() + 'Z',
            '$select': 'start,end,showAs'
        }
        url = f"{OUTLOOK_GRAPH_API}/me/calendars/{integration.calendar_id}/calendarView"
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {integration.access_token}'},
            params=params
        )

        if response.status_code != 200:
            return []

        data = response.json()
        return [
            {
                'start': event.get('start', {}).get('dateTime'),
                'end': event.get('end', {}).get('dateTime'),
                'provider': 'outlook'
            }
            for event in data.get('value', [])
            if event.get('showAs') in ('busy', 'tentative', 'oof')
        ]

    def is_time_available(
        self,
        staff_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Check if a specific time slot is available"""
        busy_times = self.get_free_busy(staff_id, start_time, end_time)

        for busy in busy_times:
            busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
            busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))

            # Check for overlap
            if start_time < busy_end and end_time > busy_start:
                return False

        return True

    # ==================== Event Sync ====================

    def sync_booking_to_calendar(self, booking: Booking) -> Optional[CalendarEvent]:
        """Sync a booking to the staff's connected calendar"""
        slot = booking.slot
        if not slot or not slot.staff_id:
            return None

        integration = self.get_integration(slot.staff_id)
        if not integration or not integration.sync_enabled:
            return None

        if not self.refresh_tokens(integration):
            return None

        # Build event details
        client = booking.client
        event_title = f"Client Call: {client.full_name or client.email or 'Client'}"
        event_description = f"Booking type: {booking.booking_type}\n"
        if booking.notes:
            event_description += f"Notes: {booking.notes}\n"
        event_description += f"\nBooked via Brightpath Ascend"

        start_datetime = datetime.combine(slot.slot_date, slot.slot_time)
        end_datetime = start_datetime + timedelta(minutes=slot.duration_minutes)

        try:
            if integration.provider == 'google':
                external_id = self._google_create_event(
                    integration, event_title, event_description,
                    start_datetime, end_datetime
                )
            elif integration.provider == 'outlook':
                external_id = self._outlook_create_event(
                    integration, event_title, event_description,
                    start_datetime, end_datetime
                )
            else:
                return None

            # Create calendar event record
            calendar_event = CalendarEvent(
                integration_id=integration.id,
                external_event_id=external_id,
                booking_id=booking.id,
                title=event_title,
                description=event_description,
                start_time=start_datetime,
                end_time=end_datetime,
                status='confirmed',
                sync_status='synced'
            )
            self.db.add(calendar_event)
            self.db.commit()

            logger.info(f"Booking {booking.id} synced to {integration.provider} calendar")
            return calendar_event

        except Exception as e:
            logger.error(f"Failed to sync booking {booking.id}: {e}")
            return None

    def _google_create_event(
        self,
        integration: CalendarIntegration,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime
    ) -> str:
        """Create event in Google Calendar"""
        event_data = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC'
            },
            'reminders': {
                'useDefault': True
            }
        }

        response = requests.post(
            f"{GOOGLE_CALENDAR_API}/calendars/{integration.calendar_id or 'primary'}/events",
            headers={
                'Authorization': f'Bearer {integration.access_token}',
                'Content-Type': 'application/json'
            },
            json=event_data
        )

        if response.status_code not in (200, 201):
            raise Exception(f"Google event creation failed: {response.text}")

        return response.json().get('id')

    def _outlook_create_event(
        self,
        integration: CalendarIntegration,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime
    ) -> str:
        """Create event in Outlook Calendar"""
        event_data = {
            'subject': title,
            'body': {
                'contentType': 'text',
                'content': description
            },
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC'
            }
        }

        url = f"{OUTLOOK_GRAPH_API}/me/calendars/{integration.calendar_id}/events"
        response = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {integration.access_token}',
                'Content-Type': 'application/json'
            },
            json=event_data
        )

        if response.status_code not in (200, 201):
            raise Exception(f"Outlook event creation failed: {response.text}")

        return response.json().get('id')

    def delete_calendar_event(self, booking_id: int) -> bool:
        """Delete calendar event when booking is cancelled"""
        calendar_event = self.db.query(CalendarEvent).filter_by(booking_id=booking_id).first()
        if not calendar_event:
            return True  # Nothing to delete

        integration = calendar_event.integration
        if not integration or not self.refresh_tokens(integration):
            return False

        try:
            if integration.provider == 'google':
                response = requests.delete(
                    f"{GOOGLE_CALENDAR_API}/calendars/{integration.calendar_id or 'primary'}/events/{calendar_event.external_event_id}",
                    headers={'Authorization': f'Bearer {integration.access_token}'}
                )
            elif integration.provider == 'outlook':
                response = requests.delete(
                    f"{OUTLOOK_GRAPH_API}/me/calendars/{integration.calendar_id}/events/{calendar_event.external_event_id}",
                    headers={'Authorization': f'Bearer {integration.access_token}'}
                )
            else:
                return False

            if response.status_code in (200, 204, 404):  # 404 means already deleted
                calendar_event.sync_status = 'deleted'
                self.db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete calendar event: {e}")
            return False

    # ==================== Sync Status ====================

    def update_sync_status(
        self,
        integration: CalendarIntegration,
        status: str,
        error: Optional[str] = None
    ):
        """Update the last sync status"""
        integration.last_sync_at = datetime.utcnow()
        integration.last_sync_status = status
        integration.last_sync_error = error
        self.db.commit()

    def get_sync_stats(self, staff_id: int) -> Dict:
        """Get calendar sync statistics for staff"""
        integrations = self.get_integrations(staff_id)

        stats = {
            'total_integrations': len(integrations),
            'active_integrations': sum(1 for i in integrations if i.is_active),
            'providers': {},
        }

        for integration in integrations:
            provider_stat = {
                'connected': integration.is_active,
                'calendar_name': integration.calendar_name,
                'last_sync': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                'last_status': integration.last_sync_status,
                'sync_enabled': integration.sync_enabled,
            }
            stats['providers'][integration.provider] = provider_stat

        return stats


# Singleton instance
_calendar_service = None


def get_calendar_service() -> CalendarSyncService:
    """Get singleton CalendarSyncService instance"""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarSyncService()
    return _calendar_service
