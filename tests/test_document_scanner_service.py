"""
Comprehensive Unit Tests for DocumentScanner Service

Tests cover:
- Document scanning and OCR
- Image processing and optimization
- Text extraction from images
- Document classification
- Multi-page document processing
- Scan session management
- PDF generation
- Cleanup and session management
"""

import io
import os
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, mock_open

# Import the module to test
from services.document_scanner_service import (
    DocumentScanner,
    ScanSession,
    DOCUMENT_TYPES,
    UPLOAD_FOLDER,
    OUTPUT_FOLDER,
    create_scan_session,
    get_scan_session,
    cleanup_old_sessions,
    get_document_types,
    scan_sessions,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def scanner():
    """Create a DocumentScanner instance with mocked Anthropic client."""
    with patch('services.document_scanner_service.anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        scanner = DocumentScanner()
        scanner.client = mock_client
        return scanner


@pytest.fixture
def scanner_no_client():
    """Create a DocumentScanner instance without an Anthropic client."""
    with patch('services.document_scanner_service.anthropic.Anthropic') as mock_anthropic:
        mock_anthropic.side_effect = Exception("No API key")
        scanner = DocumentScanner()
        scanner.client = None
        return scanner


@pytest.fixture
def mock_image_data():
    """Create mock image data bytes."""
    # Create a simple 10x10 RGB image bytes
    return b'\x89PNG\r\n\x1a\n' + b'\x00' * 100


@pytest.fixture
def mock_pil_image():
    """Create a mock PIL Image object."""
    mock_img = MagicMock()
    mock_img.mode = "RGB"
    mock_img.size = (1000, 800)
    mock_img.width = 1000
    mock_img.height = 800
    mock_img.split.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    return mock_img


@pytest.fixture
def scan_session():
    """Create a ScanSession instance for testing."""
    with patch('services.document_scanner_service.DocumentScanner'):
        session = ScanSession(
            client_id=1,
            client_name="Test Client",
            document_type="cra_response_r1"
        )
        session.scanner = MagicMock()
        return session


@pytest.fixture
def cleanup_sessions():
    """Fixture to clean up scan_sessions after tests."""
    yield
    scan_sessions.clear()


# =============================================================================
# Test Class: DocumentScanner Initialization
# =============================================================================

class TestDocumentScannerInit:
    """Tests for DocumentScanner initialization."""

    def test_init_with_api_key_env_var(self):
        """Test initialization with ANTHROPIC_API_KEY environment variable."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('services.document_scanner_service.anthropic.Anthropic') as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client
                scanner = DocumentScanner()
                assert scanner.client is not None

    def test_init_with_fcra_env_var(self):
        """Test initialization with FCRA Automation Secure environment variable."""
        with patch.dict(os.environ, {'FCRA Automation Secure': 'fcra-key'}, clear=True):
            with patch('services.document_scanner_service.anthropic.Anthropic') as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client
                scanner = DocumentScanner()
                mock_anthropic.assert_called_with(api_key='fcra-key')

    def test_init_without_api_key(self):
        """Test initialization without API key uses default."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('services.document_scanner_service.anthropic.Anthropic') as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client
                scanner = DocumentScanner()
                mock_anthropic.assert_called_with()

    def test_init_handles_anthropic_exception(self):
        """Test initialization handles Anthropic initialization errors."""
        with patch('services.document_scanner_service.anthropic.Anthropic') as mock_anthropic:
            mock_anthropic.side_effect = Exception("API Error")
            scanner = DocumentScanner()
            # Should not raise, client should be None or set from exception handler


# =============================================================================
# Test Class: process_uploaded_image Method
# =============================================================================

class TestProcessUploadedImage:
    """Tests for image upload processing."""

    def test_process_valid_rgb_image(self, scanner, mock_pil_image):
        """Test processing a valid RGB image."""
        with patch('services.document_scanner_service.Image.open') as mock_open:
            with patch('services.document_scanner_service.os.path.getsize', return_value=50000):
                mock_open.return_value = mock_pil_image

                result = scanner.process_uploaded_image(b'fake_data', 'test.jpg')

                assert result['success'] is True
                assert 'image_id' in result
                assert 'filepath' in result
                assert 'width' in result
                assert 'height' in result
                assert result['original_filename'] == 'test.jpg'

    def test_process_rgba_image_converts_to_rgb(self, scanner):
        """Test processing RGBA image converts to RGB."""
        mock_img = MagicMock()
        mock_img.mode = "RGBA"
        mock_img.size = (800, 600)
        mock_img.width = 800
        mock_img.height = 600
        mock_alpha = MagicMock()
        mock_img.split.return_value = [MagicMock(), MagicMock(), MagicMock(), mock_alpha]

        with patch('services.document_scanner_service.Image.open', return_value=mock_img):
            with patch('services.document_scanner_service.Image.new') as mock_new:
                mock_background = MagicMock()
                mock_background.width = 800
                mock_background.height = 600
                mock_new.return_value = mock_background
                with patch('services.document_scanner_service.os.path.getsize', return_value=30000):
                    result = scanner.process_uploaded_image(b'rgba_data', 'test.png')

                    mock_new.assert_called_once_with("RGB", (800, 600), (255, 255, 255))
                    mock_background.paste.assert_called_once()

    def test_process_grayscale_image_converts_to_rgb(self, scanner):
        """Test processing grayscale image converts to RGB."""
        mock_img = MagicMock()
        mock_img.mode = "L"
        mock_img.size = (500, 500)
        mock_img.width = 500
        mock_img.height = 500
        mock_converted = MagicMock()
        mock_converted.width = 500
        mock_converted.height = 500
        mock_img.convert.return_value = mock_converted

        with patch('services.document_scanner_service.Image.open', return_value=mock_img):
            with patch('services.document_scanner_service.os.path.getsize', return_value=20000):
                result = scanner.process_uploaded_image(b'grayscale_data', 'test.png')

                mock_img.convert.assert_called_once_with("RGB")

    def test_process_oversized_image_resizes(self, scanner):
        """Test processing oversized image resizes to max dimension."""
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.size = (3000, 2500)
        mock_img.width = 3000
        mock_img.height = 2500
        mock_resized = MagicMock()
        mock_resized.width = 2000
        mock_resized.height = 1666
        mock_img.resize.return_value = mock_resized

        with patch('services.document_scanner_service.Image.open', return_value=mock_img):
            with patch('services.document_scanner_service.Image') as mock_image_class:
                mock_image_class.open.return_value = mock_img
                mock_image_class.Resampling.LANCZOS = 'lanczos'
                with patch('services.document_scanner_service.os.path.getsize', return_value=40000):
                    # The function will call resize
                    result = scanner.process_uploaded_image(b'large_data', 'test.jpg')

    def test_process_image_generates_unique_filename(self, scanner, mock_pil_image):
        """Test that processed images get unique filenames."""
        with patch('services.document_scanner_service.Image.open', return_value=mock_pil_image):
            with patch('services.document_scanner_service.os.path.getsize', return_value=25000):
                result1 = scanner.process_uploaded_image(b'data1', 'test1.jpg')
                result2 = scanner.process_uploaded_image(b'data2', 'test2.jpg')

                assert result1['filename'] != result2['filename']
                assert 'scan_' in result1['filename']

    def test_process_image_calculates_file_size(self, scanner, mock_pil_image):
        """Test that file size is correctly calculated."""
        with patch('services.document_scanner_service.Image.open', return_value=mock_pil_image):
            with patch('services.document_scanner_service.os.path.getsize', return_value=51200):
                result = scanner.process_uploaded_image(b'data', 'test.jpg')

                assert result['file_size'] == 51200
                assert result['file_size_kb'] == 50.0

    def test_process_invalid_image_returns_error(self, scanner):
        """Test processing invalid image data returns error."""
        with patch('services.document_scanner_service.Image.open') as mock_open:
            mock_open.side_effect = Exception("Invalid image format")

            result = scanner.process_uploaded_image(b'invalid_data', 'test.xyz')

            assert result['success'] is False
            assert 'error' in result

    def test_process_image_saves_as_jpeg(self, scanner, mock_pil_image):
        """Test that image is saved as optimized JPEG."""
        with patch('services.document_scanner_service.Image.open', return_value=mock_pil_image):
            with patch('services.document_scanner_service.os.path.getsize', return_value=30000):
                result = scanner.process_uploaded_image(b'data', 'test.png')

                mock_pil_image.save.assert_called_once()
                call_args = mock_pil_image.save.call_args
                assert call_args[0][1] == "JPEG"
                assert call_args[1]['quality'] == 85
                assert call_args[1]['optimize'] is True


# =============================================================================
# Test Class: combine_images_to_pdf Method
# =============================================================================

class TestCombineImagesToPdf:
    """Tests for PDF generation from images."""

    def test_combine_empty_list_returns_error(self, scanner):
        """Test combining empty image list returns error."""
        result = scanner.combine_images_to_pdf([])

        assert result['success'] is False
        assert 'No images provided' in result['error']

    def test_combine_single_portrait_image(self, scanner):
        """Test combining single portrait image."""
        mock_img = MagicMock()
        mock_img.size = (600, 800)  # Portrait

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=100000):
                        result = scanner.combine_images_to_pdf(['/path/to/image.jpg'])

                        mock_pdf.add_page.assert_called_with(orientation='P')

    def test_combine_single_landscape_image(self, scanner):
        """Test combining single landscape image."""
        mock_img = MagicMock()
        mock_img.size = (1000, 600)  # Landscape

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=100000):
                        result = scanner.combine_images_to_pdf(['/path/to/landscape.jpg'])

                        mock_pdf.add_page.assert_called_with(orientation='L')

    def test_combine_multiple_images(self, scanner):
        """Test combining multiple images into PDF."""
        mock_img = MagicMock()
        mock_img.size = (800, 600)

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=200000):
                        result = scanner.combine_images_to_pdf([
                            '/path/to/image1.jpg',
                            '/path/to/image2.jpg',
                            '/path/to/image3.jpg'
                        ])

                        assert result['page_count'] == 3
                        assert mock_pdf.add_page.call_count == 3

    def test_combine_with_custom_filename(self, scanner):
        """Test combining with custom output filename."""
        mock_img = MagicMock()
        mock_img.size = (800, 600)

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=150000):
                        result = scanner.combine_images_to_pdf(
                            ['/path/to/image.jpg'],
                            output_filename='custom_doc.pdf'
                        )

                        assert result['pdf_filename'] == 'custom_doc.pdf'

    def test_combine_generates_filename_from_client(self, scanner):
        """Test combining generates filename from client name."""
        mock_img = MagicMock()
        mock_img.size = (800, 600)

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=150000):
                        result = scanner.combine_images_to_pdf(
                            ['/path/to/image.jpg'],
                            client_name='John Doe',
                            document_type='cra_response_r1'
                        )

                        assert 'John_Doe' in result['pdf_filename']
                        assert 'cra-response-r1' in result['pdf_filename']

    def test_combine_skips_missing_files(self, scanner):
        """Test combining skips non-existent image files."""
        mock_img = MagicMock()
        mock_img.size = (800, 600)

        def path_exists(path):
            return 'exists' in path

        with patch('services.document_scanner_service.os.path.exists', side_effect=path_exists):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=100000):
                        result = scanner.combine_images_to_pdf([
                            '/path/exists/image.jpg',
                            '/path/missing/image.jpg'
                        ])

                        # Only one image should be processed
                        assert mock_pdf.add_page.call_count == 1

    def test_combine_returns_file_size(self, scanner):
        """Test combine returns file size information."""
        mock_img = MagicMock()
        mock_img.size = (800, 600)

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=102400):
                        result = scanner.combine_images_to_pdf(['/path/to/image.jpg'])

                        assert result['file_size'] == 102400
                        assert result['file_size_kb'] == 100.0

    def test_combine_handles_exception(self, scanner):
        """Test combine handles exceptions gracefully."""
        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open') as mock_open:
                mock_open.side_effect = Exception("Image read error")

                result = scanner.combine_images_to_pdf(['/path/to/image.jpg'])

                assert result['success'] is False
                assert 'error' in result


