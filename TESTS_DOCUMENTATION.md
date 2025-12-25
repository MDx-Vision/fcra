# FCRA Litigation Platform - Test Documentation

This document provides comprehensive documentation for all automated tests across all 8 phases of the platform.

## Test Infrastructure

### Running Tests

```bash
# Run all tests
pytest tests/

# Run tests with verbose output
pytest tests/ -v

# Run specific phase tests
pytest tests/test_phase1_core.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

### Test Fixtures (`tests/conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `app` | session | Flask application instance with test configuration |
| `client` | function | Flask test client for HTTP requests |
| `db_session` | function | Database session with automatic rollback |
| `authenticated_client` | function | Test client with staff authentication |
| `sample_staff` | function | Staff user fixture for testing |
| `sample_client` | function | Client record fixture |
| `sample_credit_report` | function | Credit report fixture |
| `sample_analysis` | function | Analysis record fixture |
| `sample_tag` | function | Client tag fixture (Phase 8) |

---

## Phase 1: Core Platform Tests (`test_phase1_core.py`)

### TestClientModel
Tests for the Client database model.

| Test | Description |
|------|-------------|
| `test_client_model_exists` | Verify Client model can be imported |
| `test_client_creation` | Test creating a new client record |
| `test_client_required_fields` | Verify required fields are enforced |
| `test_client_ssn_encryption` | Test SSN field encryption |

### TestCreditReportModel
Tests for the CreditReport model.

| Test | Description |
|------|-------------|
| `test_credit_report_model_exists` | Verify CreditReport model exists |
| `test_create_credit_report` | Test creating credit report records |
| `test_credit_report_client_relationship` | Test foreign key relationship |

### TestAnalysisModel
Tests for the Analysis model.

| Test | Description |
|------|-------------|
| `test_analysis_model_exists` | Verify Analysis model exists |
| `test_create_analysis` | Test creating analysis records |
| `test_analysis_cost_tracking` | Test cost and token tracking fields |

### TestDisputeLetterModel
Tests for the DisputeLetter model.

| Test | Description |
|------|-------------|
| `test_dispute_letter_model_exists` | Verify DisputeLetter model exists |
| `test_create_dispute_letter` | Test creating dispute letters |
| `test_letter_bureaus` | Test all 3 bureau types supported |

### TestStaffModel
Tests for the Staff model.

| Test | Description |
|------|-------------|
| `test_staff_model_exists` | Verify Staff model exists |
| `test_staff_password_hashing` | Test password hashing functionality |
| `test_staff_roles` | Test role field values |

### TestDatabaseMigrations
Tests for database migration system.

| Test | Description |
|------|-------------|
| `test_migrations_list_exists` | Verify migrations list is defined |
| `test_run_migrations_function` | Test migration function exists |

### TestFileUpload
Tests for file upload functionality.

| Test | Description |
|------|-------------|
| `test_upload_endpoint_exists` | Verify upload endpoint responds |
| `test_file_type_validation` | Test allowed file types |

### TestDashboardRoutes
Tests for dashboard routes.

| Test | Description |
|------|-------------|
| `test_dashboard_requires_auth` | Verify auth is required |
| `test_client_manager_route` | Test client manager loads |
| `test_api_routes_exist` | Test API endpoints respond |

---

## Phase 2: Litigation Features Tests (`test_phase2_litigation.py`)

### TestViolationModel
Tests for FCRA violation tracking.

| Test | Description |
|------|-------------|
| `test_violation_model_exists` | Verify Violation model exists |
| `test_create_violation` | Test creating violation records |
| `test_fcra_section_field` | Test FCRA section references |
| `test_willfulness_flag` | Test willful violation flag |

### TestLetterVersioning
Tests for letter version control.

| Test | Description |
|------|-------------|
| `test_letter_version_field` | Verify version field exists |
| `test_increment_version` | Test version incrementing |
| `test_letter_history` | Test version history tracking |

### TestMultiRoundDisputes
Tests for multi-round dispute support.

| Test | Description |
|------|-------------|
| `test_dispute_round_field` | Verify round tracking field |
| `test_round_increment` | Test round progression |
| `test_max_rounds` | Test 4-round limit |

### TestResponseTracking
Tests for bureau response tracking.

| Test | Description |
|------|-------------|
| `test_response_deadline_fields` | Test deadline field exists |
| `test_response_status_tracking` | Test response status values |
| `test_30_day_deadline` | Test 30-day calculation |

### TestLitigationDocuments
Tests for litigation document generation.

| Test | Description |
|------|-------------|
| `test_intent_to_sue_fields` | Test ITS-related fields |
| `test_demand_letter_generation` | Test demand letter capability |

### TestDamageCalculations
Tests for damage estimation.

