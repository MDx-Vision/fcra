"""
Email Open/Click Tracking Service.

Provides:
- Tracking pixel generation for open tracking
- Link rewriting for click tracking
- Open/click event recording
- Email engagement statistics
"""

import hashlib
import os
import re
from datetime import datetime, timedelta
from urllib.parse import quote, unquote

from sqlalchemy import func, desc


# 1x1 transparent GIF pixel (43 bytes)
TRACKING_PIXEL = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00'
    b'\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21'
    b'\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
    b'\x01\x00\x3b'
)


def generate_tracking_id():
    """Generate a unique tracking ID."""
    return hashlib.sha256(os.urandom(32)).hexdigest()


class EmailTrackingService:
    """Service for tracking email opens and clicks."""

    def __init__(self, db_session=None):
        self._db = db_session
        self._owns_session = db_session is None

    def _get_db(self):
        if self._db is None:
            from database import get_db
            self._db = get_db()
        return self._db

    def _should_close_db(self):
        return self._owns_session

    def close(self):
        if self._should_close_db() and self._db is not None:
            try:
                self._db.close()
            except Exception:
                pass
            self._db = None

    # =========================================================================
    # Tracking ID Management
    # =========================================================================

    def create_tracking_id(self, email_log_id):
        """Assign a tracking ID to an email log entry."""
        try:
            db = self._get_db()
            from database import EmailLog
            email_log = db.query(EmailLog).filter(EmailLog.id == email_log_id).first()
            if not email_log:
                return {"success": False, "error": "Email log not found"}

            if email_log.tracking_id:
                return {"success": True, "tracking_id": email_log.tracking_id}

            tracking_id = generate_tracking_id()
            email_log.tracking_id = tracking_id
            db.commit()
            return {"success": True, "tracking_id": tracking_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # HTML Injection
    # =========================================================================

    def inject_tracking(self, html_content, tracking_id, base_url):
        """
        Inject tracking pixel and rewrite links in HTML email content.

        Args:
            html_content: Original HTML email content
            tracking_id: Unique tracking ID for this email
            base_url: Base URL for tracking endpoints (e.g. https://app.example.com)

        Returns:
            Modified HTML with tracking pixel and rewritten links
        """
        if not html_content or not tracking_id:
            return html_content

        # Rewrite links for click tracking
        html_content = self._rewrite_links(html_content, tracking_id, base_url)

        # Inject tracking pixel before </body> or at end
        pixel_url = f"{base_url}/api/email/track/open/{tracking_id}"
        pixel_tag = f'<img src="{pixel_url}" width="1" height="1" style="display:none" alt="" />'

        if "</body>" in html_content.lower():
            html_content = re.sub(
                r"</body>",
                f"{pixel_tag}</body>",
                html_content,
                flags=re.IGNORECASE,
            )
        else:
            html_content += pixel_tag

        return html_content

    def _rewrite_links(self, html_content, tracking_id, base_url):
        """Rewrite <a href="..."> links for click tracking."""
        def replace_link(match):
            original_url = match.group(1)
            # Skip mailto, tel, and anchor links
            if original_url.startswith(("mailto:", "tel:", "#", "javascript:")):
                return match.group(0)
            # Skip tracking pixel URL
            if "/api/email/track/" in original_url:
                return match.group(0)
            encoded_url = quote(original_url, safe="")
            tracked_url = f"{base_url}/api/email/track/click/{tracking_id}?url={encoded_url}"
            return match.group(0).replace(original_url, tracked_url)

        return re.sub(r'href=["\']([^"\']+)["\']', replace_link, html_content)

    # =========================================================================
    # Event Recording
    # =========================================================================

    def record_open(self, tracking_id, user_agent=None, ip_address=None):
        """Record an email open event."""
        try:
            db = self._get_db()
            from database import EmailLog
            email_log = db.query(EmailLog).filter(
                EmailLog.tracking_id == tracking_id
            ).first()

            if not email_log:
                return {"success": False, "error": "Tracking ID not found"}

            now = datetime.utcnow()
            if email_log.opened_at is None:
                email_log.opened_at = now
            email_log.open_count = (email_log.open_count or 0) + 1
            db.commit()

            return {"success": True, "open_count": email_log.open_count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def record_click(self, tracking_id, original_url, user_agent=None, ip_address=None):
        """Record a link click event."""
        try:
            db = self._get_db()
            from database import EmailLog, EmailClickLog

            email_log = db.query(EmailLog).filter(
                EmailLog.tracking_id == tracking_id
            ).first()

            if not email_log:
                return {"success": False, "error": "Tracking ID not found"}

            now = datetime.utcnow()
            if email_log.clicked_at is None:
                email_log.clicked_at = now
            email_log.click_count = (email_log.click_count or 0) + 1

            # Log individual click
            click_log = EmailClickLog(
                email_log_id=email_log.id,
                tracking_id=tracking_id,
                original_url=original_url,
                clicked_at=now,
                user_agent=user_agent,
                ip_address=ip_address,
            )
            db.add(click_log)
            db.commit()

            return {"success": True, "click_count": email_log.click_count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_email_stats(self, email_log_id):
        """Get tracking stats for a specific email."""
        try:
            db = self._get_db()
            from database import EmailLog, EmailClickLog

            email_log = db.query(EmailLog).filter(EmailLog.id == email_log_id).first()
            if not email_log:
                return {"success": False, "error": "Email not found"}

            clicks = db.query(EmailClickLog).filter(
                EmailClickLog.email_log_id == email_log_id
            ).order_by(EmailClickLog.clicked_at.desc()).all()

            return {
                "success": True,
                "tracking_id": email_log.tracking_id,
                "opened_at": email_log.opened_at.isoformat() if email_log.opened_at else None,
                "open_count": email_log.open_count or 0,
                "clicked_at": email_log.clicked_at.isoformat() if email_log.clicked_at else None,
                "click_count": email_log.click_count or 0,
                "clicks": [
                    {
                        "url": c.original_url,
                        "clicked_at": c.clicked_at.isoformat() if c.clicked_at else None,
                        "user_agent": c.user_agent,
                        "ip_address": c.ip_address,
                    }
                    for c in clicks
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_overall_stats(self, days=30):
        """Get overall email tracking statistics."""
        try:
            db = self._get_db()
            from database import EmailLog

            since = datetime.utcnow() - timedelta(days=days)

            total_sent = db.query(func.count(EmailLog.id)).filter(
                EmailLog.sent_at >= since,
                EmailLog.status == "sent",
            ).scalar() or 0

            total_tracked = db.query(func.count(EmailLog.id)).filter(
                EmailLog.sent_at >= since,
                EmailLog.tracking_id.isnot(None),
            ).scalar() or 0

            total_opened = db.query(func.count(EmailLog.id)).filter(
                EmailLog.sent_at >= since,
                EmailLog.opened_at.isnot(None),
            ).scalar() or 0

            total_clicked = db.query(func.count(EmailLog.id)).filter(
                EmailLog.sent_at >= since,
                EmailLog.clicked_at.isnot(None),
            ).scalar() or 0

            open_rate = (total_opened / total_tracked * 100) if total_tracked > 0 else 0
            click_rate = (total_clicked / total_tracked * 100) if total_tracked > 0 else 0
            click_to_open = (total_clicked / total_opened * 100) if total_opened > 0 else 0

            # Top performing templates
            top_templates = db.query(
                EmailLog.template_type,
                func.count(EmailLog.id).label("sent"),
                func.count(EmailLog.opened_at).label("opened"),
                func.count(EmailLog.clicked_at).label("clicked"),
            ).filter(
                EmailLog.sent_at >= since,
                EmailLog.tracking_id.isnot(None),
                EmailLog.template_type.isnot(None),
            ).group_by(
                EmailLog.template_type
            ).order_by(
                desc("sent")
            ).limit(10).all()

            # Daily stats for chart
            daily_stats = db.query(
                func.date(EmailLog.sent_at).label("date"),
                func.count(EmailLog.id).label("sent"),
                func.count(EmailLog.opened_at).label("opened"),
                func.count(EmailLog.clicked_at).label("clicked"),
            ).filter(
                EmailLog.sent_at >= since,
                EmailLog.tracking_id.isnot(None),
            ).group_by(
                func.date(EmailLog.sent_at)
            ).order_by("date").all()

            return {
                "success": True,
                "period_days": days,
                "total_sent": total_sent,
                "total_tracked": total_tracked,
                "total_opened": total_opened,
                "total_clicked": total_clicked,
                "open_rate": round(open_rate, 1),
                "click_rate": round(click_rate, 1),
                "click_to_open_rate": round(click_to_open, 1),
                "top_templates": [
                    {
                        "template_type": t[0],
                        "sent": t[1],
                        "opened": t[2],
                        "clicked": t[3],
                        "open_rate": round(t[2] / t[1] * 100, 1) if t[1] > 0 else 0,
                    }
                    for t in top_templates
                ],
                "daily_stats": [
                    {
                        "date": str(d[0]),
                        "sent": d[1],
                        "opened": d[2],
                        "clicked": d[3],
                    }
                    for d in daily_stats
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_recent_emails(self, page=1, per_page=50):
        """Get recent tracked emails with their stats."""
        try:
            db = self._get_db()
            from database import EmailLog

            total = db.query(func.count(EmailLog.id)).filter(
                EmailLog.tracking_id.isnot(None)
            ).scalar() or 0

            emails = db.query(EmailLog).filter(
                EmailLog.tracking_id.isnot(None)
            ).order_by(
                EmailLog.sent_at.desc()
            ).offset((page - 1) * per_page).limit(per_page).all()

            return {
                "success": True,
                "total": total,
                "page": page,
                "per_page": per_page,
                "emails": [
                    {
                        "id": e.id,
                        "email_address": e.email_address,
                        "subject": e.subject,
                        "template_type": e.template_type,
                        "status": e.status,
                        "sent_at": e.sent_at.isoformat() if e.sent_at else None,
                        "tracking_id": e.tracking_id,
                        "opened_at": e.opened_at.isoformat() if e.opened_at else None,
                        "open_count": e.open_count or 0,
                        "clicked_at": e.clicked_at.isoformat() if e.clicked_at else None,
                        "click_count": e.click_count or 0,
                    }
                    for e in emails
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Module-level singleton
_service_instance = None


def get_email_tracking_service():
    """Get singleton instance of EmailTrackingService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = EmailTrackingService()
    return _service_instance
