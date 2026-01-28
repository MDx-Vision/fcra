"""
Load Testing Suite for FCRA Platform.

Simulates realistic user flows:
- Staff dashboard browsing
- Client portal access
- API endpoint usage
- Lead capture / signup
- Document operations

Run with:
    locust -f load_tests/locustfile.py --host http://localhost:5001

Or headless:
    locust -f load_tests/locustfile.py --host http://localhost:5001 \
        --headless -u 50 -r 5 --run-time 5m
"""

import random
import string

from locust import HttpUser, TaskSet, between, tag, task


def random_email():
    """Generate a random email for testing."""
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"loadtest_{rand}@example.com"


# =============================================================================
# Staff Dashboard User
# =============================================================================


class StaffBehavior(TaskSet):
    """Simulates a staff member using the dashboard."""

    def on_start(self):
        """Login as staff."""
        self.client.post(
            "/api/staff/login",
            json={"email": "test@example.com", "password": "testpass123"},
            name="/api/staff/login",
        )

    @tag("dashboard")
    @task(10)
    def view_dashboard(self):
        self.client.get("/dashboard", name="/dashboard")

    @tag("clients")
    @task(8)
    def view_clients(self):
        self.client.get("/dashboard/clients", name="/dashboard/clients")

    @tag("clients")
    @task(5)
    def search_clients(self):
        self.client.get(
            "/api/clients?search=test&page=1&per_page=20",
            name="/api/clients?search",
        )

    @tag("cases")
    @task(4)
    def view_cases(self):
        self.client.get("/dashboard/cases", name="/dashboard/cases")

    @tag("analytics")
    @task(3)
    def view_analytics(self):
        self.client.get("/dashboard/analytics", name="/dashboard/analytics")

    @tag("email")
    @task(2)
    def view_email_tracking(self):
        self.client.get("/api/email-tracking/stats?days=30", name="/api/email-tracking/stats")

    @tag("tags")
    @task(2)
    def view_tags(self):
        self.client.get("/api/tags", name="/api/tags")

    @tag("tasks")
    @task(3)
    def view_tasks(self):
        self.client.get("/api/staff-tasks/my-tasks", name="/api/staff-tasks/my-tasks")

    @tag("messages")
    @task(2)
    def check_messages(self):
        self.client.get("/api/messages/unread-total", name="/api/messages/unread-total")

    @tag("call-logs")
    @task(2)
    def view_call_logs(self):
        self.client.get("/api/call-logs?page=1&per_page=20", name="/api/call-logs")

    @tag("revenue")
    @task(1)
    def view_revenue(self):
        self.client.get("/api/revenue/summary", name="/api/revenue/summary")

    @tag("health")
    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")


class StaffUser(HttpUser):
    """Staff user simulation."""
    tasks = [StaffBehavior]
    wait_time = between(1, 5)
    weight = 3  # Most common user type


# =============================================================================
# Client Portal User
# =============================================================================


class PortalBehavior(TaskSet):
    """Simulates a client using the portal."""

    def on_start(self):
        """Login as client."""
        self.client.post(
            "/portal/login",
            data={"email": "testclient@example.com", "password": "test123"},
            name="/portal/login",
        )

    @tag("portal")
    @task(10)
    def view_portal_dashboard(self):
        self.client.get("/portal/dashboard", name="/portal/dashboard")

    @tag("portal")
    @task(5)
    def view_status(self):
        self.client.get("/portal/status", name="/portal/status")

    @tag("portal")
    @task(4)
    def view_documents(self):
        self.client.get("/portal/documents", name="/portal/documents")

    @tag("portal")
    @task(3)
    def view_messages(self):
        self.client.get("/portal/messages", name="/portal/messages")

    @tag("portal")
    @task(2)
    def view_timeline(self):
        self.client.get("/portal/timeline", name="/portal/timeline")

    @tag("portal")
    @task(2)
    def view_profile(self):
        self.client.get("/portal/profile", name="/portal/profile")

    @tag("portal")
    @task(1)
    def view_bookings(self):
        self.client.get("/portal/booking", name="/portal/booking")

    @tag("portal")
    @task(1)
    def check_unread(self):
        self.client.get("/api/portal/messages/unread-count", name="/api/portal/messages/unread-count")


class PortalUser(HttpUser):
    """Client portal user simulation."""
    tasks = [PortalBehavior]
    wait_time = between(2, 8)
    weight = 2


# =============================================================================
# API-Heavy User (Integrations / Automations)
# =============================================================================


class APIBehavior(TaskSet):
    """Simulates API-heavy usage (integrations, automations)."""

    def on_start(self):
        self.client.post(
            "/api/staff/login",
            json={"email": "test@example.com", "password": "testpass123"},
            name="/api/staff/login",
        )

    @tag("api")
    @task(5)
    def get_clients_list(self):
        self.client.get("/api/clients?page=1&per_page=50", name="/api/clients")

    @tag("api")
    @task(3)
    def get_tag_stats(self):
        self.client.get("/api/tags/stats", name="/api/tags/stats")

    @tag("api")
    @task(3)
    def get_backups(self):
        self.client.get("/api/backups", name="/api/backups")

    @tag("api")
    @task(2)
    def get_workflow_triggers(self):
        self.client.get("/api/workflow-triggers", name="/api/workflow-triggers")

    @tag("api")
    @task(2)
    def get_booking_slots(self):
        self.client.get("/api/booking-slots", name="/api/booking-slots")

    @tag("api")
    @task(1)
    def get_feature_flags(self):
        self.client.get("/api/feature-flags", name="/api/feature-flags")

    @tag("health")
    @task(1)
    def readiness_check(self):
        self.client.get("/ready", name="/ready")


class APIUser(HttpUser):
    """API integration user simulation."""
    tasks = [APIBehavior]
    wait_time = between(0.5, 2)
    weight = 1


# =============================================================================
# Lead Capture (Anonymous)
# =============================================================================


class LeadCaptureBehavior(TaskSet):
    """Simulates anonymous visitors hitting the signup page."""

    @tag("public")
    @task(10)
    def view_signup(self):
        self.client.get("/get-started", name="/get-started")

    @tag("public")
    @task(5)
    def view_upload_report(self):
        self.client.get("/upload-report", name="/upload-report")

    @tag("public")
    @task(2)
    def submit_lead(self):
        self.client.post(
            "/api/leads/capture",
            json={
                "first_name": "Load",
                "last_name": "Test",
                "email": random_email(),
                "phone": "555-0000",
            },
            name="/api/leads/capture",
        )

    @tag("health")
    @task(1)
    def health(self):
        self.client.get("/health", name="/health")


class LeadUser(HttpUser):
    """Anonymous visitor simulation."""
    tasks = [LeadCaptureBehavior]
    wait_time = between(3, 10)
    weight = 2
