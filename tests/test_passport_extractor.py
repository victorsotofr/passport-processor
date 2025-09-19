import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch
import sys

# Add the parent directory to the path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import (
        format_extraction_data,
        convert_df_to_csv,
        convert_df_to_json,
        save_extraction_to_history,
    )
except ImportError:
    # If import fails, skip tests
    pytest.skip("Cannot import main module", allow_module_level=True)


class TestPassportExtractor:
    """Test suite for passport extraction functionality."""

    def test_format_extraction_data_with_dict(self):
        """Test formatting extraction data from a dictionary."""
        mock_data = {
            "surname": "Doe",
            "given_names": "John, William",
            "passport_number": "A1234567",
            "nationality": "United States",
        }

        df = format_extraction_data(mock_data)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "surname" in df.columns
        assert df.iloc[0]["surname"] == "Doe"

    def test_format_extraction_data_with_nested_dict(self):
        """Test formatting extraction data with nested structure."""
        mock_data = {
            "data": {
                "surname": "Smith",
                "given_names": "Jane, Marie",
                "passport_number": "B9876543",
                "nationality": "Canada",
            }
        }

        df = format_extraction_data(mock_data)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "surname" in df.columns
        assert df.iloc[0]["surname"] == "Smith"

    def test_format_extraction_data_with_list(self):
        """Test formatting extraction data from a list."""
        mock_data = [
            {"surname": "Doe", "passport_number": "A1234567"},
            {"surname": "Smith", "passport_number": "B9876543"},
        ]

        df = format_extraction_data(mock_data)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "surname" in df.columns
        assert df.iloc[0]["surname"] == "Doe"
        assert df.iloc[1]["surname"] == "Smith"

    def test_format_extraction_data_with_invalid_input(self):
        """Test formatting extraction data with invalid input."""
        mock_data = "invalid_data"

        df = format_extraction_data(mock_data)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "extracted_data" in df.columns

    def test_convert_df_to_csv(self):
        """Test converting DataFrame to CSV format."""
        df = pd.DataFrame(
            {"surname": ["Doe", "Smith"], "passport_number": ["A1234567", "B9876543"]}
        )

        csv_string = convert_df_to_csv(df)

        assert isinstance(csv_string, str)
        assert "surname,passport_number" in csv_string
        assert "Doe,A1234567" in csv_string
        assert "Smith,B9876543" in csv_string

    def test_convert_df_to_json(self):
        """Test converting DataFrame to JSON format."""
        df = pd.DataFrame({"surname": ["Doe"], "passport_number": ["A1234567"]})

        json_string = convert_df_to_json(df)

        assert isinstance(json_string, str)
        assert "Doe" in json_string
        assert "A1234567" in json_string

    @patch("streamlit.session_state")
    def test_save_extraction_to_history(self, mock_session_state):
        """Test saving extraction to session history."""
        # Setup mock session state
        mock_session_state.extraction_history = []

        df = pd.DataFrame({"surname": ["Doe"], "passport_number": ["A1234567"]})
        filename = "test_passport.pdf"

        save_extraction_to_history(df, filename)

        # Verify history was updated
        assert len(mock_session_state.extraction_history) == 1
        entry = mock_session_state.extraction_history[0]
        assert entry["filename"] == filename
        assert entry["record_count"] == 1
        assert "timestamp" in entry
        assert isinstance(entry["data"], pd.DataFrame)


