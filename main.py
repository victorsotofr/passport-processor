# IMPORTANT: Fix typing compatibility BEFORE any other imports
import sys
if sys.version_info < (3, 12):
    try:
        import typing
        from typing_extensions import TypedDict, NotRequired, Required, Self
        # Aggressively monkey patch typing module
        typing.TypedDict = TypedDict
        typing.NotRequired = NotRequired
        typing.Required = Required
        typing.Self = Self
        # Also patch the module in sys.modules to ensure all imports see the patch
        sys.modules['typing'].TypedDict = TypedDict
        sys.modules['typing'].NotRequired = NotRequired
        sys.modules['typing'].Required = Required
        sys.modules['typing'].Self = Self
    except ImportError:
        pass

import streamlit as st
import pandas as pd
import os
import io
import json
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import extend_ai, fall back to mock if not available
EXTEND_AVAILABLE = False
try:
    from extend_ai import Extend
    EXTEND_AVAILABLE = True
    print("✅ Extend AI package imported successfully")
except ImportError as e:
    print(f"⚠️ Failed to import extend_ai: {e}")
    EXTEND_AVAILABLE = False
except Exception as e:
    print(f"⚠️ Failed to import extend_ai due to compatibility issue: {e}")
    EXTEND_AVAILABLE = False
    # Create a mock Extend class for demonstration
    class Extend:
        def __init__(self, token: str):
            self.token = token
            self.file = MockFile()
            self.processor_run = MockProcessorRun()
    
    class MockFile:
        def upload(self, file):
            # Return mock file upload response
            class MockFileResponse:
                def __init__(self):
                    self.file = MockFileObject()
            return MockFileResponse()
    
    class MockFileObject:
        def __init__(self):
            self.id = "file_mock123456"
    
    class MockProcessorRun:
        def create(self, processor_id: str, file: dict, sync: bool, config: dict):
            # Return mock passport data - this should be updated based on actual Extend response structure
            return MockProcessorResponse()
    
    class MockProcessorResponse:
        def __init__(self):
            self.processor_run = MockProcessorRunObject()
    
    class MockProcessorRunObject:
        def __init__(self):
            self.output = MockOutput()
    
    class MockOutput:
        def __init__(self):
            self.value = {
                "sex": "M",
                "type": "P", 
                "height": "1,83 m",
                "surname": "MOCK",
                "eye_color": "MARRON",
                "residence": "123 MOCK STREET MOCK CITY 12345 FRANCE",
                "given_names": "John, William",
                "nationality": "Française",
                "country_code": "FRA",
                "date_of_birth": "1990-01-15",
                "date_of_issue": "2020-03-10",
                "date_of_expiry": "2030-03-09",
                "place_of_birth": "MOCK CITY",
                "passport_number": "MOCK123456",
                "holder_signature": "[signature present]",
                "issuing_authority": "Mock Authority",
                "machine_readable_zone": "P<FRAMOCK<<JOHN<WILLIAM<<<<<<<<<<<<<<<MOCK1234566FRA9001158M3003096<<<<<<<<<<<<<<<08",
                "_demo_note": "DEMO MODE - Mock data (replace with actual Extend response structure)"
            }