| Test | Description |
|------|-------------|
| `test_statutory_damages` | Test $100-$1000 range |
| `test_willful_damages` | Test willful violation cap |
| `test_actual_damages_field` | Test actual damages tracking |

---

## Phase 3: AI Integration Tests (`test_phase3_ai.py`)

### TestCreditReportParser
Tests for credit report parsing.

| Test | Description |
|------|-------------|
| `test_parser_exists` | Verify parser class exists |
| `test_parse_basic_structure` | Test HTML parsing |
| `test_extract_accounts` | Test account extraction |

### TestViolationDetection
Tests for AI-powered violation detection.

| Test | Description |
|------|-------------|
| `test_fcra_sections_defined` | Test violation types defined |
| `test_violation_severity_levels` | Test severity classification |

### TestLetterGeneration
Tests for AI letter generation.

| Test | Description |
|------|-------------|
| `test_letter_generator_exists` | Verify generator exists |
| `test_letter_templates` | Test template loading |
| `test_letter_bureau_specific` | Test bureau customization |

### TestBatchProcessing
Tests for batch analysis.

| Test | Description |
|------|-------------|
| `test_batch_endpoint` | Test batch API endpoint |
| `test_concurrent_processing` | Test parallel processing |

### TestCostTracking
Tests for AI cost tracking.

| Test | Description |
|------|-------------|
| `test_token_tracking` | Test token count field |
| `test_cost_calculation` | Test cost calculation |

---

## Phase 4: Certified Mail Tests (`test_phase4_mail.py`)

### TestCertifiedMailModels
Tests for mail tracking models.

| Test | Description |
|------|-------------|
| `test_certified_mail_order_model_exists` | Verify model exists |
| `test_dispute_letter_tracking_fields` | Test tracking fields |

### TestMailServiceIntegration
Tests for mail service framework.

| Test | Description |
|------|-------------|
| `test_integration_connection_model` | Test connection model |
| `test_sftp_configuration_structure` | Test SFTP config |

### TestLetterUploadWorkflow
Tests for mail upload workflow.

| Test | Description |
|------|-------------|
| `test_pdf_generation_for_mail` | Test PDF generation |
| `test_letter_has_required_mail_fields` | Test required fields |

### TestAddressValidation
Tests for address validation.

| Test | Description |
|------|-------------|
| `test_client_address_fields` | Test address fields exist |
| `test_address_completeness_check` | Test completeness validation |

### TestTrackingNumbers
Tests for tracking number handling.

| Test | Description |
|------|-------------|
| `test_tracking_number_format` | Test USPS format |
| `test_tracking_update_storage` | Test storage of updates |

### TestMailCostTracking
Tests for mailing costs.

| Test | Description |
|------|-------------|
| `test_cost_per_letter` | Test cost calculation |
| `test_bulk_mailing_discount` | Test bulk discounts |

### TestDeliveryNotifications
Tests for delivery notifications.

| Test | Description |
|------|-------------|
| `test_notification_model_exists` | Verify model exists |
| `test_create_delivery_notification` | Test notification creation |

### TestFailedDeliveryAlerts
Tests for failed delivery handling.

| Test | Description |
|------|-------------|
| `test_failed_delivery_status` | Test failure status codes |
| `test_alert_on_failure` | Test failure alerts |

---

## Phase 5: Client Portal Tests (`test_phase5_portal.py`)

### TestClientAuthentication
Tests for portal authentication.

| Test | Description |
|------|-------------|
| `test_portal_login_page_exists` | Verify login page exists |
| `test_portal_login_with_token` | Test token-based login |
| `test_portal_requires_auth` | Test auth requirement |

### TestClientDashboard
Tests for client dashboard.

| Test | Description |
|------|-------------|
| `test_dashboard_tabs_structure` | Test required tabs |
| `test_case_status_display` | Test status display |

### TestLetterViewing
Tests for letter viewing.

| Test | Description |
|------|-------------|
| `test_letter_download_endpoint` | Test download endpoint |

### TestDocumentUpload
Tests for document uploads.

| Test | Description |
|------|-------------|
| `test_client_upload_model` | Verify model exists |
| `test_upload_categories` | Test upload categories |
| `test_create_upload_record` | Test upload record creation |

### TestProgressTimeline
Tests for progress tracking.

| Test | Description |
|------|-------------|
| `test_dispute_round_tracking` | Test round tracking |
| `test_round_started_timestamp` | Test timestamp field |

### TestCommunicationSystem
Tests for notifications.

| Test | Description |
|------|-------------|
| `test_notification_model` | Verify model exists |
| `test_create_notification` | Test notification creation |
| `test_email_log_model` | Verify email logging |
| `test_sms_log_model` | Verify SMS logging |

### TestCaseDeadlines
Tests for deadline tracking.