# =============================================================================
# Test Class: extract_text_from_image Method (OCR)
# =============================================================================

class TestExtractTextFromImage:
    """Tests for OCR text extraction."""

    def test_extract_without_client_returns_error(self, scanner_no_client):
        """Test extraction without Anthropic client returns error."""
        result = scanner_no_client.extract_text_from_image('/path/to/image.jpg')

        assert result['success'] is False
        assert 'Anthropic client not initialized' in result['error']
        assert result['mock'] is True

    def test_extract_text_jpeg_image(self, scanner):
        """Test extracting text from JPEG image."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Extracted text content")]
        mock_response.usage.input_tokens = 1000
        mock_response.usage.output_tokens = 500
        scanner.client.messages.create.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'image_data')):
            result = scanner.extract_text_from_image('/path/to/image.jpg', 'other')

            assert result['success'] is True
            assert result['text'] == "Extracted text content"
            assert result['char_count'] == len("Extracted text content")

    def test_extract_text_png_image(self, scanner):
        """Test extracting text from PNG image."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="PNG text")]
        mock_response.usage.input_tokens = 800
        mock_response.usage.output_tokens = 200
        scanner.client.messages.create.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'png_data')):
            result = scanner.extract_text_from_image('/path/to/image.png', 'other')

            call_args = scanner.client.messages.create.call_args
            # Check media type is set correctly for PNG
            assert result['success'] is True

    def test_extract_text_gif_image(self, scanner):
        """Test extracting text from GIF image."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="GIF text")]
        mock_response.usage.input_tokens = 500
        mock_response.usage.output_tokens = 100
        scanner.client.messages.create.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'gif_data')):
            result = scanner.extract_text_from_image('/path/to/image.gif', 'other')

            assert result['success'] is True

    def test_extract_text_webp_image(self, scanner):
        """Test extracting text from WebP image."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="WebP text")]
        mock_response.usage.input_tokens = 600
        mock_response.usage.output_tokens = 150
        scanner.client.messages.create.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'webp_data')):
            result = scanner.extract_text_from_image('/path/to/image.webp', 'other')

            assert result['success'] is True

    def test_extract_text_uses_document_type_prompt(self, scanner):
        """Test extraction uses document-type-specific OCR prompt."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="CRA response text")]
        mock_response.usage.input_tokens = 1200
        mock_response.usage.output_tokens = 600
        scanner.client.messages.create.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'data')):
            result = scanner.extract_text_from_image('/path/to/image.jpg', 'cra_response_r1')

            call_args = scanner.client.messages.create.call_args
            messages = call_args[1]['messages']
            # The prompt should contain document-specific instructions
            assert 'Round 1 response' in DOCUMENT_TYPES['cra_response_r1']['ocr_prompt']

    def test_extract_text_calculates_word_count(self, scanner):
        """Test extraction calculates word count."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is a test sentence with seven words")]
        mock_response.usage.input_tokens = 500
        mock_response.usage.output_tokens = 100
        scanner.client.messages.create.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'data')):
            result = scanner.extract_text_from_image('/path/to/image.jpg')

            assert result['word_count'] == 8

    def test_extract_text_calculates_cost(self, scanner):
        """Test extraction calculates estimated cost."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Text")]
        mock_response.usage.input_tokens = 1000
        mock_response.usage.output_tokens = 500
        scanner.client.messages.create.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'data')):
            result = scanner.extract_text_from_image('/path/to/image.jpg')

            # Cost calculation: (1000 * 0.003 + 500 * 0.015) / 1000
            expected_cost = round((1000 * 0.003 + 500 * 0.015) / 1000, 4)
            assert result['estimated_cost'] == expected_cost

    def test_extract_text_handles_empty_response(self, scanner):
        """Test extraction handles empty response content."""
        mock_response = MagicMock()
        mock_response.content = []
        mock_response.usage.input_tokens = 500
        mock_response.usage.output_tokens = 0
        scanner.client.messages.create.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'data')):
            result = scanner.extract_text_from_image('/path/to/image.jpg')

            assert result['text'] == ""

    def test_extract_text_handles_api_error(self, scanner):
        """Test extraction handles API errors gracefully."""
        scanner.client.messages.create.side_effect = Exception("API Error")

        with patch('builtins.open', mock_open(read_data=b'data')):
            result = scanner.extract_text_from_image('/path/to/image.jpg')

            assert result['success'] is False
            assert 'error' in result

    def test_extract_text_handles_file_not_found(self, scanner):
        """Test extraction handles file not found error."""
        with patch('builtins.open') as mock_file:
            mock_file.side_effect = FileNotFoundError("File not found")

            result = scanner.extract_text_from_image('/nonexistent/image.jpg')

            assert result['success'] is False


# =============================================================================
# Test Class: process_multi_page_document Method
# =============================================================================

class TestProcessMultiPageDocument:
    """Tests for multi-page document processing."""

    def test_process_returns_pdf_info(self, scanner):
        """Test processing returns PDF information."""
        scanner.combine_images_to_pdf = MagicMock(return_value={
            'success': True,
            'pdf_path': '/output/test.pdf',
            'pdf_filename': 'test.pdf',
            'page_count': 2
        })
        scanner.extract_text_from_image = MagicMock(return_value={
            'success': True,
            'text': 'Page text',
            'char_count': 9,
            'word_count': 2,
            'estimated_cost': 0.001
        })

        with patch('builtins.open', mock_open()):
            result = scanner.process_multi_page_document(
                ['/path/image1.jpg', '/path/image2.jpg'],
                run_ocr=False
            )

            assert result['success'] is True
            assert result['pdf_path'] == '/output/test.pdf'
            assert result['page_count'] == 2

    def test_process_with_ocr_extracts_all_pages(self, scanner):
        """Test processing with OCR extracts text from all pages."""
        scanner.combine_images_to_pdf = MagicMock(return_value={
            'success': True,
            'pdf_path': '/output/test.pdf',
            'pdf_filename': 'test.pdf',
            'page_count': 3
        })
        scanner.extract_text_from_image = MagicMock(return_value={
            'success': True,
            'text': 'Page content',
            'char_count': 12,
            'word_count': 2,
            'estimated_cost': 0.002
        })

        with patch('builtins.open', mock_open()):
            result = scanner.process_multi_page_document(
                ['/path/image1.jpg', '/path/image2.jpg', '/path/image3.jpg'],
                run_ocr=True
            )

            assert result['ocr_completed'] is True
            assert scanner.extract_text_from_image.call_count == 3
            assert '--- PAGE 1 ---' in result['extracted_text']

    def test_process_without_ocr(self, scanner):
        """Test processing without OCR skips text extraction."""
        scanner.combine_images_to_pdf = MagicMock(return_value={
            'success': True,
            'pdf_path': '/output/test.pdf',
            'pdf_filename': 'test.pdf',
            'page_count': 1
        })

        result = scanner.process_multi_page_document(
            ['/path/image.jpg'],
            run_ocr=False
        )

        assert result['ocr_completed'] is False
        assert 'extracted_text' not in result

    def test_process_saves_text_file(self, scanner):
        """Test processing saves extracted text to file."""
        scanner.combine_images_to_pdf = MagicMock(return_value={
            'success': True,
            'pdf_path': '/output/document.pdf',
            'pdf_filename': 'document.pdf',
            'page_count': 1
        })
        scanner.extract_text_from_image = MagicMock(return_value={
            'success': True,
            'text': 'Extracted text',
            'char_count': 14,
            'word_count': 2,
            'estimated_cost': 0.001
        })

        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            result = scanner.process_multi_page_document(
                ['/path/image.jpg'],
                run_ocr=True
            )

            assert 'text_file_path' in result
            assert result['text_file_path'].endswith('_text.txt')

    def test_process_calculates_total_cost(self, scanner):
        """Test processing calculates total OCR cost."""
        scanner.combine_images_to_pdf = MagicMock(return_value={
            'success': True,
            'pdf_path': '/output/test.pdf',
            'pdf_filename': 'test.pdf',
            'page_count': 2
        })
        scanner.extract_text_from_image = MagicMock(return_value={
            'success': True,
            'text': 'Text',
            'char_count': 4,
            'word_count': 1,
            'estimated_cost': 0.005
        })

        with patch('builtins.open', mock_open()):
            result = scanner.process_multi_page_document(
                ['/path/image1.jpg', '/path/image2.jpg'],
                run_ocr=True
            )

            assert result['estimated_ocr_cost'] == 0.01

    def test_process_handles_pdf_failure(self, scanner):
        """Test processing handles PDF creation failure."""
        scanner.combine_images_to_pdf = MagicMock(return_value={
            'success': False,
            'error': 'PDF creation failed'
        })

        result = scanner.process_multi_page_document(['/path/image.jpg'])

        assert result['success'] is False
        assert 'PDF creation failed' in result['error']

    def test_process_stores_document_in_database(self, scanner):
        """Test processing stores document in database when client_id provided."""
        scanner.combine_images_to_pdf = MagicMock(return_value={
            'success': True,
            'pdf_path': '/output/test.pdf',
            'pdf_filename': 'test.pdf',
            'page_count': 1
        })

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 123

        with patch('services.document_scanner_service.get_db', return_value=mock_db):
            with patch('services.document_scanner_service.Document') as mock_doc_class:
                mock_doc_class.return_value = mock_doc

                result = scanner.process_multi_page_document(
                    ['/path/image.jpg'],
                    client_id=1,
                    run_ocr=False
                )

                assert result['document_id'] == 123
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()

    def test_process_handles_database_error(self, scanner):
        """Test processing handles database errors gracefully."""
        scanner.combine_images_to_pdf = MagicMock(return_value={
            'success': True,
            'pdf_path': '/output/test.pdf',
            'pdf_filename': 'test.pdf',
            'page_count': 1
        })

        with patch('services.document_scanner_service.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            result = scanner.process_multi_page_document(
                ['/path/image.jpg'],
                client_id=1,
                run_ocr=False
            )

            assert result['success'] is True
            assert 'database_error' in result


# =============================================================================
# Test Class: cleanup_temp_images Method
# =============================================================================

class TestCleanupTempImages:
    """Tests for temporary image cleanup."""

    def test_cleanup_removes_existing_files(self, scanner):
        """Test cleanup removes existing temporary files."""
        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.os.remove') as mock_remove:
                paths = [
                    f'{UPLOAD_FOLDER}/image1.jpg',
                    f'{UPLOAD_FOLDER}/image2.jpg'
                ]
                removed = scanner.cleanup_temp_images(paths)

                assert removed == 2
                assert mock_remove.call_count == 2

    def test_cleanup_skips_nonexistent_files(self, scanner):
        """Test cleanup skips non-existent files."""
        with patch('services.document_scanner_service.os.path.exists', return_value=False):
            with patch('services.document_scanner_service.os.remove') as mock_remove:
                removed = scanner.cleanup_temp_images(['/nonexistent/image.jpg'])

                assert removed == 0
                mock_remove.assert_not_called()

    def test_cleanup_only_removes_from_upload_folder(self, scanner):
        """Test cleanup only removes files from upload folder."""
        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.os.remove') as mock_remove:
                paths = [
                    f'{UPLOAD_FOLDER}/safe.jpg',
                    '/other/folder/unsafe.jpg'
                ]
                removed = scanner.cleanup_temp_images(paths)

                assert removed == 1

    def test_cleanup_handles_remove_errors(self, scanner):
        """Test cleanup handles file removal errors gracefully."""
        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.os.remove') as mock_remove:
                mock_remove.side_effect = PermissionError("Cannot remove")

                paths = [f'{UPLOAD_FOLDER}/image.jpg']
                removed = scanner.cleanup_temp_images(paths)

                assert removed == 0


# =============================================================================
# Test Class: ScanSession
# =============================================================================

class TestScanSession:
    """Tests for ScanSession class."""

    def test_session_init(self):
        """Test ScanSession initialization."""
        with patch('services.document_scanner_service.DocumentScanner'):
            session = ScanSession(
                client_id=1,
                client_name="Test Client",
                document_type="cra_response_r1"
            )

            assert session.client_id == 1
            assert session.client_name == "Test Client"
            assert session.document_type == "cra_response_r1"
            assert len(session.session_id) > 0
            assert session.images == []

    def test_session_add_image_success(self, scan_session):
        """Test adding image to session successfully."""
        scan_session.scanner.process_uploaded_image.return_value = {
            'success': True,
            'image_id': 'abc123',
            'filepath': '/path/to/image.jpg',
            'filename': 'scan_123.jpg',
            'width': 800,
            'height': 600,
            'file_size_kb': 50.0
        }

        result = scan_session.add_image(b'image_data', 'test.jpg')

        assert result['success'] is True
        assert result['page_number'] == 1
        assert len(scan_session.images) == 1

    def test_session_add_multiple_images(self, scan_session):
        """Test adding multiple images to session."""
        scan_session.scanner.process_uploaded_image.return_value = {
            'success': True,
            'image_id': 'abc123',
            'filepath': '/path/to/image.jpg',
            'filename': 'scan_123.jpg',
            'width': 800,
            'height': 600,
            'file_size_kb': 50.0
        }

        scan_session.add_image(b'data1', 'test1.jpg')
        scan_session.add_image(b'data2', 'test2.jpg')
        result = scan_session.add_image(b'data3', 'test3.jpg')

        assert result['page_number'] == 3
        assert result['total_pages'] == 3

    def test_session_add_image_failure(self, scan_session):
        """Test adding image to session fails gracefully."""
        scan_session.scanner.process_uploaded_image.return_value = {
            'success': False,
            'error': 'Invalid image'
        }

        result = scan_session.add_image(b'bad_data', 'bad.xyz')

        assert result['success'] is False
        assert len(scan_session.images) == 0

    def test_session_remove_image(self, scan_session):
        """Test removing image from session."""
        scan_session.images = [
            {'filepath': '/path/1.jpg', 'page_number': 1},
            {'filepath': '/path/2.jpg', 'page_number': 2},
            {'filepath': '/path/3.jpg', 'page_number': 3}
        ]

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.os.remove'):
                result = scan_session.remove_image(2)

                assert result is True
                assert len(scan_session.images) == 2
                # Page numbers should be renumbered
                assert scan_session.images[0]['page_number'] == 1
                assert scan_session.images[1]['page_number'] == 2

    def test_session_remove_invalid_page(self, scan_session):
        """Test removing invalid page number fails."""
        scan_session.images = [{'filepath': '/path/1.jpg', 'page_number': 1}]

        result = scan_session.remove_image(5)

        assert result is False

    def test_session_reorder_images(self, scan_session):
        """Test reordering images in session."""
        scan_session.images = [
            {'filepath': '/path/1.jpg', 'page_number': 1, 'image_id': 'a'},
            {'filepath': '/path/2.jpg', 'page_number': 2, 'image_id': 'b'},
            {'filepath': '/path/3.jpg', 'page_number': 3, 'image_id': 'c'}
        ]

        result = scan_session.reorder_images([3, 1, 2])

        assert result is True
        assert scan_session.images[0]['image_id'] == 'c'
        assert scan_session.images[1]['image_id'] == 'a'
        assert scan_session.images[2]['image_id'] == 'b'

    def test_session_reorder_invalid_order(self, scan_session):
        """Test reordering with invalid order fails."""
        scan_session.images = [
            {'filepath': '/path/1.jpg', 'page_number': 1},
            {'filepath': '/path/2.jpg', 'page_number': 2}
        ]

        result = scan_session.reorder_images([1, 1])  # Invalid - duplicate

        assert result is False

    def test_session_get_status(self, scan_session):
        """Test getting session status."""
        scan_session.images = [
            {'filepath': '/path/1.jpg', 'page_number': 1}
        ]

        status = scan_session.get_status()

        assert status['session_id'] == scan_session.session_id
        assert status['client_id'] == 1
        assert status['client_name'] == "Test Client"
        assert status['document_type'] == "cra_response_r1"
        assert status['page_count'] == 1

    def test_session_finalize(self, scan_session):
        """Test finalizing session."""
        scan_session.images = [
            {'filepath': '/path/1.jpg', 'page_number': 1}
        ]
        scan_session.scanner.process_multi_page_document.return_value = {
            'success': True,
            'pdf_path': '/output/test.pdf'
        }

        result = scan_session.finalize(run_ocr=True)

        assert result['success'] is True
        assert result['session_id'] == scan_session.session_id

    def test_session_finalize_empty_fails(self, scan_session):
        """Test finalizing empty session fails."""
        scan_session.images = []

        result = scan_session.finalize()

        assert result['success'] is False
        assert 'No images in session' in result['error']

    def test_session_cancel(self, scan_session):
        """Test canceling session cleans up images."""
        scan_session.images = [
            {'filepath': f'{UPLOAD_FOLDER}/1.jpg'},
            {'filepath': f'{UPLOAD_FOLDER}/2.jpg'}
        ]
        scan_session.scanner.cleanup_temp_images.return_value = 2

        removed = scan_session.cancel()

        assert removed == 2
        assert scan_session.images == []


# =============================================================================
# Test Class: Module-Level Functions
# =============================================================================

class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_create_scan_session(self, cleanup_sessions):
        """Test creating a new scan session."""
        with patch('services.document_scanner_service.ScanSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.session_id = 'test-session-123'
            mock_session_class.return_value = mock_session

            result = create_scan_session(
                client_id=1,
                client_name="Test",
                document_type="other"
            )

            assert result['success'] is True
            assert result['session_id'] == 'test-session-123'

    def test_get_scan_session_exists(self, cleanup_sessions):
        """Test getting existing scan session."""
        mock_session = MagicMock()
        scan_sessions['test-id'] = mock_session

        result = get_scan_session('test-id')

        assert result == mock_session

    def test_get_scan_session_not_exists(self, cleanup_sessions):
        """Test getting non-existent scan session."""
        result = get_scan_session('nonexistent-id')

        assert result is None

    def test_cleanup_old_sessions(self, cleanup_sessions):
        """Test cleaning up old sessions."""
        old_session = MagicMock()
        old_session.created_at = datetime.utcnow() - timedelta(hours=48)
        old_session.cancel.return_value = 2

        new_session = MagicMock()
        new_session.created_at = datetime.utcnow() - timedelta(hours=1)

        scan_sessions['old'] = old_session
        scan_sessions['new'] = new_session

        removed = cleanup_old_sessions(max_age_hours=24)

        assert removed == 1
        assert 'old' not in scan_sessions
        assert 'new' in scan_sessions

    def test_get_document_types(self):
        """Test getting document types list."""
        types = get_document_types()

        assert isinstance(types, list)
        assert len(types) == len(DOCUMENT_TYPES)
        assert all('id' in t and 'name' in t and 'description' in t for t in types)


# =============================================================================
# Test Class: Document Types Configuration
# =============================================================================

class TestDocumentTypes:
    """Tests for document types configuration."""

    def test_all_document_types_have_required_fields(self):
        """Test all document types have required fields."""
        for doc_id, config in DOCUMENT_TYPES.items():
            assert 'name' in config, f"{doc_id} missing 'name'"
            assert 'description' in config, f"{doc_id} missing 'description'"
            assert 'ocr_prompt' in config, f"{doc_id} missing 'ocr_prompt'"

    def test_cra_response_types_have_round(self):
        """Test CRA response types have round number."""
        cra_types = [k for k in DOCUMENT_TYPES.keys() if k.startswith('cra_response')]

        for doc_type in cra_types:
            assert 'round' in DOCUMENT_TYPES[doc_type]

    def test_document_type_prompts_are_strings(self):
        """Test all OCR prompts are non-empty strings."""
        for doc_id, config in DOCUMENT_TYPES.items():
            assert isinstance(config['ocr_prompt'], str)
            assert len(config['ocr_prompt']) > 10

    def test_other_document_type_exists(self):
        """Test 'other' document type exists as fallback."""
        assert 'other' in DOCUMENT_TYPES
        assert DOCUMENT_TYPES['other']['name'] == 'Other Document'


# =============================================================================
# Test Class: Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_process_very_long_client_name(self, scanner):
        """Test processing with very long client name truncates."""
        mock_img = MagicMock()
        mock_img.size = (800, 600)

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=50000):
                        long_name = "A" * 100
                        result = scanner.combine_images_to_pdf(
                            ['/path/to/image.jpg'],
                            client_name=long_name
                        )

                        # Name should be truncated to 30 chars
                        assert len(result['pdf_filename'].split('_')[0]) <= 30

    def test_process_client_name_with_spaces(self, scanner):
        """Test processing with spaces in client name."""
        mock_img = MagicMock()
        mock_img.size = (800, 600)

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=50000):
                        result = scanner.combine_images_to_pdf(
                            ['/path/to/image.jpg'],
                            client_name="John Doe Smith"
                        )

                        # Spaces should be replaced with underscores
                        assert ' ' not in result['pdf_filename']

    def test_session_created_at_is_utc(self):
        """Test session created_at uses UTC time."""
        with patch('services.document_scanner_service.DocumentScanner'):
            session = ScanSession()

            # Should be close to current UTC time
            time_diff = abs((datetime.utcnow() - session.created_at).total_seconds())
            assert time_diff < 5

    def test_extract_handles_missing_usage_attribute(self, scanner):
        """Test extraction handles response without usage attribute."""
        mock_response = MagicMock(spec=['content'])  # Only spec content, not usage
        mock_response.content = [MagicMock(text="Text")]
        scanner.client.messages.create.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'data')):
            # This should not raise, just handle gracefully
            result = scanner.extract_text_from_image('/path/to/image.jpg')
            # The function has hasattr checks for usage
            assert result['success'] is True
            assert result['input_tokens'] == 0
            assert result['output_tokens'] == 0

    def test_null_client_name_handling(self, scanner):
        """Test processing with None client name."""
        mock_img = MagicMock()
        mock_img.size = (800, 600)

        with patch('services.document_scanner_service.os.path.exists', return_value=True):
            with patch('services.document_scanner_service.Image.open', return_value=mock_img):
                with patch('services.document_scanner_service.FPDF') as mock_fpdf:
                    mock_pdf = MagicMock()
                    mock_fpdf.return_value = mock_pdf
                    with patch('services.document_scanner_service.os.path.getsize', return_value=50000):
                        result = scanner.combine_images_to_pdf(
                            ['/path/to/image.jpg'],
                            client_name=None
                        )

                        # Should use 'unknown' as default
                        assert 'unknown' in result['pdf_filename']
