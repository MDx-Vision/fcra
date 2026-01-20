"""
Unit tests for TaskService
"""

import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import MagicMock, patch, PropertyMock


class TestTaskServiceConstants:
    """Tests for TaskService constants"""

    def test_categories_list(self):
        """Test that categories list is properly defined"""
        from services.task_service import TaskService
        assert 'general' in TaskService.CATEGORIES
        assert 'follow_up' in TaskService.CATEGORIES
        assert 'document' in TaskService.CATEGORIES
        assert 'call' in TaskService.CATEGORIES
        assert 'review' in TaskService.CATEGORIES
        assert 'dispute' in TaskService.CATEGORIES
        assert 'payment' in TaskService.CATEGORIES
        assert 'onboarding' in TaskService.CATEGORIES
        assert 'other' in TaskService.CATEGORIES
        assert len(TaskService.CATEGORIES) == 9

    def test_priorities_list(self):
        """Test that priorities list is properly defined"""
        from services.task_service import TaskService
        assert TaskService.PRIORITIES == ['low', 'medium', 'high', 'urgent']

    def test_statuses_list(self):
        """Test that statuses list is properly defined"""
        from services.task_service import TaskService
        assert TaskService.STATUSES == ['pending', 'in_progress', 'completed', 'cancelled']

    def test_recurrence_patterns_list(self):
        """Test that recurrence patterns list is properly defined"""
        from services.task_service import TaskService
        assert TaskService.RECURRENCE_PATTERNS == ['daily', 'weekly', 'biweekly', 'monthly']


class TestTaskServiceCreateTask:
    """Tests for create_task method"""

    @patch('database.StaffTask')
    @patch('database.Client')
    @patch('database.Staff')
    def test_create_task_success(self, mock_staff_class, mock_client_class, mock_task_class):
        """Test successful task creation"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        # Mock staff query
        mock_staff = MagicMock()
        mock_staff.id = 1
        mock_staff.name = "Test Staff"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        # Mock task creation
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Test Task"
        mock_task.assigned_to_id = 1
        mock_task.assigned_to = mock_staff
        mock_task.assigned_by = None
        mock_task.assigned_by_id = None
        mock_task.client_id = None
        mock_task.client = None
        mock_task.description = "Test description"
        mock_task.category = "general"
        mock_task.priority = "medium"
        mock_task.status = "pending"
        mock_task.due_date = None
        mock_task.due_time = None
        mock_task.reminder_at = None
        mock_task.completed_at = None
        mock_task.completed_by_id = None
        mock_task.completed_by = None
        mock_task.completion_notes = None
        mock_task.is_recurring = False
        mock_task.recurrence_pattern = None
        mock_task.recurrence_end_date = None
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()
        mock_task_class.return_value = mock_task

        result = service.create_task(
            assigned_to_id=1,
            title="Test Task",
            description="Test description"
        )

        assert result["success"] is True
        assert result["task_id"] == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('database.Staff')
    def test_create_task_staff_not_found(self, mock_staff_class):
        """Test task creation with invalid staff ID"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.create_task(assigned_to_id=999, title="Test Task")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @patch('database.Client')
    @patch('database.Staff')
    def test_create_task_client_not_found(self, mock_staff_class, mock_client_class):
        """Test task creation with invalid client ID"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_staff = MagicMock()
        mock_staff.id = 1

        # First call returns staff, second returns None for client
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [mock_staff, None]

        result = service.create_task(
            assigned_to_id=1,
            title="Test Task",
            client_id=999
        )

        assert result["success"] is False
        assert "client not found" in result["error"].lower()

    @patch('database.Staff')
    def test_create_task_invalid_category(self, mock_staff_class):
        """Test task creation with invalid category"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_staff = MagicMock()
        mock_staff.id = 1
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        result = service.create_task(
            assigned_to_id=1,
            title="Test Task",
            category="invalid_category"
        )

        assert result["success"] is False
        assert "invalid category" in result["error"].lower()

    @patch('database.Staff')
    def test_create_task_invalid_priority(self, mock_staff_class):
        """Test task creation with invalid priority"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_staff = MagicMock()
        mock_staff.id = 1
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        result = service.create_task(
            assigned_to_id=1,
            title="Test Task",
            priority="super_urgent"
        )

        assert result["success"] is False
        assert "invalid priority" in result["error"].lower()

    @patch('database.Staff')
    def test_create_task_invalid_recurrence_pattern(self, mock_staff_class):
        """Test task creation with invalid recurrence pattern"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_staff = MagicMock()
        mock_staff.id = 1
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        result = service.create_task(
            assigned_to_id=1,
            title="Test Task",
            is_recurring=True,
            recurrence_pattern="yearly"  # invalid
        )

        assert result["success"] is False
        assert "invalid recurrence" in result["error"].lower()