| Test | Description |
|------|-------------|
| `test_deadline_model` | Verify model exists |
| `test_create_deadline` | Test deadline creation |

### TestSettlementNotifications
Tests for settlements.

| Test | Description |
|------|-------------|
| `test_settlement_model` | Verify model exists |
| `test_create_settlement` | Test settlement creation |

### TestPasswordReset
Tests for password reset.

| Test | Description |
|------|-------------|
| `test_password_reset_fields` | Test reset fields exist |
| `test_generate_reset_token` | Test token generation |

---

## Phase 6: Business Intelligence Tests (`test_phase6_analytics.py`)

### TestAnalyticsDashboard
Tests for analytics page.

| Test | Description |
|------|-------------|
| `test_analytics_page_requires_auth` | Test auth requirement |
| `test_analytics_page_authenticated` | Test page loads |

### TestCaseMetrics
Tests for case metrics.

| Test | Description |
|------|-------------|
| `test_count_total_cases` | Test case counting |
| `test_count_by_status` | Test status grouping |
| `test_count_by_round` | Test round grouping |

### TestViolationAnalytics
Tests for violation analytics.

| Test | Description |
|------|-------------|
| `test_violation_type_breakdown` | Test type breakdown |
| `test_willfulness_ratio` | Test ratio calculation |

### TestSettlementTracking
Tests for settlement tracking.

| Test | Description |
|------|-------------|
| `test_settlements_page_exists` | Verify page exists |
| `test_settlement_model_fields` | Test required fields |
| `test_calculate_average_settlement` | Test average calculation |
| `test_settlement_status_values` | Test status values |

### TestRevenueTracking
Tests for revenue tracking.

| Test | Description |
|------|-------------|
| `test_payment_status_field` | Test payment fields |
| `test_calculate_total_revenue` | Test revenue calculation |

### TestCostTracking
Tests for cost tracking.

| Test | Description |
|------|-------------|
| `test_analysis_cost_field` | Test cost field |
| `test_calculate_average_cost` | Test average calculation |

### TestBureauCompliance
Tests for compliance tracking.

| Test | Description |
|------|-------------|
| `test_bureau_response_tracking` | Test response tracking |

### TestReporting
Tests for reporting features.

| Test | Description |
|------|-------------|
| `test_date_range_filtering` | Test date filtering |
| `test_monthly_aggregation` | Test monthly grouping |

### TestCasePipeline
Tests for pipeline visualization.

| Test | Description |
|------|-------------|
| `test_pipeline_stages` | Test stage definitions |
| `test_cases_per_stage` | Test stage counting |

### TestStaffRoles
Tests for staff roles.

| Test | Description |
|------|-------------|
| `test_staff_roles_defined` | Test role definitions |
| `test_permission_checking` | Test permission system |
| `test_client_assignment` | Test client assignment |

---

## Phase 7: Credit Monitoring Tests (`test_phase7_credit.py`)

### TestCreditMonitoringCredentials
Tests for credential storage.

| Test | Description |
|------|-------------|
| `test_credential_model_exists` | Verify model exists |
| `test_client_credential_fields` | Test credential fields |
| `test_supported_services` | Test supported services |

### TestEncryption
Tests for password encryption.

| Test | Description |
|------|-------------|
| `test_encryption_module_exists` | Verify module exists |
| `test_encrypt_decrypt_round_trip` | Test encrypt/decrypt |
| `test_is_encrypted_check` | Test encryption detection |

### TestCreditReportParser
Tests for report parsing.

| Test | Description |
|------|-------------|
| `test_parser_module_exists` | Verify parser exists |
| `test_parse_basic_html` | Test HTML parsing |

### TestScoreExtraction
Tests for score extraction.

| Test | Description |
|------|-------------|
| `test_score_snapshot_model` | Verify model exists |
| `test_create_score_snapshot` | Test snapshot creation |
| `test_score_range_validation` | Test 300-850 range |

### TestAccountExtraction
Tests for account extraction.

| Test | Description |
|------|-------------|
| `test_account_fields` | Test expected fields |
| `test_payment_history_format` | Test history codes |

### TestLatePaymentDetection
Tests for late payment detection.

| Test | Description |
|------|-------------|
| `test_count_late_payments` | Test late counting |
| `test_late_payment_severity` | Test severity levels |

### TestInquiryExtraction
Tests for inquiry extraction.

| Test | Description |
|------|-------------|
| `test_inquiry_fields` | Test inquiry structure |
| `test_hard_vs_soft_inquiries` | Test inquiry types |

### TestAccountDeduplication
Tests for deduplication.

| Test | Description |
|------|-------------|
| `test_identify_duplicate_accounts` | Test duplicate detection |

### TestCollectionsDetection
Tests for collections.

| Test | Description |
|------|-------------|
| `test_identify_collection_accounts` | Test collections detection |

