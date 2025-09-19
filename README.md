# Passport Data Extractor

For those who want to quickly extract data from passports ⚡️

## 1. Initialization

Go on [Extend AI](https://extend.ai), configure an extraction processor for Passports, get an API key & Processor ID

```bash
EXTEND_API_TOKEN=<your-API-key>
EXTEND_PROCESSOR_ID=<ID-of-the-configured-processor>
```

## 2. Run

### Locally

```bash
git clone <repository-url>
cd passeport-extractor

pip install -r requirements.txt

cp env.example .env

streamlit run main.py
```

### Docker

1. Build the Docker image:
```bash
docker build -t passport-extractor .

docker run -p 8501:8501 passport-extractor
```

Or use Docker Compose:
```bash
docker-compose up
```
---

## Features

- **Passport Document Processing**: Upload and process passport images (PNG, JPG, JPEG) or PDFs
- **Advanced Data Extraction**: Uses Extend AI's advanced document processing API
- **Multiple Export Formats**: Download extracted data as CSV, JSON, or raw API response
- **Extraction History**: Track and review previous extractions
- **Containerized Deployment**: Ready for Docker deployment
- **Comprehensive Testing**: Includes unit tests for all core functionality

---

For any questions, contact me @ victor.soto@hec.edu