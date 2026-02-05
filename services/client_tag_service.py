"""
Client Tag Service

Manages client tags for flexible client segmentation and organization.
Provides CRUD operations for tags and tag assignments.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Client, ClientTag, ClientTagAssignment, SessionLocal

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Predefined tag colors for quick selection
TAG_COLORS = [
    {"name": "Indigo", "color": "#6366f1"},
    {"name": "Blue", "color": "#3b82f6"},
    {"name": "Green", "color": "#22c55e"},
    {"name": "Yellow", "color": "#eab308"},
    {"name": "Orange", "color": "#f97316"},
    {"name": "Red", "color": "#ef4444"},
    {"name": "Pink", "color": "#ec4899"},
    {"name": "Purple", "color": "#a855f7"},
    {"name": "Teal", "color": "#14b8a6"},
    {"name": "Gray", "color": "#6b7280"},
]

# Default tags that can be seeded
DEFAULT_TAGS = [
    {"name": "VIP", "color": "#eab308"},
    {"name": "Priority", "color": "#ef4444"},
    {"name": "New Client", "color": "#22c55e"},
    {"name": "Needs Follow-up", "color": "#f97316"},
    {"name": "Payment Issue", "color": "#ec4899"},
    {"name": "Identity Theft", "color": "#a855f7"},
    {"name": "Litigation Ready", "color": "#3b82f6"},
    {"name": "Settlement Pending", "color": "#14b8a6"},
]


# =============================================================================
# Service Class
# =============================================================================


class ClientTagService:
    """Service for managing client tags and assignments."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize with optional database session."""
        self._db = db_session
        self._owns_session = db_session is None

    def _get_db(self) -> Session:
        """Get or create database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def _should_close_db(self) -> bool:
        """Check if we should close the database session."""
        return self._owns_session

    def close(self):
        """Close database session if we own it."""
        if self._should_close_db() and self._db:
            self._db.close()
            self._db = None

    # =========================================================================
    # Tag CRUD Operations
    # =========================================================================

    def create_tag(
        self,
        name: str,
        color: str = "#6366f1",
    ) -> Dict[str, Any]:
        """
        Create a new client tag.

        Args:
            name: Tag name (must be unique)
            color: Hex color code for the tag

        Returns:
            Dict with success status and tag data or error message
        """
        db = self._get_db()
        try:
            # Validate inputs
            if not name or not name.strip():
                return {"success": False, "error": "Tag name is required"}

            name = name.strip()

            # Check for duplicate name
            existing = (
                db.query(ClientTag)
                .filter(func.lower(ClientTag.name) == name.lower())
                .first()
            )
            if existing:
                return {"success": False, "error": f"Tag '{name}' already exists"}

            # Validate color format
            if not color.startswith("#") or len(color) != 7:
                color = "#6366f1"  # Default to indigo if invalid

            # Create tag
            tag = ClientTag(
                name=name,
                color=color,
            )
            db.add(tag)
            db.commit()
            db.refresh(tag)

            logger.info(f"Created tag: {name} (ID: {tag.id})")

            return {
                "success": True,
                "tag": self._tag_to_dict(tag),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating tag: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self._should_close_db():
                db.close()

    def get_tag(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a tag by ID.

        Args:
            tag_id: Tag ID

        Returns:
            Tag dict or None if not found
        """
        db = self._get_db()
        try:
            tag = db.query(ClientTag).filter(ClientTag.id == tag_id).first()
            if tag:
                return self._tag_to_dict(tag, db)
            return None
        finally:
            if self._should_close_db():
                db.close()

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags with client counts.

        Returns:
            List of tag dicts with client counts
        """
        db = self._get_db()
        try:
            tags = db.query(ClientTag).order_by(ClientTag.name).all()
            return [self._tag_to_dict(tag, db) for tag in tags]
        finally:
            if self._should_close_db():
                db.close()

    def update_tag(
        self,
        tag_id: int,
        name: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a tag.

        Args:
            tag_id: Tag ID
            name: New name (optional)
            color: New color (optional)

        Returns:
            Dict with success status and updated tag or error
        """
        db = self._get_db()
        try:
            tag = db.query(ClientTag).filter(ClientTag.id == tag_id).first()
            if not tag:
                return {"success": False, "error": "Tag not found"}

            if name is not None:
                name = name.strip()
                if not name:
                    return {"success": False, "error": "Tag name cannot be empty"}

                # Check for duplicate name (excluding this tag)
                existing = (
                    db.query(ClientTag)
                    .filter(
                        func.lower(ClientTag.name) == name.lower(),
                        ClientTag.id != tag_id,
                    )
                    .first()
                )
                if existing:
                    return {"success": False, "error": f"Tag '{name}' already exists"}

                tag.name = name

            if color is not None:
                if color.startswith("#") and len(color) == 7:
                    tag.color = color

            db.commit()
            db.refresh(tag)

            logger.info(f"Updated tag ID {tag_id}")

            return {
                "success": True,
                "tag": self._tag_to_dict(tag, db),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating tag: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self._should_close_db():
                db.close()

    def delete_tag(self, tag_id: int) -> Dict[str, Any]:
        """
        Delete a tag. Also removes all assignments.

        Args:
            tag_id: Tag ID

        Returns:
            Dict with success status
        """
        db = self._get_db()
        try:
            tag = db.query(ClientTag).filter(ClientTag.id == tag_id).first()
            if not tag:
                return {"success": False, "error": "Tag not found"}

            tag_name = tag.name

            # Delete assignments first (cascade should handle this but be explicit)
            db.query(ClientTagAssignment).filter(
                ClientTagAssignment.tag_id == tag_id
            ).delete()

            # Delete tag
            db.delete(tag)
            db.commit()

            logger.info(f"Deleted tag: {tag_name} (ID: {tag_id})")

            return {"success": True, "message": f"Tag '{tag_name}' deleted"}

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting tag: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self._should_close_db():
                db.close()

    # =========================================================================
    # Tag Assignment Operations
    # =========================================================================

    def assign_tag(self, client_id: int, tag_id: int) -> Dict[str, Any]:
        """
        Assign a tag to a client.

        Args:
            client_id: Client ID
            tag_id: Tag ID

        Returns:
            Dict with success status
        """
        db = self._get_db()
        try:
            # Verify client exists
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {"success": False, "error": "Client not found"}

            # Verify tag exists
            tag = db.query(ClientTag).filter(ClientTag.id == tag_id).first()
            if not tag:
                return {"success": False, "error": "Tag not found"}

            # Check if already assigned
            existing = (
                db.query(ClientTagAssignment)
                .filter(
                    ClientTagAssignment.client_id == client_id,
                    ClientTagAssignment.tag_id == tag_id,
                )
                .first()
            )
            if existing:
                return {"success": True, "message": "Tag already assigned"}

            # Create assignment
            assignment = ClientTagAssignment(
                client_id=client_id,
                tag_id=tag_id,
            )
            db.add(assignment)
            db.commit()

            logger.info(f"Assigned tag '{tag.name}' to client {client_id}")

            return {"success": True, "message": f"Tag '{tag.name}' assigned"}

        except Exception as e:
            db.rollback()
            logger.error(f"Error assigning tag: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self._should_close_db():
                db.close()

    def remove_tag(self, client_id: int, tag_id: int) -> Dict[str, Any]:
        """
        Remove a tag from a client.

        Args:
            client_id: Client ID
            tag_id: Tag ID

        Returns:
            Dict with success status
        """
        db = self._get_db()
        try:
            assignment = (
                db.query(ClientTagAssignment)
                .filter(
                    ClientTagAssignment.client_id == client_id,
                    ClientTagAssignment.tag_id == tag_id,
                )
                .first()
            )

            if not assignment:
                return {"success": False, "error": "Tag assignment not found"}

            db.delete(assignment)
            db.commit()

            logger.info(f"Removed tag {tag_id} from client {client_id}")

            return {"success": True, "message": "Tag removed"}

        except Exception as e:
            db.rollback()
            logger.error(f"Error removing tag: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self._should_close_db():
                db.close()

    def get_client_tags(self, client_id: int) -> List[Dict[str, Any]]:
        """
        Get all tags assigned to a client.

        Args:
            client_id: Client ID

        Returns:
            List of tag dicts
        """
        db = self._get_db()
        try:
            tags = (
                db.query(ClientTag)
                .join(ClientTagAssignment, ClientTagAssignment.tag_id == ClientTag.id)
                .filter(ClientTagAssignment.client_id == client_id)
                .order_by(ClientTag.name)
                .all()
            )
            return [self._tag_to_dict(tag) for tag in tags]
        finally:
            if self._should_close_db():
                db.close()

    def set_client_tags(self, client_id: int, tag_ids: List[int]) -> Dict[str, Any]:
        """
        Set all tags for a client (replaces existing).

        Args:
            client_id: Client ID
            tag_ids: List of tag IDs to assign

        Returns:
            Dict with success status
        """
        db = self._get_db()
        try:
            # Verify client exists
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {"success": False, "error": "Client not found"}

            # Remove existing assignments
            db.query(ClientTagAssignment).filter(
                ClientTagAssignment.client_id == client_id
            ).delete()

            # Add new assignments
            for tag_id in tag_ids:
                tag = db.query(ClientTag).filter(ClientTag.id == tag_id).first()
                if tag:
                    assignment = ClientTagAssignment(
                        client_id=client_id,
                        tag_id=tag_id,
                    )
                    db.add(assignment)

            db.commit()

            logger.info(f"Set {len(tag_ids)} tags for client {client_id}")

            return {"success": True, "message": f"Assigned {len(tag_ids)} tags"}

        except Exception as e:
            db.rollback()
            logger.error(f"Error setting client tags: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self._should_close_db():
                db.close()

    # =========================================================================
    # Client Filtering by Tags
    # =========================================================================

    def get_clients_by_tag(
        self,
        tag_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get clients with a specific tag.

        Args:
            tag_id: Tag ID
            limit: Max clients to return
            offset: Offset for pagination

        Returns:
            Dict with clients and total count
        """
        db = self._get_db()
        try:
            # Get tag info
            tag = db.query(ClientTag).filter(ClientTag.id == tag_id).first()
            if not tag:
                return {"success": False, "error": "Tag not found"}

            # Count total
            total = (
                db.query(func.count(Client.id))
                .join(ClientTagAssignment, ClientTagAssignment.client_id == Client.id)
                .filter(ClientTagAssignment.tag_id == tag_id)
                .scalar()
            )

            # Get clients
            clients = (
                db.query(Client)
                .join(ClientTagAssignment, ClientTagAssignment.client_id == Client.id)
                .filter(ClientTagAssignment.tag_id == tag_id)
                .order_by(Client.last_name, Client.first_name)
                .offset(offset)
                .limit(limit)
                .all()
            )

            return {
                "success": True,
                "tag": self._tag_to_dict(tag),
                "clients": [self._client_to_dict(c) for c in clients],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        finally:
            if self._should_close_db():
                db.close()

    def get_clients_by_tags(
        self,
        tag_ids: List[int],
        match_all: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get clients with any or all of the specified tags.

        Args:
            tag_ids: List of tag IDs
            match_all: If True, client must have ALL tags; if False, client needs ANY tag
            limit: Max clients to return
            offset: Offset for pagination

        Returns:
            Dict with clients and total count
        """
        db = self._get_db()
        try:
            if not tag_ids:
                return {"success": False, "error": "No tag IDs provided"}

            if match_all:
                # Client must have ALL specified tags
                # Use HAVING COUNT to match all tags
                subquery = (
                    db.query(ClientTagAssignment.client_id)
                    .filter(ClientTagAssignment.tag_id.in_(tag_ids))
                    .group_by(ClientTagAssignment.client_id)
                    .having(func.count(ClientTagAssignment.tag_id) == len(tag_ids))
                    .subquery()
                )
                query = db.query(Client).filter(Client.id.in_(subquery))
            else:
                # Client needs ANY of the tags
                client_ids = (
                    db.query(ClientTagAssignment.client_id)
                    .filter(ClientTagAssignment.tag_id.in_(tag_ids))
                    .distinct()
                    .subquery()
                )
                query = db.query(Client).filter(Client.id.in_(client_ids))

            # Get total
            total = query.count()

            # Get clients
            clients = (
                query.order_by(Client.last_name, Client.first_name)
                .offset(offset)
                .limit(limit)
                .all()
            )

            return {
                "success": True,
                "clients": [self._client_to_dict(c) for c in clients],
                "total": total,
                "limit": limit,
                "offset": offset,
                "match_all": match_all,
            }

        finally:
            if self._should_close_db():
                db.close()

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    def bulk_assign_tag(
        self,
        client_ids: List[int],
        tag_id: int,
    ) -> Dict[str, Any]:
        """
        Assign a tag to multiple clients.

        Args:
            client_ids: List of client IDs
            tag_id: Tag ID

        Returns:
            Dict with success count
        """
        db = self._get_db()
        try:
            # Verify tag exists
            tag = db.query(ClientTag).filter(ClientTag.id == tag_id).first()
            if not tag:
                return {"success": False, "error": "Tag not found"}

            assigned = 0
            skipped = 0

            for client_id in client_ids:
                # Check if already assigned
                existing = (
                    db.query(ClientTagAssignment)
                    .filter(
                        ClientTagAssignment.client_id == client_id,
                        ClientTagAssignment.tag_id == tag_id,
                    )
                    .first()
                )

                if existing:
                    skipped += 1
                else:
                    assignment = ClientTagAssignment(
                        client_id=client_id,
                        tag_id=tag_id,
                    )
                    db.add(assignment)
                    assigned += 1

            db.commit()

            logger.info(f"Bulk assigned tag '{tag.name}' to {assigned} clients")

            return {
                "success": True,
                "assigned": assigned,
                "skipped": skipped,
                "total": len(client_ids),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error in bulk assign: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self._should_close_db():
                db.close()

    def bulk_remove_tag(
        self,
        client_ids: List[int],
        tag_id: int,
    ) -> Dict[str, Any]:
        """
        Remove a tag from multiple clients.

        Args:
            client_ids: List of client IDs
            tag_id: Tag ID

        Returns:
            Dict with removal count
        """
        db = self._get_db()
        try:
            deleted = (
                db.query(ClientTagAssignment)
                .filter(
                    ClientTagAssignment.client_id.in_(client_ids),
                    ClientTagAssignment.tag_id == tag_id,
                )
                .delete(synchronize_session=False)
            )

            db.commit()

            logger.info(f"Bulk removed tag {tag_id} from {deleted} clients")

            return {
                "success": True,
                "removed": deleted,
                "total": len(client_ids),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error in bulk remove: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self._should_close_db():
                db.close()

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get tag statistics.

        Returns:
            Dict with tag usage statistics
        """
        db = self._get_db()
        try:
            total_tags = db.query(func.count(ClientTag.id)).scalar() or 0

            total_assignments = (
                db.query(func.count(ClientTagAssignment.id)).scalar() or 0
            )

            # Clients with at least one tag
            clients_with_tags = (
                db.query(
                    func.count(func.distinct(ClientTagAssignment.client_id))
                ).scalar()
                or 0
            )

            # Most used tags
            most_used = (
                db.query(
                    ClientTag.id,
                    ClientTag.name,
                    ClientTag.color,
                    func.count(ClientTagAssignment.id).label("count"),
                )
                .outerjoin(
                    ClientTagAssignment, ClientTagAssignment.tag_id == ClientTag.id
                )
                .group_by(ClientTag.id)
                .order_by(func.count(ClientTagAssignment.id).desc())
                .limit(10)
                .all()
            )

            return {
                "total_tags": total_tags,
                "total_assignments": total_assignments,
                "clients_with_tags": clients_with_tags,
                "most_used": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "color": t.color,
                        "client_count": t.count,
                    }
                    for t in most_used
                ],
            }

        finally:
            if self._should_close_db():
                db.close()

    # =========================================================================
    # Seed Default Tags
    # =========================================================================

    def seed_default_tags(self) -> Dict[str, Any]:
        """
        Seed the database with default tags.

        Returns:
            Dict with count of created tags
        """
        db = self._get_db()
        try:
            created = 0
            skipped = 0

            for tag_data in DEFAULT_TAGS:
                existing = (
                    db.query(ClientTag)
                    .filter(func.lower(ClientTag.name) == tag_data["name"].lower())
                    .first()
                )

                if existing:
                    skipped += 1
                else:
                    tag = ClientTag(
                        name=tag_data["name"],
                        color=tag_data["color"],
                    )
                    db.add(tag)
                    created += 1

            db.commit()

            logger.info(f"Seeded {created} default tags, skipped {skipped} existing")

            return {
                "success": True,
                "created": created,
                "skipped": skipped,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error seeding tags: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self._should_close_db():
                db.close()

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _tag_to_dict(
        self, tag: ClientTag, db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Convert ClientTag to dictionary."""
        result = {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
        }

        # Add client count if db session available
        if db:
            count = (
                db.query(func.count(ClientTagAssignment.id))
                .filter(ClientTagAssignment.tag_id == tag.id)
                .scalar()
                or 0
            )
            result["client_count"] = count

        return result

    def _client_to_dict(self, client: Client) -> Dict[str, Any]:
        """Convert Client to minimal dictionary for tag results."""
        return {
            "id": client.id,
            "first_name": client.first_name,
            "last_name": client.last_name,
            "email": client.email,
            "phone": client.phone,
            "dispute_status": client.dispute_status,
        }


# =============================================================================
# Module-level Functions (Convenience)
# =============================================================================

_service_instance: Optional[ClientTagService] = None


def get_client_tag_service() -> ClientTagService:
    """Get singleton service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ClientTagService()
    return _service_instance


def get_available_colors() -> List[Dict[str, str]]:
    """Get list of predefined tag colors."""
    return TAG_COLORS


def get_default_tags() -> List[Dict[str, str]]:
    """Get list of default tags."""
    return DEFAULT_TAGS