class TestTaskServiceUpdateTask:
    """Tests for update_task method"""

    @patch('database.StaffTask')
    def test_update_task_success(self, mock_task_class):
        """Test successful task update"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Updated Task"
        mock_task.assigned_to = MagicMock(name="Staff")
        mock_task.assigned_by = None
        mock_task.client = None
        mock_task.completed_by = None
        mock_task.description = None
        mock_task.category = "general"
        mock_task.priority = "high"
        mock_task.status = "pending"
        mock_task.due_date = None
        mock_task.due_time = None
        mock_task.reminder_at = None
        mock_task.completed_at = None
        mock_task.completion_notes = None
        mock_task.is_recurring = False
        mock_task.recurrence_pattern = None
        mock_task.recurrence_end_date = None
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        result = service.update_task(1, title="Updated Task", priority="high")

        assert result["success"] is True
        mock_db.commit.assert_called_once()

    @patch('database.StaffTask')
    def test_update_task_not_found(self, mock_task_class):
        """Test updating non-existent task"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.update_task(999, title="Updated Task")

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestTaskServiceCompleteTask:
    """Tests for complete_task method"""

    @patch('database.StaffTask')
    def test_complete_task_success(self, mock_task_class):
        """Test successful task completion"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Test Task"
        mock_task.status = "pending"
        mock_task.is_recurring = False
        mock_task.recurrence_pattern = None
        mock_task.assigned_to = MagicMock(name="Staff")
        mock_task.assigned_by = None
        mock_task.client = None
        mock_task.completed_by = None
        mock_task.description = None
        mock_task.category = "general"
        mock_task.priority = "medium"
        mock_task.due_date = None
        mock_task.due_time = None
        mock_task.reminder_at = None
        mock_task.completed_at = None
        mock_task.completion_notes = None
        mock_task.recurrence_end_date = None
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        result = service.complete_task(1, completed_by_id=1, completion_notes="Done!")

        assert result["success"] is True
        assert mock_task.status == "completed"
        assert mock_task.completed_at is not None
        mock_db.commit.assert_called_once()

    @patch('database.StaffTask')
    def test_complete_task_not_found(self, mock_task_class):
        """Test completing non-existent task"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.complete_task(999, completed_by_id=1)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @patch('database.StaffTask')
    def test_complete_recurring_task_creates_next(self, mock_task_class):
        """Test completing a recurring task creates the next instance"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Recurring Task"
        mock_task.status = "pending"
        mock_task.is_recurring = True
        mock_task.recurrence_pattern = "weekly"
        mock_task.due_date = date.today()
        mock_task.recurrence_end_date = date.today() + timedelta(days=30)
        mock_task.assigned_to_id = 1
        mock_task.assigned_by_id = None
        mock_task.client_id = None
        mock_task.description = "Test"
        mock_task.category = "general"
        mock_task.priority = "medium"
        mock_task.due_time = None
        mock_task.parent_task_id = None
        mock_task.assigned_to = MagicMock(name="Staff")
        mock_task.assigned_by = None
        mock_task.client = None
        mock_task.completed_by = None
        mock_task.reminder_at = None
        mock_task.completed_at = None
        mock_task.completion_notes = None
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        result = service.complete_task(1, completed_by_id=1)

        assert result["success"] is True
        # Should have added a new task
        assert mock_db.add.call_count >= 1


class TestTaskServiceCancelTask:
    """Tests for cancel_task method"""

    @patch('database.StaffTask')
    def test_cancel_task_success(self, mock_task_class):
        """Test successful task cancellation"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "pending"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        result = service.cancel_task(1)

        assert result["success"] is True
        assert mock_task.status == "cancelled"
        mock_db.commit.assert_called_once()

    @patch('database.StaffTask')
    def test_cancel_task_not_found(self, mock_task_class):
        """Test canceling non-existent task"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.cancel_task(999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestTaskServiceDeleteTask:
    """Tests for delete_task method"""

    @patch('database.StaffTaskComment')
    @patch('database.StaffTask')
    def test_delete_task_success(self, mock_task_class, mock_comment_class):
        """Test successful task deletion"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        result = service.delete_task(1)

        assert result["success"] is True
        mock_db.delete.assert_called_once_with(mock_task)
        mock_db.commit.assert_called_once()

    @patch('database.StaffTask')
    def test_delete_task_not_found(self, mock_task_class):
        """Test deleting non-existent task"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.delete_task(999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestTaskServiceGetTask:
    """Tests for get_task method"""

    @patch('database.StaffTask')
    def test_get_task_success(self, mock_task_class):
        """Test getting a task by ID"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Test Task"
        mock_task.assigned_to_id = 1
        mock_task.assigned_to = MagicMock(name="Staff")
        mock_task.assigned_by_id = None
        mock_task.assigned_by = None
        mock_task.client_id = None
        mock_task.client = None
        mock_task.description = "Test description"
        mock_task.category = "general"
        mock_task.priority = "medium"
        mock_task.status = "pending"
        mock_task.due_date = None
        mock_task.due_time = None
        mock_task.reminder_at = None
        mock_task.completed_at = None
        mock_task.completed_by_id = None
        mock_task.completed_by = None
        mock_task.completion_notes = None
        mock_task.is_recurring = False
        mock_task.recurrence_pattern = None
        mock_task.recurrence_end_date = None
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()
        mock_task.comments = []

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        result = service.get_task(1)

        assert result is not None
        assert result["id"] == 1
        assert result["title"] == "Test Task"

    @patch('database.StaffTask')
    def test_get_task_not_found(self, mock_task_class):
        """Test getting non-existent task"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.get_task(999)

        assert result is None


class TestTaskServiceGetTasks:
    """Tests for get_tasks method"""

    @patch('services.task_service.asc')
    @patch('services.task_service.desc')
    @patch('database.StaffTask')
    def test_get_tasks_no_filters(self, mock_task_class, mock_desc, mock_asc):
        """Test getting tasks without filters"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Test Task"
        mock_task.assigned_to = MagicMock(name="Staff")
        mock_task.assigned_by = None
        mock_task.client = None
        mock_task.completed_by = None
        mock_task.description = None
        mock_task.category = "general"
        mock_task.priority = "medium"
        mock_task.status = "pending"
        mock_task.due_date = None
        mock_task.due_time = None
        mock_task.reminder_at = None
        mock_task.completed_at = None
        mock_task.completion_notes = None
        mock_task.is_recurring = False
        mock_task.recurrence_pattern = None
        mock_task.recurrence_end_date = None
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()

        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_task]
        mock_db.query.return_value = mock_query

        result = service.get_tasks()

        assert "tasks" in result
        assert result["total"] == 1
        assert len(result["tasks"]) == 1

    @patch('services.task_service.asc')
    @patch('services.task_service.desc')
    @patch('database.StaffTask')
    def test_get_tasks_with_status_filter(self, mock_task_class, mock_desc, mock_asc):
        """Test getting tasks with status filter"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.get_tasks(status="completed")

        assert "tasks" in result
        mock_query.filter.assert_called()

    @patch('services.task_service.or_')
    @patch('services.task_service.asc')
    @patch('services.task_service.desc')
    @patch('database.StaffTask')
    def test_get_tasks_with_search(self, mock_task_class, mock_desc, mock_asc, mock_or):
        """Test getting tasks with search filter"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.get_tasks(search="test")

        assert "tasks" in result
        mock_query.filter.assert_called()