### TestPublicRecords
Tests for public records.

| Test | Description |
|------|-------------|
| `test_public_record_types` | Test record types |

### TestCreditImportPage
Tests for import page.

| Test | Description |
|------|-------------|
| `test_import_page_exists` | Verify page exists |
| `test_import_page_structure` | Test page structure |

### TestEnhancedReportView
Tests for report view.

| Test | Description |
|------|-------------|
| `test_report_view_endpoint` | Test view endpoint |

---

## Phase 8: BAG CRM Feature Parity Tests (`test_phase8_crm.py`)

### TestClientTagModel
Tests for tag model.

| Test | Description |
|------|-------------|
| `test_client_tag_model_exists` | Verify model exists |
| `test_create_tag` | Test tag creation |
| `test_tag_unique_name` | Test name uniqueness |

### TestClientTagAssignment
Tests for tag assignments.

| Test | Description |
|------|-------------|
| `test_assignment_model_exists` | Verify model exists |
| `test_assign_tag_to_client` | Test assignment creation |
| `test_get_client_tags` | Test getting client tags |

### TestTagAPIEndpoints
Tests for tag API.

| Test | Description |
|------|-------------|
| `test_list_tags` | Test GET /api/tags |
| `test_create_tag_api` | Test POST /api/tags |
| `test_update_tag_api` | Test PUT /api/tags/{id} |
| `test_delete_tag_api` | Test DELETE /api/tags/{id} |

### TestClientTagAPIEndpoints
Tests for client tag API.

| Test | Description |
|------|-------------|
| `test_get_client_tags_api` | Test GET client tags |
| `test_add_tag_to_client_api` | Test POST tag to client |
| `test_remove_tag_from_client_api` | Test DELETE tag from client |

### TestUserQuickLinks
Tests for quick links model.

| Test | Description |
|------|-------------|
| `test_quick_link_model_exists` | Verify model exists |
| `test_create_quick_link` | Test quick link creation |
| `test_quick_link_slots` | Test 8-slot limit |

### TestQuickLinksAPI
Tests for quick links API.

| Test | Description |
|------|-------------|
| `test_get_quick_links` | Test GET quick links |
| `test_save_quick_link` | Test POST quick link |
| `test_delete_quick_link` | Test DELETE quick link |

### TestPagination
Tests for pagination.

| Test | Description |
|------|-------------|
| `test_client_manager_pagination` | Test pagination works |
| `test_pagination_parameters` | Test per_page values |
| `test_invalid_per_page_defaults` | Test invalid values |

### TestInlineEditing
Tests for inline editing.

| Test | Description |
|------|-------------|
| `test_update_status_2` | Test status_2 update |
| `test_toggle_phone_verified` | Test phone toggle |
| `test_client_type_update` | Test type update |

### TestNewClientFields
Tests for new fields.

| Test | Description |
|------|-------------|
| `test_employer_company_field` | Test employer field |
| `test_status_2_field` | Test status_2 field |
| `test_phone_verified_field` | Test phone verified |
| `test_starred_field` | Test starred field |
| `test_is_affiliate_field` | Test affiliate field |
| `test_portal_posted_field` | Test portal posted |

### TestVersionBadge
Tests for version badge.

| Test | Description |
|------|-------------|
| `test_client_manager_has_version` | Test v2.0 badge display |

### TestClientTypeColumn
Tests for type column.

| Test | Description |
|------|-------------|
| `test_client_type_values` | Test valid type values |
| `test_client_type_default` | Test default value |

### TestAffiliateDisplay
Tests for affiliate badges.

| Test | Description |
|------|-------------|
| `test_affiliate_field` | Test field exists |
| `test_set_affiliate_status` | Test setting status |

---

## Test Statistics

| Phase | Test Classes | Test Methods |
|-------|--------------|--------------|
| Phase 1 - Core Platform | 8 | 18 |
| Phase 2 - Litigation | 6 | 15 |
| Phase 3 - AI Integration | 5 | 12 |
| Phase 4 - Certified Mail | 8 | 17 |
| Phase 5 - Client Portal | 9 | 17 |
| Phase 6 - Business Intelligence | 10 | 18 |
| Phase 7 - Credit Monitoring | 12 | 18 |
| Phase 8 - BAG CRM | 12 | 32 |
| **Total** | **70** | **147** |

---

## Continuous Integration

Tests are designed to run in CI/CD pipelines. Recommended configuration:

```yaml
# GitHub Actions example
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest tests/ -v --tb=short
```

---

## Contributing

When adding new features:
1. Create corresponding tests in the appropriate phase file
2. Add fixture to `conftest.py` if needed
3. Update this documentation
4. Ensure all tests pass before committing

---

*Last updated: December 2025*
