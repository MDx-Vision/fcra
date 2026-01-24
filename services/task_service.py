"""
Task Assignment Service

Manages staff task assignment, tracking, and completion.
Supports recurring tasks, priorities, categories, and comments.
"""

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session


class TaskService:
    """Service for managing staff tasks"""

    # Task categories
    CATEGORIES = [
        "general",  # General tasks
        "follow_up",  # Follow-up with client
        "document",  # Document review/processing
        "call",  # Make a call
        "review",  # Review case/analysis
        "dispute",  # Dispute-related task
        "payment",  # Payment-related task
        "onboarding",  # Client onboarding
        "other",  # Other
    ]

    # Task priorities
    PRIORITIES = ["low", "medium", "high", "urgent"]

    # Task statuses
    STATUSES = ["pending", "in_progress", "completed", "cancelled"]

    # Recurrence patterns
    RECURRENCE_PATTERNS = ["daily", "weekly", "biweekly", "monthly"]

    def __init__(self, db: Session):
        self.db = db

    def create_task(
        self,
        assigned_to_id: int,
        title: str,
        assigned_by_id: Optional[int] = None,
        client_id: Optional[int] = None,
        description: Optional[str] = None,
        category: str = "general",
        priority: str = "medium",
        due_date: Optional[date] = None,
        due_time: Optional[time] = None,
        reminder_at: Optional[datetime] = None,
        is_recurring: bool = False,
        recurrence_pattern: Optional[str] = None,
        recurrence_end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a new task.

        Args:
            assigned_to_id: Staff member to assign the task to
            title: Task title
            assigned_by_id: Staff member who created the task
            client_id: Optional client the task relates to
            description: Detailed task description
            category: Task category
            priority: Task priority (low, medium, high, urgent)
            due_date: Due date
            due_time: Specific due time
            reminder_at: When to send reminder
            is_recurring: Whether task repeats
            recurrence_pattern: How often (daily, weekly, monthly)
            recurrence_end_date: When recurrence stops

        Returns:
            Dict with success status and task data
        """
        from database import Client, Staff
        from database import StaffTask as Task

        # Validate assigned_to exists
        assigned_to = self.db.query(Staff).filter_by(id=assigned_to_id).first()
        if not assigned_to:
            return {"success": False, "error": "Assigned staff member not found"}

        # Validate client if provided
        if client_id:
            client = self.db.query(Client).filter_by(id=client_id).first()
            if not client:
                return {"success": False, "error": "Client not found"}

        # Validate category
        if category not in self.CATEGORIES:
            return {
                "success": False,
                "error": f"Invalid category. Must be one of: {self.CATEGORIES}",
            }

        # Validate priority
        if priority not in self.PRIORITIES:
            return {
                "success": False,
                "error": f"Invalid priority. Must be one of: {self.PRIORITIES}",
            }

        # Validate recurrence
        if is_recurring and recurrence_pattern not in self.RECURRENCE_PATTERNS:
            return {
                "success": False,
                "error": f"Invalid recurrence pattern. Must be one of: {self.RECURRENCE_PATTERNS}",
            }

        try:
            task = Task(
                assigned_to_id=assigned_to_id,
                assigned_by_id=assigned_by_id,
                client_id=client_id,
                title=title,
                description=description,
                category=category,
                priority=priority,
                status="pending",
                due_date=due_date,
                due_time=due_time,
                reminder_at=reminder_at,
                is_recurring=is_recurring,
                recurrence_pattern=recurrence_pattern if is_recurring else None,
                recurrence_end_date=recurrence_end_date if is_recurring else None,
            )

            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            return {
                "success": True,
                "task_id": task.id,
                "task": self._serialize_task(task),
            }

        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def update_task(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update a task.

        Args:
            task_id: ID of the task to update
            **kwargs: Fields to update

        Returns:
            Dict with success status and updated task
        """
        from database import StaffTask as Task

        task = self.db.query(Task).filter_by(id=task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}

        allowed_fields = [
            "assigned_to_id",
            "client_id",
            "title",
            "description",
            "category",
            "priority",
            "status",
            "due_date",
            "due_time",
            "reminder_at",
            "is_recurring",
            "recurrence_pattern",
            "recurrence_end_date",
        ]

        try:
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(task, field, value)

            task.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(task)

            return {"success": True, "task": self._serialize_task(task)}

        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def complete_task(
        self, task_id: int, completed_by_id: int, completion_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a task as completed.

        Args:
            task_id: ID of the task to complete
            completed_by_id: Staff member who completed it
            completion_notes: Optional completion notes

        Returns:
            Dict with success status
        """
        from database import StaffTask as Task

        task = self.db.query(Task).filter_by(id=task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}

        try:
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.completed_by_id = completed_by_id
            task.completion_notes = completion_notes
            task.updated_at = datetime.utcnow()

            # Create next recurring task if applicable
            next_task = None
            if task.is_recurring and task.recurrence_pattern:
                next_task = self._create_next_recurring_task(task)

            self.db.commit()

            result = {
                "success": True,
                "message": "Task completed",
                "task": self._serialize_task(task),
            }

            if next_task:
                result["next_recurring_task_id"] = next_task.id

            return result

        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def _create_next_recurring_task(self, completed_task) -> Optional[Any]:
        """Create the next instance of a recurring task."""
        from database import StaffTask as Task

        if not completed_task.due_date:
            return None

        # Calculate next due date
        if completed_task.recurrence_pattern == "daily":
            next_due = completed_task.due_date + timedelta(days=1)
        elif completed_task.recurrence_pattern == "weekly":
            next_due = completed_task.due_date + timedelta(weeks=1)
        elif completed_task.recurrence_pattern == "biweekly":
            next_due = completed_task.due_date + timedelta(weeks=2)
        elif completed_task.recurrence_pattern == "monthly":
            # Add approximately one month
            next_due = completed_task.due_date + timedelta(days=30)
        else:
            return None

        # Check if past recurrence end date
        if (
            completed_task.recurrence_end_date
            and next_due > completed_task.recurrence_end_date
        ):
            return None

        # Create the next task
        next_task = Task(
            assigned_to_id=completed_task.assigned_to_id,
            assigned_by_id=completed_task.assigned_by_id,
            client_id=completed_task.client_id,
            title=completed_task.title,
            description=completed_task.description,
            category=completed_task.category,
            priority=completed_task.priority,
            status="pending",
            due_date=next_due,
            due_time=completed_task.due_time,
            is_recurring=True,
            recurrence_pattern=completed_task.recurrence_pattern,
            recurrence_end_date=completed_task.recurrence_end_date,
            parent_task_id=completed_task.parent_task_id or completed_task.id,
        )

        self.db.add(next_task)
        return next_task

    def cancel_task(self, task_id: int) -> Dict[str, Any]:
        """Cancel a task."""
        from database import StaffTask as Task

        task = self.db.query(Task).filter_by(id=task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}

        task.status = "cancelled"
        task.updated_at = datetime.utcnow()
        self.db.commit()

        return {"success": True, "message": "Task cancelled"}

    def delete_task(self, task_id: int) -> Dict[str, Any]:
        """Delete a task."""
        from database import StaffTask as Task
        from database import StaffTaskComment as TaskComment

        task = self.db.query(Task).filter_by(id=task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}

        try:
            # Delete comments first
            self.db.query(TaskComment).filter_by(task_id=task_id).delete()
            self.db.delete(task)
            self.db.commit()
            return {"success": True, "message": "Task deleted"}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a single task by ID."""
        from database import StaffTask as Task

        task = self.db.query(Task).filter_by(id=task_id).first()
        if not task:
            return None
        return self._serialize_task(task, include_comments=True)

    def get_tasks(
        self,
        assigned_to_id: Optional[int] = None,
        assigned_by_id: Optional[int] = None,
        client_id: Optional[int] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        due_date_from: Optional[date] = None,
        due_date_to: Optional[date] = None,
        overdue_only: bool = False,
        search: Optional[str] = None,
        sort_by: str = "due_date",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get tasks with filtering and sorting.

        Args:
            assigned_to_id: Filter by assignee
            assigned_by_id: Filter by creator
            client_id: Filter by client
            category: Filter by category
            priority: Filter by priority
            status: Filter by status
            due_date_from: Filter by due date start
            due_date_to: Filter by due date end
            overdue_only: Only show overdue tasks
            search: Search in title and description
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            limit: Max results
            offset: Pagination offset

        Returns:
            Dict with tasks and pagination info
        """
        from database import StaffTask as Task

        query = self.db.query(Task)

        # Apply filters
        if assigned_to_id:
            query = query.filter(Task.assigned_to_id == assigned_to_id)
        if assigned_by_id:
            query = query.filter(Task.assigned_by_id == assigned_by_id)
        if client_id:
            query = query.filter(Task.client_id == client_id)
        if category:
            query = query.filter(Task.category == category)
        if priority:
            query = query.filter(Task.priority == priority)
        if status:
            query = query.filter(Task.status == status)
        if due_date_from:
            query = query.filter(Task.due_date >= due_date_from)
        if due_date_to:
            query = query.filter(Task.due_date <= due_date_to)
        if overdue_only:
            query = query.filter(
                Task.due_date < date.today(),
                Task.status.in_(["pending", "in_progress"]),
            )
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(Task.title.ilike(search_term), Task.description.ilike(search_term))
            )

        # Get total count
        total = query.count()

        # Apply sorting
        sort_column = getattr(Task, sort_by, Task.due_date)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column).nullslast())
        else:
            query = query.order_by(asc(sort_column).nullsfirst())

        # Apply pagination
        tasks = query.offset(offset).limit(limit).all()

        return {
            "tasks": [self._serialize_task(t) for t in tasks],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": total > offset + limit,
        }

    def get_my_tasks(
        self, staff_id: int, include_completed: bool = False
    ) -> Dict[str, Any]:
        """Get tasks assigned to a staff member grouped by status."""
        from database import StaffTask as Task

        query = self.db.query(Task).filter(Task.assigned_to_id == staff_id)

        if not include_completed:
            query = query.filter(Task.status.in_(["pending", "in_progress"]))

        tasks = query.order_by(
            # Order by priority (urgent first), then due date
            asc(
                func.case(
                    (Task.priority == "urgent", 0),
                    (Task.priority == "high", 1),
                    (Task.priority == "medium", 2),
                    (Task.priority == "low", 3),
                    else_=4,
                )
            ),
            asc(Task.due_date).nullslast(),
        ).all()

        # Group by status
        grouped = {
            "overdue": [],
            "today": [],
            "upcoming": [],
            "no_due_date": [],
            "in_progress": [],
            "completed": [],
        }

        today = date.today()
        for task in tasks:
            serialized = self._serialize_task(task)

            if task.status == "completed":
                grouped["completed"].append(serialized)
            elif task.status == "in_progress":
                grouped["in_progress"].append(serialized)
            elif task.due_date is None:
                grouped["no_due_date"].append(serialized)
            elif task.due_date < today:
                grouped["overdue"].append(serialized)
            elif task.due_date == today:
                grouped["today"].append(serialized)
            else:
                grouped["upcoming"].append(serialized)

        return {
            "tasks": grouped,
            "counts": {k: len(v) for k, v in grouped.items()},
            "total": len(tasks),
        }

    def get_team_workload(self) -> List[Dict[str, Any]]:
        """Get task counts per staff member."""
        from database import Staff
        from database import StaffTask as Task

        staff_list = self.db.query(Staff).filter(Staff.is_active == True).all()

        workload = []
        for staff in staff_list:
            pending = (
                self.db.query(Task)
                .filter(Task.assigned_to_id == staff.id, Task.status == "pending")
                .count()
            )

            in_progress = (
                self.db.query(Task)
                .filter(Task.assigned_to_id == staff.id, Task.status == "in_progress")
                .count()
            )

            overdue = (
                self.db.query(Task)
                .filter(
                    Task.assigned_to_id == staff.id,
                    Task.status.in_(["pending", "in_progress"]),
                    Task.due_date < date.today(),
                )
                .count()
            )

            completed_this_week = (
                self.db.query(Task)
                .filter(
                    Task.assigned_to_id == staff.id,
                    Task.status == "completed",
                    Task.completed_at >= datetime.now() - timedelta(days=7),
                )
                .count()
            )

            workload.append(
                {
                    "staff_id": staff.id,
                    "staff_name": staff.name,
                    "pending": pending,
                    "in_progress": in_progress,
                    "overdue": overdue,
                    "completed_this_week": completed_this_week,
                    "total_active": pending + in_progress,
                }
            )

        # Sort by total active tasks descending
        workload.sort(key=lambda x: x["total_active"], reverse=True)
        return workload

    def add_comment(self, task_id: int, staff_id: int, comment: str) -> Dict[str, Any]:
        """Add a comment to a task."""
        from database import StaffTask as Task
        from database import StaffTaskComment as TaskComment

        task = self.db.query(Task).filter_by(id=task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}

        try:
            task_comment = TaskComment(
                task_id=task_id, staff_id=staff_id, comment=comment
            )
            self.db.add(task_comment)
            self.db.commit()
            self.db.refresh(task_comment)

            return {
                "success": True,
                "comment": {
                    "id": task_comment.id,
                    "task_id": task_comment.task_id,
                    "staff_id": task_comment.staff_id,
                    "staff_name": (
                        task_comment.staff.name if task_comment.staff else None
                    ),
                    "comment": task_comment.comment,
                    "created_at": task_comment.created_at.isoformat(),
                },
            }
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def get_task_statistics(
        self,
        staff_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get task statistics."""
        from database import StaffTask as Task

        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()

        query = self.db.query(Task)
        if staff_id:
            query = query.filter(Task.assigned_to_id == staff_id)

        # All tasks in period
        tasks_in_period = query.filter(
            Task.created_at >= datetime.combine(date_from, time.min),
            Task.created_at <= datetime.combine(date_to, time.max),
        ).all()

        # Current active tasks
        active_tasks = query.filter(Task.status.in_(["pending", "in_progress"])).all()

        # Overdue tasks
        overdue = [t for t in active_tasks if t.due_date and t.due_date < date.today()]

        # Completed in period
        completed = [t for t in tasks_in_period if t.status == "completed"]

        # By category
        by_category = {}
        for cat in self.CATEGORIES:
            by_category[cat] = len([t for t in active_tasks if t.category == cat])

        # By priority
        by_priority = {}
        for pri in self.PRIORITIES:
            by_priority[pri] = len([t for t in active_tasks if t.priority == pri])

        return {
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "created": len(tasks_in_period),
            "completed": len(completed),
            "active": len(active_tasks),
            "overdue": len(overdue),
            "by_category": by_category,
            "by_priority": by_priority,
        }

    def get_upcoming_reminders(self, within_hours: int = 24) -> List[Dict[str, Any]]:
        """Get tasks with reminders due within specified hours."""
        from database import StaffTask as Task

        reminder_deadline = datetime.now() + timedelta(hours=within_hours)

        tasks = (
            self.db.query(Task)
            .filter(
                Task.reminder_at.isnot(None),
                Task.reminder_at <= reminder_deadline,
                Task.reminder_at >= datetime.now(),
                Task.status.in_(["pending", "in_progress"]),
            )
            .all()
        )

        return [self._serialize_task(t) for t in tasks]

    def _serialize_task(self, task, include_comments: bool = False) -> Dict[str, Any]:
        """Serialize a task to a dictionary."""
        data = {
            "id": task.id,
            "assigned_to_id": task.assigned_to_id,
            "assigned_to_name": task.assigned_to.name if task.assigned_to else None,
            "assigned_by_id": task.assigned_by_id,
            "assigned_by_name": task.assigned_by.name if task.assigned_by else None,
            "client_id": task.client_id,
            "client_name": (
                f"{task.client.first_name} {task.client.last_name}"
                if task.client
                else None
            ),
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "priority": task.priority,
            "status": task.status,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "due_time": task.due_time.isoformat() if task.due_time else None,
            "reminder_at": task.reminder_at.isoformat() if task.reminder_at else None,
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "completed_by_id": task.completed_by_id,
            "completed_by_name": task.completed_by.name if task.completed_by else None,
            "completion_notes": task.completion_notes,
            "is_recurring": task.is_recurring,
            "recurrence_pattern": task.recurrence_pattern,
            "recurrence_end_date": (
                task.recurrence_end_date.isoformat()
                if task.recurrence_end_date
                else None
            ),
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "is_overdue": (
                task.due_date < date.today()
                if task.due_date and task.status in ["pending", "in_progress"]
                else False
            ),
        }

        if include_comments and hasattr(task, "comments"):
            data["comments"] = [
                {
                    "id": c.id,
                    "staff_id": c.staff_id,
                    "staff_name": c.staff.name if c.staff else None,
                    "comment": c.comment,
                    "created_at": c.created_at.isoformat(),
                }
                for c in sorted(task.comments, key=lambda x: x.created_at)
            ]

        return data


def get_task_service(db: Session) -> TaskService:
    """Factory function to get a TaskService instance."""
    return TaskService(db)