class TestTaskServiceGetMyTasks:
    """Tests for get_my_tasks method"""

    @patch('services.task_service.func')
    @patch('services.task_service.asc')
    @patch('database.StaffTask')
    def test_get_my_tasks(self, mock_task_class, mock_asc, mock_func):
        """Test getting tasks for a specific staff member"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        # Create mock tasks
        mock_task_pending = MagicMock()
        mock_task_pending.id = 1
        mock_task_pending.status = "pending"
        mock_task_pending.due_date = date.today() + timedelta(days=1)
        mock_task_pending.assigned_to = MagicMock(name="Staff")
        mock_task_pending.assigned_by = None
        mock_task_pending.client = None
        mock_task_pending.completed_by = None
        mock_task_pending.title = "Pending Task"
        mock_task_pending.description = None
        mock_task_pending.category = "general"
        mock_task_pending.priority = "medium"
        mock_task_pending.due_time = None
        mock_task_pending.reminder_at = None
        mock_task_pending.completed_at = None
        mock_task_pending.completion_notes = None
        mock_task_pending.is_recurring = False
        mock_task_pending.recurrence_pattern = None
        mock_task_pending.recurrence_end_date = None
        mock_task_pending.created_at = datetime.now()
        mock_task_pending.updated_at = datetime.now()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_task_pending]
        mock_db.query.return_value = mock_query

        result = service.get_my_tasks(staff_id=1)

        assert "tasks" in result
        assert "counts" in result
        assert "total" in result


class TestTaskServiceGetTeamWorkload:
    """Tests for get_team_workload method"""

    def test_get_team_workload(self):
        """Test getting team workload statistics"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        # Mock staff
        mock_staff = MagicMock()
        mock_staff.id = 1
        mock_staff.name = "Test Staff"
        mock_staff.is_active = True

        # Create a mock query that returns the staff list
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_staff]
        mock_query.count.return_value = 3

        mock_db.query.return_value = mock_query

        result = service.get_team_workload()

        assert isinstance(result, list)


