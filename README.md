# Fiction TikTok - Novel to Multimedia Content Generation System

A comprehensive system that transforms novels into engaging multimedia content for social media marketing.

## Features

### Core Functionality
- **Novel Input & Processing**: Manual input and automated web scraping
- **Multi-language Support**: Chinese, Japanese, and English content
- **AI-Generated Illustrations**: Contextually relevant illustrations synced with novel content
- **Multi-language Text-to-Speech**: Multiple voices, adjustable parameters
- **Video Generation**: Automated composition of illustrations and audio
- **Social Media Integration**: Automated publishing to various platforms

### Technical Capabilities
- Real-time illustration generation matching story context and mood
- High-quality voice synthesis with character differentiation
- Automated video editing and composition
- Content management system for organizing materials
- Support for multiple novel sources and formats

## Architecture

```
fiction-tiktok/
├── backend/                 # FastAPI backend services
│   ├── api/                # Main API application
│   ├── services/           # Microservices
│   │   ├── novel_scraper/  # Web scraping service
│   │   ├── illustration/   # AI illustration generation
│   │   ├── tts/           # Text-to-speech service
│   │   ├── video/         # Video composition
│   │   └── social_media/  # Social media publishing
│   ├── models/            # Database models
│   ├── utils/             # Shared utilities
│   └── config/            # Configuration
├── frontend/              # React admin interface
├── docker/                # Docker configurations
├── scripts/               # Utility scripts
├── tests/                 # Test suites
└── docs/                  # Documentation
```

## Tech Stack

- **Backend**: Python (FastAPI), PostgreSQL, Redis
- **AI Services**: Stable Diffusion, OpenAI TTS/GPT, ElevenLabs
- **Video Processing**: FFmpeg
- **Frontend**: React/Next.js
- **Deployment**: Docker containers
- **Social Media**: TikTok, YouTube, Instagram APIs

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/changshize/fiction-tiktok.git
cd fiction-tiktok

# 2. Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Configure your API keys in .env file
# Edit .env with your OpenAI, ElevenLabs, and other API keys

# 4. Start the system
make start
# or: docker-compose up -d

# 5. Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

## Key Features Implemented

✅ **Novel Management**
- Manual novel input and chapter management
- Multi-language web scraping (Chinese, Japanese, English)
- Support for various novel sources (WuxiaWorld, WebNovel, etc.)

✅ **AI Content Generation**
- **Illustrations**: DALL-E 3 and Stable Diffusion integration
- **Audio**: OpenAI TTS and ElevenLabs voice synthesis
- **Video**: Automated composition with FFmpeg

✅ **Multi-language Support**
- Chinese, Japanese, and English text processing
- Language-specific voice selection
- Cultural context awareness

✅ **Social Media Ready**
- TikTok-optimized vertical videos (1080x1920)
- YouTube horizontal format support
- Automated content formatting

✅ **Production Ready**
- Docker containerization
- PostgreSQL database with Redis caching
- Background task processing
- Comprehensive API documentation

## System Architecture

The system uses a microservices architecture with:

- **FastAPI Backend**: RESTful API with async support
- **React Frontend**: Modern admin interface
- **PostgreSQL**: Primary database for structured data
- **Redis**: Caching and task queue management
- **AI Services**: OpenAI, Stable Diffusion, ElevenLabs integration
- **FFmpeg**: Video composition and processing

## API Usage Examples

### Generate Content
```bash
# Generate illustration
curl -X POST "http://localhost:8000/api/content/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"novel_id": 1, "content_type": "illustration", "generation_params": {"style": "anime"}}'

# Generate audio narration
curl -X POST "http://localhost:8000/api/content/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"novel_id": 1, "content_type": "audio", "generation_params": {"voice": "alloy"}}'

# Generate complete video
curl -X POST "http://localhost:8000/api/content/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"novel_id": 1, "content_type": "video", "generation_params": {"resolution": "1080x1920"}}'
```

### Batch Processing
```bash
# Generate multiple content types for multiple chapters
curl -X POST "http://localhost:8000/api/content/batch-generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"novel_id": 1, "content_types": ["illustration", "audio", "video"], "chapter_ids": [1,2,3]}'
```

## Development

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- API keys for AI services

### Local Development
```bash
# Start development environment
make dev

# View logs
make logs

# Run tests
make test

# Format code
make format
```

### Available Commands
```bash
make help          # Show all available commands
make setup         # Initial setup
make start         # Start all services
make stop          # Stop all services
make logs          # View logs
make test          # Run tests
make backup        # Backup database and files
make health        # Check service health
```

## Configuration

### Required API Keys
Add these to your `.env` file:

```env
# AI Services (Required)
OPENAI_API_KEY=sk-your-openai-key

# Optional but recommended
ELEVENLABS_API_KEY=your-elevenlabs-key
STABLE_DIFFUSION_API_KEY=your-sd-key

# Social Media (Optional)
TIKTOK_CLIENT_KEY=your-tiktok-key
YOUTUBE_API_KEY=your-youtube-key
INSTAGRAM_ACCESS_TOKEN=your-instagram-token
```

### Supported Content Types

**Illustrations**
- Styles: anime, realistic, fantasy, cyberpunk, watercolor
- Sizes: 1024x1024, 1920x1080, 1080x1920
- AI Models: DALL-E 3, Stable Diffusion

**Audio**
- Languages: English, Chinese, Japanese
- Voices: Multiple OpenAI and ElevenLabs voices
- Formats: MP3, adjustable speed and pitch

**Video**
- Resolutions: 1080x1920 (TikTok), 1920x1080 (YouTube)
- Formats: MP4 with H.264 encoding
- Features: Text overlays, transitions, effects

## Deployment

### Production Deployment
```bash
# Build for production
make prod-build

# Start production services
make prod-start

# Set up SSL (with domain)
make ssl-setup DOMAIN=your-domain.com
```

### Cloud Deployment
- **AWS**: EC2, RDS, ElastiCache, S3 integration
- **GCP**: Cloud Run, Cloud SQL, Cloud Storage
- **Azure**: Container Instances, PostgreSQL, Blob Storage

See `docs/DEPLOYMENT.md` for detailed deployment instructions.

## Documentation

- **API Documentation**: http://localhost:8000/docs
- **Getting Started**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **API Reference**: [docs/API.md](docs/API.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive guides in `/docs`
- **API Reference**: Interactive docs at `/docs` endpoint

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for GPT-4, DALL-E, and TTS APIs
- ElevenLabs for advanced voice synthesis
- Stability AI for Stable Diffusion
- FastAPI and React communities
