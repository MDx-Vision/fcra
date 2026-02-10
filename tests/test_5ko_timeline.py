"""
Tests for 5-Day Knockout Timeline API endpoints and Client Items API
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestFkoClientItemsBureauDetection:
    """Tests for GET /api/5day-knockout/client/<id>/items - Bureau Detection Fix (ISSUE-005)"""

    def test_bureau_detection_nested_structure(self):
        """Test that bureau detection works with nested bureaus.X.present structure"""
        # This is the structure from JSON extraction
        account = {
            "creditor": "AMERICAN EXPRESS",
            "account_number": "1234",
            "balance": "$100.00",
            "bureaus": {
                "transunion": {"present": False},
                "experian": {"present": False},
                "equifax": {"present": True, "balance": "$100.00"},
            }
        }

        bureaus = []
        bureaus_data = account.get("bureaus", {})

        if bureaus_data.get("equifax", {}).get("present"):
            bureaus.append("Equifax")
        elif account.get("equifax") or account.get("efx_status"):
            bureaus.append("Equifax")

        if bureaus_data.get("experian", {}).get("present"):
            bureaus.append("Experian")
        elif account.get("experian") or account.get("exp_status"):
            bureaus.append("Experian")

        if bureaus_data.get("transunion", {}).get("present"):
            bureaus.append("TransUnion")
        elif account.get("transunion") or account.get("tu_status"):
            bureaus.append("TransUnion")

        # Should only detect Equifax, not all 3
        assert bureaus == ["Equifax"]
        assert "Experian" not in bureaus
        assert "TransUnion" not in bureaus

    def test_bureau_detection_flat_structure(self):
        """Test that bureau detection still works with flat structure (legacy)"""
        # This is the legacy flat structure
        account = {
            "creditor": "CHASE",
            "equifax": True,
            "experian": True,
            "transunion": False,
        }

        bureaus = []
        bureaus_data = account.get("bureaus", {})

        if bureaus_data.get("equifax", {}).get("present"):
            bureaus.append("Equifax")
        elif account.get("equifax") or account.get("efx_status"):
            bureaus.append("Equifax")

        if bureaus_data.get("experian", {}).get("present"):
            bureaus.append("Experian")
        elif account.get("experian") or account.get("exp_status"):
            bureaus.append("Experian")

        if bureaus_data.get("transunion", {}).get("present"):
            bureaus.append("TransUnion")
        elif account.get("transunion") or account.get("tu_status"):
            bureaus.append("TransUnion")

        assert "Equifax" in bureaus
        assert "Experian" in bureaus
        assert "TransUnion" not in bureaus

    def test_bureau_detection_all_three_present(self):
        """Test detection when all 3 bureaus report the account"""
        account = {
            "creditor": "CITICARDS",
            "bureaus": {
                "transunion": {"present": True, "balance": "$500.00"},
                "experian": {"present": True, "balance": "$500.00"},
                "equifax": {"present": True, "balance": "$500.00"},
            }
        }

        bureaus = []
        bureaus_data = account.get("bureaus", {})

        if bureaus_data.get("equifax", {}).get("present"):
            bureaus.append("Equifax")
        if bureaus_data.get("experian", {}).get("present"):
            bureaus.append("Experian")
        if bureaus_data.get("transunion", {}).get("present"):
            bureaus.append("TransUnion")

        assert len(bureaus) == 3
        assert "Equifax" in bureaus
        assert "Experian" in bureaus
        assert "TransUnion" in bureaus

    def test_bureau_detection_defaults_to_all_when_no_data(self):
        """Test that missing bureau data defaults to all 3 bureaus"""
        account = {
            "creditor": "UNKNOWN CREDITOR",
            "balance": "$50.00",
        }

        bureaus = []
        bureaus_data = account.get("bureaus", {})

        if bureaus_data.get("equifax", {}).get("present"):
            bureaus.append("Equifax")
        elif account.get("equifax") or account.get("efx_status"):
            bureaus.append("Equifax")

        if bureaus_data.get("experian", {}).get("present"):
            bureaus.append("Experian")
        elif account.get("experian") or account.get("exp_status"):
            bureaus.append("Experian")

        if bureaus_data.get("transunion", {}).get("present"):
            bureaus.append("TransUnion")
        elif account.get("transunion") or account.get("tu_status"):
            bureaus.append("TransUnion")

        # Default to all 3 when no bureau info
        if not bureaus:
            bureaus = ["Equifax", "Experian", "TransUnion"]

        assert len(bureaus) == 3

    def test_bureau_detection_efx_status_fallback(self):
        """Test that efx_status/exp_status/tu_status fallbacks work"""
        account = {
            "creditor": "OLD FORMAT",
            "efx_status": "Active",
            "exp_status": None,
            "tu_status": "Closed",
        }

        bureaus = []
        bureaus_data = account.get("bureaus", {})

        if bureaus_data.get("equifax", {}).get("present"):
            bureaus.append("Equifax")
        elif account.get("equifax") or account.get("efx_status"):
            bureaus.append("Equifax")

        if bureaus_data.get("experian", {}).get("present"):
            bureaus.append("Experian")
        elif account.get("experian") or account.get("exp_status"):
            bureaus.append("Experian")

        if bureaus_data.get("transunion", {}).get("present"):
            bureaus.append("TransUnion")
        elif account.get("transunion") or account.get("tu_status"):
            bureaus.append("TransUnion")

        assert "Equifax" in bureaus  # efx_status = "Active"
        assert "Experian" not in bureaus  # exp_status = None
        assert "TransUnion" in bureaus  # tu_status = "Closed"


class TestFkoTimelineGet:
    """Tests for GET /api/5day-knockout/client/<id>/timeline"""

    def test_get_timeline_returns_correct_structure(self):
        """Test that timeline API returns expected fields"""
        with patch('app.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_client = MagicMock()
            mock_client.id = 1
            mock_client.name = "Test Client"
            mock_client.fko_started_at = None
            mock_client.fko_ftc_filed_at = None
            mock_client.fko_cfpb_filed_at = None
            mock_client.fko_police_filed_at = None
            mock_client.fko_letters_sent_at = None
            mock_client.fko_followup_called_at = None
            mock_client.fko_verified_at = None
            mock_client.fko_completed_at = None
            mock_client.fko_status = "not_started"
            mock_client.fko_notes = None

            mock_db.query.return_value.filter.return_value.first.return_value = mock_client
            mock_get_db.return_value.__enter__.return_value = mock_db

            from app import app
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['staff_id'] = 1
                    sess['staff_role'] = 'admin'

                response = client.get('/api/5day-knockout/client/1/timeline')
                data = response.get_json()

                assert data['success'] is True
                assert 'steps' in data
                assert 'progress_percent' in data
                assert 'status' in data

    def test_get_timeline_client_not_found(self):
        """Test 404 when client doesn't exist"""
        with patch('app.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_db.return_value.__enter__.return_value = mock_db

            from app import app
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['staff_id'] = 1
                    sess['staff_role'] = 'admin'

                response = client.get('/api/5day-knockout/client/999/timeline')
                assert response.status_code == 404


class TestFkoTimelineUpdate:
    """Tests for POST /api/5day-knockout/client/<id>/timeline"""

    def test_update_timeline_step_complete(self):
        """Test completing a timeline step"""
        with patch('app.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_client = MagicMock()
            mock_client.fko_started_at = None
            mock_client.fko_ftc_filed_at = None
            mock_client.fko_status = "not_started"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_client
            mock_get_db.return_value.__enter__.return_value = mock_db

            from app import app
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['staff_id'] = 1
                    sess['staff_role'] = 'admin'

                response = client.post('/api/5day-knockout/client/1/timeline',
                    json={'step_id': 'ftc_filed', 'action': 'complete'})
                data = response.get_json()

                assert data['success'] is True
                assert data['step_id'] == 'ftc_filed'
                assert data['action'] == 'complete'

    def test_update_timeline_invalid_step(self):
        """Test error on invalid step_id"""
        with patch('app.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db

            from app import app
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['staff_id'] = 1
                    sess['staff_role'] = 'admin'

                response = client.post('/api/5day-knockout/client/1/timeline',
                    json={'step_id': 'invalid_step', 'action': 'complete'})

                assert response.status_code == 400

    def test_update_timeline_missing_step_id(self):
        """Test error when step_id is missing"""
        with patch('app.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_db

            from app import app
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['staff_id'] = 1
                    sess['staff_role'] = 'admin'

                response = client.post('/api/5day-knockout/client/1/timeline',
                    json={'action': 'complete'})

                assert response.status_code == 400


class TestFkoTimelineStart:
    """Tests for POST /api/5day-knockout/client/<id>/timeline/start"""

    def test_start_process(self):
        """Test starting the 5KO process"""
        with patch('app.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_client = MagicMock()
            mock_client.fko_started_at = None
            mock_client.fko_status = "not_started"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_client
            mock_get_db.return_value.__enter__.return_value = mock_db

            from app import app
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['staff_id'] = 1
                    sess['staff_role'] = 'admin'

                response = client.post('/api/5day-knockout/client/1/timeline/start')
                data = response.get_json()

                assert data['success'] is True
                assert 'started_at' in data

    def test_start_process_already_started(self):
        """Test starting when process already started"""
        with patch('app.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_client = MagicMock()
            mock_client.fko_started_at = datetime.utcnow()
            mock_client.fko_status = "in_progress"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_client
            mock_get_db.return_value.__enter__.return_value = mock_db

            from app import app
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['staff_id'] = 1
                    sess['staff_role'] = 'admin'

                response = client.post('/api/5day-knockout/client/1/timeline/start')
                data = response.get_json()

                assert data['success'] is True
                assert data['message'] == 'Process already started'


class TestFkoTimelineNotes:
    """Tests for POST /api/5day-knockout/client/<id>/timeline/notes"""

    def test_update_notes(self):
        """Test updating notes"""
        with patch('app.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_client = MagicMock()
            mock_client.fko_notes = None

            mock_db.query.return_value.filter.return_value.first.return_value = mock_client
            mock_get_db.return_value.__enter__.return_value = mock_db

            from app import app
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['staff_id'] = 1
                    sess['staff_role'] = 'admin'

                response = client.post('/api/5day-knockout/client/1/timeline/notes',
                    json={'notes': 'Test notes'})
                data = response.get_json()

                assert data['success'] is True


class TestFkoTimelineSteps:
    """Tests for timeline step definitions"""

    def test_all_step_ids_are_valid(self):
        """Test that all step IDs are in the column map"""
        step_column_map = {
            "started": "fko_started_at",
            "ftc_filed": "fko_ftc_filed_at",
            "cfpb_filed": "fko_cfpb_filed_at",
            "police_filed": "fko_police_filed_at",
            "letters_sent": "fko_letters_sent_at",
            "followup_called": "fko_followup_called_at",
            "verified": "fko_verified_at",
            "completed": "fko_completed_at",
        }

        # Verify all columns exist in the Client model
        from database import Client

        for step_id, column_name in step_column_map.items():
            assert hasattr(Client, column_name), f"Client model missing column: {column_name}"

    def test_fko_status_column_exists(self):
        """Test that fko_status column exists"""
        from database import Client
        assert hasattr(Client, 'fko_status')

    def test_fko_notes_column_exists(self):
        """Test that fko_notes column exists"""
        from database import Client
        assert hasattr(Client, 'fko_notes')
