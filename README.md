# AI RSS News Analyzer

An AI-powered RSS news aggregation and analysis system that supports multilingual (Chinese/English) news sources, performs sentiment analysis, and provides real-time push notifications.

## Features

- Multilingual RSS feed subscription and aggregation
- AI-powered news content and sentiment analysis
- Multiple notification channels (WeChat Work, DingTalk, etc.)
- Custom keyword filtering and categorization
- Scheduled task management
- MongoDB persistence

## Tech Stack

- Python 3.11+
- MongoDB
- FastAPI
- APScheduler
- Multiple AI Model Support (DeepSeek, Dify, etc.)

## Installation

1. Clone the repository
```bash
git clone https://github.com/Richard0047/-ai-rss-analyzer.git
cd -ai-rss-analyzer
```

2. Create and activate virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
```
Then edit the `.env` file with your configuration details.

## Configuration

### Required Settings
- MongoDB connection details
- AI model API keys (at least one)
- Notification channel settings (at least one)

### RSS Source Configuration
In `src/config.py`, you can:
- Add/remove RSS sources
- Modify keyword filtering rules
- Adjust scheduling frequencies

## Usage

1. Start the service
```bash
python src/main.py
```

2. View API documentation
```
Visit http://localhost:8000/docs
```

3. Monitor logs
```bash
tail -f logs/app.log
```

## Scheduled Tasks

The system includes three main scheduled tasks:
- News fetching: Every 30 minutes
- AI analysis: Every 30 minutes
- Notification pushing: Every 2 hours

Frequencies can be adjusted in the `SCHEDULE` configuration in `src/config.py`.

## Development Guide

### Project Structure
```
.
├── src/
│   ├── config.py         # Configuration file
│   ├── main.py          # Main program
│   └── utils/           # Utility functions
├── requirements.txt     # Dependencies
├── .env.example        # Environment template
└── README.md          # Documentation
```

### Adding New Features
1. New RSS sources: Add to `RSS_SOURCES` in `config.py`
2. New keywords: Add to `KEYWORDS` in `config.py`
3. New notification channels: Add corresponding modules in `utils` directory

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Contact

Richard Lin - richardlin0047@gmail.com

Project Link: [https://github.com/Richard0047/-ai-rss-analyzer](https://github.com/Richard0047/-ai-rss-analyzer)
