# Passport Data Extractor

A Streamlit application that uses the [Extend AI](https://extend.ai) API to extract structured data from passport documents. This application allows users to upload passport images or PDFs and receive extracted information in structured formats (CSV, JSON).

For any questions, contact me @ victor.soto@hec.edu

## Features

- **Passport Document Processing**: Upload and process passport images (PNG, JPG, JPEG) or PDFs
- **Advanced Data Extraction**: Uses Extend AI's advanced document processing API
- **Multiple Export Formats**: Download extracted data as CSV, JSON, or raw API response
- **Extraction History**: Track and review previous extractions
- **Containerized Deployment**: Ready for Docker deployment
- **Comprehensive Testing**: Includes unit tests for all core functionality

## Prerequisites

- Python 3.8+
- Extend AI API token — go and get your API token on [Extend AI Platform](https://extend.ai).
- Extend AI processor ID configured for passport extraction

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd passeport-extractor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp env.example .env
# Edit .env with your Extend AI API credentials
```

4. Run the application:
```bash
streamlit run main.py
```

The application will be available at `http://localhost:8501`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t passport-extractor .
```

2. Run the container:
```bash
docker run -p 8501:8501 passport-extractor
```

Or use Docker Compose:
```bash
docker-compose up
```

## Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Extend AI API Configuration
EXTEND_API_TOKEN=<your-API-key>
EXTEND_PROCESSOR_ID=<ID-of-the-configured-processor>
```

### Extend AI Setup

1. Sign up for an Extend AI account at [extend.ai](https://extend.ai)
2. Create a new processor for passport extraction or use the template provided by the Extend AI team
3. Configure your extraction schema for passport fields
4. Get your API token and processor ID

## Usage

1. **Configure API Access**: Enter your Extend AI API token and processor ID in the sidebar
2. **Upload Document**: Choose a passport image or PDF file
3. **Extract Data**: Click "Extract Passport Data" to process the document
4. **Download Results**: Export extracted data in your preferred format (CSV, JSON, or raw)
5. **Review History**: Access previous extractions in the "Extraction History" tab

## API Integration

The application uses the Extend AI Python client:

```python
from extend_ai import Extend

# Initialize the client
client = Extend(token="YOUR_EXTEND_API_TOKEN")

# Upload file
with open("passport.pdf", "rb") as f:
    upload_response = client.file.upload(file=f)

file_id = upload_response.file.id

# Extract passport data
response = client.processor_run.create(
    processor_id="dp_jT1DNo-oQE5mhdB5YqUcO",
    file={"fileId": file_id},
    sync=True,
    config={
        "type": "EXTRACT",
        "baseProcessor": "extraction_performance",
        "baseVersion": "4.2.0",
        "schema": {
            # ... passport extraction schema
        }
    }
)
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=main --cov-report=html
```

## Project Structure

```
passeport-extractor/
├── main.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── env.example             # Environment variables template
├── README.md               # This file
└── tests/
    ├── __init__.py
    └── test_passport_extractor.py  # Test suite
```

## Supported File Formats

- **Images**: PNG, JPG, JPEG
- **Documents**: PDF

## Data Export Formats

- **CSV**: Comma-separated values for spreadsheet applications
- **JSON**: Structured data format for programmatic use
- **Raw Response**: Complete API response from Extend AI

## Security Considerations

- API tokens are handled securely through environment variables
- Temporary files are automatically cleaned up after processing
- No sensitive data is stored permanently in the application

## Troubleshooting

### Common Issues

1. **API Token Invalid**: Verify your Extend AI API token in the sidebar
2. **Processor ID Not Found**: Ensure your processor ID is correct and the processor exists
3. **File Upload Failed**: Check file format and size (max 200MB)
4. **Extraction Failed**: Verify document quality and format

### Error Messages

- `Failed to initialize Extend client`: Check API token configuration
- `Failed to extract passport data`: Verify processor ID and document format
- `No extractions performed yet`: Upload and process a document first

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is provided as-is for educational and development purposes.

## Support

For issues with the Extend AI API, consult the [Extend AI documentation](https://extend.ai/docs).

For application-specific issues, please check the troubleshooting section or create an issue in the repository.