######################################################################
# CONFIGURATION
######################################################################
st.set_page_config(
    page_title="Passport Data Extractor", 
    page_icon="", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "extraction_history" not in st.session_state:
    st.session_state.extraction_history = []

if "current_extraction" not in st.session_state:
    st.session_state.current_extraction = None

######################################################################
# HELPER FUNCTIONS
######################################################################

def initialize_extend_client(api_token: str) -> Optional[Extend]:
    """Initialize Extend client with API token."""
    try:
        return Extend(token=api_token)
    except Exception as e:
        st.error(f"Failed to initialize Extend client: {str(e)}")
        return None

def extract_passport_data(client: Extend, file_path: str, processor_id: str) -> Optional[Dict[Any, Any]]:
    """Extract data from passport document using Extend AI."""
    try:
        with st.spinner("Extracting passport data..."):
            # Upload file
            with open(file_path, "rb") as f:
                upload_response = client.file.upload(file=f)
            
            # Extract the file ID from the upload response
            file_id = upload_response.file.id
            
            # Run the processor with the passport extraction schema
            response = client.processor_run.create(
                processor_id=processor_id,
                file={"fileId": file_id},
                sync=True,
                config={
                    "type": "EXTRACT",
                    "baseProcessor": "extraction_performance",
                    "baseVersion": "4.2.0",
                    "schema": {
                        "type": "object",
                        "required": [
                            "sex", "type", "height", "surname", "eye_color", "residence",
                            "given_names", "nationality", "country_code", "date_of_birth",
                            "date_of_issue", "date_of_expiry", "place_of_birth",
                            "passport_number", "holder_signature", "issuing_authority",
                            "machine_readable_zone"
                        ],
                        "properties": {
                            "sex": {
                                "type": ["string", "null"],
                                "description": "The gender or sex of the passport holder as indicated in the document. May be represented as 'M', 'F', or other designations. Commonly labeled as 'Sex', 'Sexe', or similar."
                            },
                            "type": {
                                "type": ["string", "null"],
                                "description": "The document type code, usually a single letter such as 'P' for passport. Commonly labeled as 'Type' or similar."
                            },
                            "height": {
                                "type": ["string", "null"],
                                "description": "The height of the passport holder as recorded in the document. May be given in meters, centimeters, or feet/inches, and is often labeled as 'Height', 'Taille', or similar."
                            },
                            "surname": {
                                "type": ["string", "null"],
                                "description": "The family name or last name of the passport holder as it appears on the document. Commonly labeled as 'Surname', 'Nom', or similar. This is the primary legal surname for identification."
                            },
                            "eye_color": {
                                "type": ["string", "null"],
                                "description": "The color of the passport holder's eyes as stated in the document. Commonly labeled as 'Eye Color', 'Couleur des yeux', or similar. May use color names or codes."
                            },
                            "residence": {
                                "type": ["string", "null"],
                                "description": "The address or place of residence of the passport holder as recorded in the document. May include street, city, postal code, and country. Commonly labeled as 'Residence', 'Domicile', or similar."
                            },
                            "given_names": {
                                "type": ["string", "null"],
                                "description": "The given names (first and middle names) of the passport holder as listed on the document. May include multiple names separated by spaces or commas. Commonly labeled as 'Given Names', 'Prénoms', or similar."
                            },
                            "nationality": {
                                "type": ["string", "null"],
                                "description": "The official nationality or citizenship of the passport holder as stated on the document. Commonly labeled as 'Nationality', 'Nationalité', or similar."
                            },
                            "country_code": {
                                "type": ["string", "null"],
                                "description": "The three-letter country code representing the issuing country of the passport, typically following ISO 3166-1 alpha-3 format. Commonly labeled as 'Country Code', 'Code du pays', or similar."
                            },
                            "date_of_birth": {
                                "type": ["string", "null"],
                                "description": "The birth date of the passport holder. This is the official date of birth as recorded in the passport, typically labeled as 'Date of Birth', 'Date de naissance', or similar. Format may vary but should be interpreted as a date.",
                                "extend:type": "date"
                            },
                            "date_of_issue": {
                                "type": ["string", "null"],
                                "description": "The date on which the passport was issued. This is the official start date of the document's validity, often labeled as 'Date of Issue', 'Date de délivrance', or similar.",
                                "extend:type": "date"
                            },
                            "date_of_expiry": {
                                "type": ["string", "null"],
                                "description": "The date on which the passport expires. This is the last date the document is valid for travel, commonly labeled as 'Date of Expiry', 'Date d'expiration', or similar.",
                                "extend:type": "date"
                            },
                            "place_of_birth": {
                                "type": ["string", "null"],
                                "description": "The city, region, or country where the passport holder was born, as stated in the document. Commonly labeled as 'Place of Birth', 'Lieu de naissance', or similar."
                            },
                            "passport_number": {
                                "type": ["string", "null"],
                                "description": "The unique identifier assigned to this passport. This is the primary reference number for the document, often labeled as 'Passport No', 'Passeport nº', or similar. It may contain letters and numbers and is used for official identification."
                            },
                            "holder_signature": {
                                "type": ["string", "null"],
                                "description": "The signature of the passport holder as it appears on the document. This may be a handwritten or digital signature, and is often labeled as 'Holder's signature', 'Signature du titulaire', or similar."
                            },
                            "issuing_authority": {
                                "type": ["string", "null"],
                                "description": "The name of the authority or agency that issued the passport. This may be a government office, ministry, or other official body, and is often labeled as 'Authority', 'Autorité', or similar."
                            },
                            "machine_readable_zone": {
                                "type": ["string", "null"],
                                "description": "The machine-readable zone (MRZ) text at the bottom of the passport identity page. This is a standardized string of characters used for automated document reading and verification. Typically consists of two or three lines of letters, numbers, and chevrons ('<')."
                            }
                        },
                        "additionalProperties": False
                    },
                    "advancedOptions": {
                        "citationsEnabled": True,
                        "chunkingOptions": {},
                        "advancedFigureParsingEnabled": True
                    }
                }
            )
        
        # Debug: Print the actual structure returned by Extend
        if EXTEND_AVAILABLE:
            st.write("**Debug - Actual Extend Response Structure:**")
            st.code(str(response))
            print("=== EXTEND COMPLETION RESPONSE ===")
            print(response)
            print("=== END EXTEND RESPONSE ===")
        
        # Extract the actual data from the response
        if hasattr(response, 'processor_run') and hasattr(response.processor_run, 'output'):
            return response.processor_run.output.value
        else:
            return response
        
    except Exception as e:
        st.error(f"Failed to extract passport data: {str(e)}")
        return None

def format_extraction_data(extraction_result: Dict[Any, Any]) -> pd.DataFrame:
    """Format extraction result into a pandas DataFrame with flattened nested objects."""
    try:
        # Handle different possible response formats from Extend
        if isinstance(extraction_result, dict):
            if 'data' in extraction_result:
                data = extraction_result['data']
            else:
                data = extraction_result
            
            # If data is a list, convert to records
            if isinstance(data, list):
                flattened_data = []
                for item in data:
                    flattened_data.append(_flatten_nested_dict(item))
                return pd.DataFrame(flattened_data)
            # If data is a dict, flatten nested objects and convert to single row DataFrame
            elif isinstance(data, dict):
                flattened_data = _flatten_nested_dict(data)
                return pd.DataFrame([flattened_data])
            else:
                # Fallback: create DataFrame with raw data
                return pd.DataFrame([{"extracted_data": str(data)}])
        elif isinstance(extraction_result, list):
            # Handle direct list input
            flattened_data = []
            for item in extraction_result:
                flattened_data.append(_flatten_nested_dict(item) if isinstance(item, dict) else item)
            return pd.DataFrame(flattened_data)
        else:
            return pd.DataFrame([{"extracted_data": str(extraction_result)}])
    except Exception as e:
        st.error(f"Failed to format extraction data: {str(e)}")
        return pd.DataFrame([{"error": str(e)}])

def _flatten_nested_dict(data: Dict[Any, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flatten nested dictionary for better DataFrame display."""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict) and v:  # Only flatten non-empty dicts
            items.extend(_flatten_nested_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list) and v:  # Handle non-empty lists
            if all(isinstance(item, str) for item in v):
                # If list of strings, join them
                items.append((new_key, '; '.join(v)))
            else:
                # For complex lists, convert to string representation
                items.append((new_key, str(v)))
        else:
            # Handle None values and regular values
            items.append((new_key, v))
    return dict(items)

def save_extraction_to_history(extraction_data: pd.DataFrame, filename: str):
    """Save extraction result to session history."""
    history_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filename": filename,
        "data": extraction_data,
        "record_count": len(extraction_data)
    }
    st.session_state.extraction_history.append(history_entry)

def convert_df_to_csv(df: pd.DataFrame) -> str:
    """Convert DataFrame to CSV string."""
    return df.to_csv(index=False)

def convert_df_to_json(df: pd.DataFrame) -> str:
    """Convert DataFrame to JSON string."""
    return df.to_json(orient='records', indent=2)

######################################################################
# MAIN UI
######################################################################

# Sidebar
st.sidebar.title("🛂 Passport Extractor")
st.sidebar.markdown("---")

# API Configuration
st.sidebar.subheader("🔑 Extend AI Configuration")

# Load default values from environment variables
default_api_token = os.getenv("EXTEND_API_TOKEN", "")
default_processor_id = os.getenv("EXTEND_PROCESSOR_ID", "dp_jT1DNo-oQE5mhdB5YqUcO")

api_token = st.sidebar.text_input(
    "Extend API Token", 
    value=default_api_token,
    type="password",
    help="Enter your Extend AI API token (can be set in .env file)"
)

processor_id = st.sidebar.text_input(
    "Processor ID",
    value=default_processor_id,
    help="Enter your Extend processor ID for passport extraction (can be set in .env file)"
)

# Navigation
page = st.sidebar.selectbox(
    "Navigate to:",
    ["Extract Passport", "Extraction History", "Settings"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Built for Passport Data Extraction**")

# Main content
if page == "Extract Passport":
    st.title("🛂 Passport Data Extractor")
    if not EXTEND_AVAILABLE:
        st.error("""
        ❌ **Extend AI Package Error**: The extend-ai package could not be loaded properly. 
        This is likely due to package compatibility issues.
        The app will use mock data for demonstration purposes.
        
        **To fix this:**
        1. Ensure you're using Python 3.8+ 
        2. Try: `pip install extend-ai --force-reinstall`
        3. If issues persist, use Docker deployment for a clean environment
        """)
    elif EXTEND_AVAILABLE and not api_token:
        st.info("""
        ℹ️ **Ready for Real API Calls**: Extend AI package is available! 
        Please provide your API token to process real passport documents.
        """)
    
    st.markdown("""
    Upload passport images or PDFs to extract structured data using Extend AI's advanced document processing capabilities.
    
    **Supported formats:** PDF, PNG, JPG, JPEG
    """)
    
    # Check if API token is provided
    if not api_token:
        st.warning("⚠️ Please provide your Extend API token in the sidebar to continue.")
        st.stop()
    
    # Initialize Extend client
    client = initialize_extend_client(api_token)
    if not client:
        st.stop()
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a passport document",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Upload a clear image or PDF of a passport"
    )
    
    if uploaded_file is not None:
        # Display uploaded file info
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info(f"📄 **File:** {uploaded_file.name}")
            st.info(f"📊 **Size:** {uploaded_file.size / 1024:.1f} KB")
            st.info(f"🗂️ **Type:** {uploaded_file.type}")
        
        with col2:
            if uploaded_file.type.startswith('image'):
                st.image(uploaded_file, caption="Uploaded Passport", use_column_width=True)
        
        # Extract button
        if st.button("🔍 Extract Passport Data", type="primary"):
            if not processor_id:
                st.error("Please provide a Processor ID in the sidebar.")
                st.stop()
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path = temp_file.name
            
            try:
                # Extract data using Extend
                extraction_result = extract_passport_data(client, temp_file_path, processor_id)
                
                if extraction_result:
                    # Format and display results
                    df = format_extraction_data(extraction_result)
                    st.session_state.current_extraction = df
                    
                    # Save to history
                    save_extraction_to_history(df, uploaded_file.name)
                    
                    st.success("✅ Passport data extracted successfully!")
                    
                    # Display extraction results
                    st.subheader("📋 Extracted Data")
                    st.dataframe(df, use_container_width=True)
                    
                    # Download options
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        csv_data = convert_df_to_csv(df)
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv_data,
                            file_name=f"passport_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        json_data = convert_df_to_json(df)
                        st.download_button(
                            label="📥 Download as JSON",
                            data=json_data,
                            file_name=f"passport_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    with col3:
                        # Raw response download
                        raw_data = json.dumps(extraction_result, indent=2)
                        st.download_button(
                            label="📥 Download Raw Response",
                            data=raw_data,
                            file_name=f"passport_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

elif page == "Extraction History":
    st.title("📚 Extraction History")
    
    if not st.session_state.extraction_history:
        st.info("No extractions performed yet. Go to 'Extract Passport' to get started!")
    else:
        st.markdown(f"**Total extractions:** {len(st.session_state.extraction_history)}")
        
        # Display history
        for i, entry in enumerate(reversed(st.session_state.extraction_history)):
            with st.expander(f"🗓️ {entry['timestamp']} - {entry['filename']} ({entry['record_count']} records)"):
                st.dataframe(entry['data'], use_container_width=True)
                
                # Download options for historical data
                col1, col2 = st.columns(2)
                with col1:
                    csv_data = convert_df_to_csv(entry['data'])
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"passport_data_{entry['timestamp'].replace(':', '-').replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"csv_{i}"
                    )
                
                with col2:
                    json_data = convert_df_to_json(entry['data'])
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name=f"passport_data_{entry['timestamp'].replace(':', '-').replace(' ', '_')}.json",
                        mime="application/json",
                        key=f"json_{i}"
                    )
        
        # Clear history button
        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.extraction_history = []
            st.rerun()

elif page == "Settings":
    st.title("⚙️ Settings")
    
    st.subheader("🔧 Configuration")
    st.write("**Current Extend AI Configuration:**")
    
    if api_token:
        st.success("✅ API Token is configured")
    else:
        st.error("❌ API Token is not configured")
    
    if processor_id:
        st.success(f"✅ Processor ID: {processor_id}")
    else:
        st.error("❌ Processor ID is not configured")
    
    st.subheader("📊 Session Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Extractions This Session", len(st.session_state.extraction_history))
    
    with col2:
        current_extraction_status = "Available" if st.session_state.current_extraction is not None else "None"
        st.metric("Current Extraction", current_extraction_status)
    
    st.subheader("ℹ️ About")
    st.markdown("""
    **Passport Data Extractor v2.0**
    
    This application uses Extend AI's advanced document processing API to extract structured data from passport documents.
    
    **Features:**
    - Support for PDF and image formats
    - Structured data extraction
    - CSV and JSON export
    - Extraction history tracking
    - Containerized deployment ready
    
    **Usage:**
    1. Configure your Extend AI API token and processor ID
    2. Upload a passport document
    3. Extract structured data
    4. Download results in your preferred format
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("*Powered by Extend AI*")