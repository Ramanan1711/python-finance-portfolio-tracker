# Python Finance Portfolio Tracker

A comprehensive portfolio tracking application with web dashboard and reporting capabilities.

## Features

- Real-time stock portfolio tracking
- Interactive web dashboard
- PDF and Excel report generation
- Price alerts system
- Portfolio analysis and metrics
- Real-time data fetching
- Docker containerization

## Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the web dashboard:
```bash
streamlit run src/dashboard.py
```

## Docker Deployment

### Using Docker Compose (Recommended)

1. Build and run the application:
```bash
docker-compose up -d
```

2. Access the dashboard at `http://localhost:8501`

3. Stop the application:
```bash
docker-compose down
```

### Using Docker Directly

1. Build the image:
```bash
docker build -t portfolio-tracker .
```

2. Run the container:
```bash
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  --name portfolio-tracker \
  portfolio-tracker
```

3. Access the dashboard at `http://localhost:8501`

4. Stop the container:
```bash
docker stop portfolio-tracker
```

## Project Structure

```
python-finance-portfolio-tracker/
├── src/
│   ├── dashboard.py         # Streamlit web interface
│   ├── portfolio.py         # Core portfolio logic
│   ├── api_fetcher.py       # Stock data fetching
│   ├── analyzer.py          # Portfolio analysis
│   ├── alerts.py            # Price alerts system
│   └── report_generator.py  # PDF/Excel report generation
├── data/
│   ├── sample-portfolio.csv # Sample portfolio data
│   └── alerts.json         # Price alerts configuration
├── reports/                 # Generated reports directory
├── templates/              # Report templates
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
└── requirements.txt       # Python dependencies
```

## Environment Variables

The application uses the following environment variables:

- `PYTHONPATH`: Set to `/app` in Docker
- `PYTHONUNBUFFERED`: Set to `1` for unbuffered output

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request