class TestExtendAIIntegration:
    """Test suite for Extend AI API integration."""

    @patch("main.Extend")
    def test_initialize_extend_client_success(self, mock_extend):
        """Test successful Extend AI client initialization."""
        from main import initialize_extend_client

        mock_client = Mock()
        mock_extend.return_value = mock_client

        client = initialize_extend_client("test_api_token")

        assert client == mock_client
        mock_extend.assert_called_once_with(token="test_api_token")

    @patch("main.Extend")
    @patch("streamlit.error")
    def test_initialize_extend_client_failure(self, mock_st_error, mock_extend):
        """Test failed Extend AI client initialization."""
        from main import initialize_extend_client

        mock_extend.side_effect = Exception("API token invalid")

        client = initialize_extend_client("invalid_token")

        assert client is None
        mock_st_error.assert_called_once()

    @patch("main.Extend")
    @patch("streamlit.spinner")
    @patch("builtins.open", create=True)
    def test_extract_passport_data_success(self, mock_open, mock_spinner, mock_extend):
        """Test successful passport data extraction."""
        from main import extract_passport_data

        # Setup mocks
        mock_client = Mock()
        mock_file_response = Mock()
        mock_file_response.file.id = "file_test123"
        mock_client.file.upload.return_value = mock_file_response

        mock_processor_response = Mock()
        mock_processor_response.processor_run.output.value = {
            "surname": "Doe",
            "given_names": "John, William",
            "passport_number": "A1234567",
        }
        mock_client.processor_run.create.return_value = mock_processor_response

        mock_spinner.return_value.__enter__ = Mock()
        mock_spinner.return_value.__exit__ = Mock()

        result = extract_passport_data(
            mock_client, "test_path.pdf", "test_processor_id"
        )

        assert result == mock_processor_response.processor_run.output.value
        mock_client.file.upload.assert_called_once()
        mock_client.processor_run.create.assert_called_once()

    @patch("main.Extend")
    @patch("streamlit.error")
    @patch("streamlit.spinner")
    def test_extract_passport_data_failure(
        self, mock_spinner, mock_st_error, mock_extend
    ):
        """Test failed passport data extraction."""
        from main import extract_passport_data

        # Setup mocks
        mock_client = Mock()
        mock_client.file.upload.side_effect = Exception("Upload failed")
        mock_spinner.return_value.__enter__ = Mock()
        mock_spinner.return_value.__exit__ = Mock()

        result = extract_passport_data(
            mock_client, "test_path.pdf", "test_processor_id"
        )

        assert result is None
        mock_st_error.assert_called_once()


class TestFileHandling:
    """Test suite for file handling functionality."""

    def test_temporary_file_creation(self):
        """Test temporary file handling for uploads."""
        test_content = b"fake pdf content"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            # Verify file exists and has content
            assert os.path.exists(temp_file_path)
            with open(temp_file_path, "rb") as f:
                content = f.read()
            assert content == test_content
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_supported_file_extensions(self):
        """Test that supported file extensions are handled correctly."""
        supported_extensions = [".pdf", ".png", ".jpg", ".jpeg"]

        for ext in supported_extensions:
            filename = f"test_passport{ext}"
            assert any(
                filename.lower().endswith(supported_ext.lower())
                for supported_ext in supported_extensions
            )


class TestPassportSchema:
    """Test suite for passport extraction schema validation."""

    def test_passport_schema_fields(self):
        """Test that all required passport fields are present."""
        required_fields = [
            "sex",
            "type",
            "height",
            "surname",
            "eye_color",
            "residence",
            "given_names",
            "nationality",
            "country_code",
            "date_of_birth",
            "date_of_issue",
            "date_of_expiry",
            "place_of_birth",
            "passport_number",
            "holder_signature",
            "issuing_authority",
            "machine_readable_zone",
        ]

        mock_passport_data = {field: f"test_{field}" for field in required_fields}

        df = format_extraction_data(mock_passport_data)

        # Verify all required fields are present in the DataFrame
        for field in required_fields:
            assert field in df.columns

    def test_passport_data_types(self):
        """Test passport data type handling."""
        passport_data = {
            "sex": "M",
            "type": "P",
            "height": "1,83 m",
            "surname": "SOTO",
            "eye_color": "MARRON",
            "residence": "123 Test Street, Test City",
            "given_names": "Victor, Paul, André",
            "nationality": "Française",
            "country_code": "FRA",
            "date_of_birth": "2001-05-08",
            "date_of_issue": "2019-08-01",
            "date_of_expiry": "2029-07-31",
            "place_of_birth": "ROUEN",
            "passport_number": "19EC41504",
            "holder_signature": "[signature present]",
            "issuing_authority": "Préfecture du Rhône LYON",
            "machine_readable_zone": "P<FRASOTO<<VICTOR<PAUL<ANDRE<<<<<<<<<<<<<<19EC415044FRA0105086M2907310<<<<<<<<<<<<08",
        }

        df = format_extraction_data(passport_data)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["surname"] == "SOTO"
        assert df.iloc[0]["passport_number"] == "19EC41504"


if __name__ == "__main__":
    pytest.main([__file__])