class TestTaskServiceAddComment:
    """Tests for add_comment method"""

    @patch('database.StaffTaskComment')
    @patch('database.StaffTask')
    def test_add_comment_success(self, mock_task_class, mock_comment_class):
        """Test adding a comment to a task"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1

        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.task_id = 1
        mock_comment.staff_id = 1
        mock_comment.staff = MagicMock(name="Test Staff")
        mock_comment.comment = "Test comment"
        mock_comment.created_at = datetime.now()

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task
        mock_comment_class.return_value = mock_comment

        result = service.add_comment(task_id=1, staff_id=1, comment="Test comment")

        assert result["success"] is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('database.StaffTask')
    def test_add_comment_task_not_found(self, mock_task_class):
        """Test adding comment to non-existent task"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.add_comment(task_id=999, staff_id=1, comment="Test")

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestTaskServiceGetTaskStatistics:
    """Tests for get_task_statistics method"""

    def test_get_task_statistics(self):
        """Test getting task statistics"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.status = "pending"
        mock_task.category = "general"
        mock_task.priority = "medium"
        mock_task.due_date = date.today() + timedelta(days=1)
        mock_task.created_at = datetime.now()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_task]
        mock_db.query.return_value = mock_query

        result = service.get_task_statistics()

        assert "period" in result
        assert "created" in result
        assert "completed" in result
        assert "active" in result
        assert "overdue" in result
        assert "by_category" in result
        assert "by_priority" in result

    def test_get_task_statistics_with_staff_filter(self):
        """Test getting statistics filtered by staff"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.get_task_statistics(staff_id=1)

        assert "period" in result
        mock_query.filter.assert_called()


class TestTaskServiceGetUpcomingReminders:
    """Tests for get_upcoming_reminders method"""

    def test_get_upcoming_reminders(self):
        """Test getting tasks with upcoming reminders"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Reminder Task"
        mock_task.reminder_at = datetime.now() + timedelta(hours=12)
        mock_task.assigned_to = MagicMock(name="Staff")
        mock_task.assigned_by = None
        mock_task.client = None
        mock_task.completed_by = None
        mock_task.description = None
        mock_task.category = "general"
        mock_task.priority = "medium"
        mock_task.status = "pending"
        mock_task.due_date = None
        mock_task.due_time = None
        mock_task.completed_at = None
        mock_task.completion_notes = None
        mock_task.is_recurring = False
        mock_task.recurrence_pattern = None
        mock_task.recurrence_end_date = None
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_task]
        mock_db.query.return_value = mock_query

        result = service.get_upcoming_reminders(within_hours=24)

        assert isinstance(result, list)


class TestGetTaskServiceFactory:
    """Tests for get_task_service factory function"""

    def test_get_task_service(self):
        """Test factory function creates TaskService"""
        from services.task_service import get_task_service, TaskService

        mock_db = MagicMock()
        service = get_task_service(mock_db)

        assert isinstance(service, TaskService)
        assert service.db == mock_db


class TestRecurringTaskCreation:
    """Tests for recurring task creation logic"""

    @patch('database.StaffTask')
    def test_create_next_recurring_daily(self, mock_task_class):
        """Test next task creation for daily recurrence"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.due_date = date.today()
        mock_task.recurrence_pattern = "daily"
        mock_task.recurrence_end_date = date.today() + timedelta(days=30)
        mock_task.due_time = None
        mock_task.parent_task_id = None
        mock_task.id = 1
        mock_task.assigned_to_id = 1
        mock_task.assigned_by_id = None
        mock_task.client_id = None
        mock_task.title = "Daily Task"
        mock_task.description = "Test"
        mock_task.category = "general"
        mock_task.priority = "medium"

        result = service._create_next_recurring_task(mock_task)

        # Should create a new task instance
        mock_db.add.assert_called_once()

    @patch('database.StaffTask')
    def test_create_next_recurring_past_end_date(self, mock_task_class):
        """Test that no task is created when past end date"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.due_date = date.today()
        mock_task.recurrence_pattern = "daily"
        mock_task.recurrence_end_date = date.today()  # End date is today

        result = service._create_next_recurring_task(mock_task)

        # Should not create a new task (next would be tomorrow, past end date)
        assert result is None

    def test_create_next_recurring_no_due_date(self):
        """Test that no task is created when no due date"""
        from services.task_service import TaskService

        mock_db = MagicMock()
        service = TaskService(mock_db)

        mock_task = MagicMock()
        mock_task.due_date = None
        mock_task.recurrence_pattern = "daily"

        result = service._create_next_recurring_task(mock_task)

        assert result is None
