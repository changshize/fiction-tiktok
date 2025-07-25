# Getting Started with Fiction TikTok

## Quick Start Guide

### 1. Prerequisites

Before you begin, ensure you have:

- **Docker & Docker Compose** installed
- **Git** for cloning the repository
- **API Keys** for AI services (see below)
- **4GB+ RAM** available for development

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/changshize/fiction-tiktok.git
cd fiction-tiktok

# Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. Configure API Keys

Edit the `.env` file with your API keys:

```env
# Required for basic functionality
OPENAI_API_KEY=sk-your-openai-key-here

# Optional but recommended
ELEVENLABS_API_KEY=your-elevenlabs-key
STABLE_DIFFUSION_API_KEY=your-sd-key

# Social media (optional)
TIKTOK_CLIENT_KEY=your-tiktok-key
YOUTUBE_API_KEY=your-youtube-key
```

### 4. Start the System

```bash
docker-compose up -d
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Backend API**: http://localhost:8000

## First Steps Tutorial

### Step 1: Create an Account

1. Go to http://localhost:3000
2. Click "Sign Up" and create your account
3. Login with your credentials

### Step 2: Add Your First Novel

**Option A: Manual Input**
1. Navigate to "Novels" → "Add Novel"
2. Fill in the novel details
3. Add chapters manually or upload a text file

**Option B: Web Scraping**
1. Go to "Novels" → "Scrape Novel"
2. Enter a novel URL (e.g., from WuxiaWorld)
3. Select the language and start scraping

### Step 3: Generate Content

1. Select your novel from the novels list
2. Choose a chapter
3. Click "Generate Content"
4. Select content types:
   - **Illustration**: AI-generated artwork
   - **Audio**: Text-to-speech narration
   - **Video**: Combined illustration + audio

### Step 4: Customize Generation

**Illustration Settings:**
- Style: anime, realistic, fantasy, cyberpunk
- Mood: happy, mysterious, action, calm
- Size: 1024x1024, 1920x1080

**Audio Settings:**
- Voice: alloy, echo, fable, onyx, nova, shimmer
- Speed: 0.5x to 2.0x
- Language: English, Chinese, Japanese

**Video Settings:**
- Resolution: 1080x1920 (TikTok), 1920x1080 (YouTube)
- Style: matches illustration style
- Duration: based on audio length

### Step 5: Review and Publish

1. Preview generated content
2. Make adjustments if needed
3. Publish to social media platforms (if configured)

## API Usage Examples

### Generate Illustration

```bash
curl -X POST "http://localhost:8000/api/content/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": 1,
    "chapter_id": 1,
    "content_type": "illustration",
    "generation_params": {
      "style": "anime",
      "mood": "mysterious"
    }
  }'
```

### Generate Audio

```bash
curl -X POST "http://localhost:8000/api/content/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": 1,
    "chapter_id": 1,
    "content_type": "audio",
    "generation_params": {
      "voice": "alloy",
      "speed": 1.0
    }
  }'
```

### Batch Generate

```bash
curl -X POST "http://localhost:8000/api/content/batch-generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": 1,
    "content_types": ["illustration", "audio", "video"],
    "chapter_ids": [1, 2, 3]
  }'
```

## Supported Novel Sources

### Automatic Scraping Support

- **WuxiaWorld**: English translated novels
- **NovelUpdates**: Novel information and links
- **WebNovel**: Popular web novels
- **Qidian**: Chinese novels (basic support)

### Manual Input Support

- **Text files**: .txt, .md
- **EPUB files**: Coming soon
- **Copy-paste**: Direct text input

## AI Models and Services

### Illustration Generation

**Primary**: OpenAI DALL-E 3
- High quality, consistent style
- Good prompt understanding
- Multiple aspect ratios

**Secondary**: Stable Diffusion
- More style options
- Faster generation
- Cost-effective

### Text-to-Speech

**Primary**: OpenAI TTS
- Multiple languages
- Natural voices
- Good pronunciation

**Secondary**: ElevenLabs
- Emotional voices
- Character differentiation
- Premium quality

### Text Processing

**OpenAI GPT-4**: Content analysis and prompt generation
**Custom NLP**: Language detection and text processing

## Troubleshooting

### Common Issues

**1. Services won't start**
```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs backend
```

**2. API key errors**
- Verify keys in `.env` file
- Check key permissions and quotas
- Restart services after updating keys

**3. Generation fails**
- Check API key validity
- Verify internet connection
- Review error logs

**4. Slow generation**
- AI services can be slow during peak times
- Consider upgrading to paid tiers
- Use batch generation for efficiency

### Getting Help

1. **Documentation**: Check `/docs` folder
2. **API Docs**: http://localhost:8000/docs
3. **Logs**: `docker-compose logs -f service_name`
4. **GitHub Issues**: Report bugs and feature requests

## Next Steps

### Advanced Features

1. **Custom Prompts**: Create your own illustration prompts
2. **Voice Cloning**: Use ElevenLabs for character voices
3. **Social Media Automation**: Set up auto-posting
4. **Batch Processing**: Process entire novels automatically

### Scaling Up

1. **Production Deployment**: See `docs/DEPLOYMENT.md`
2. **Cloud Services**: AWS, GCP, Azure integration
3. **Custom AI Models**: Train your own models
4. **API Integration**: Build custom applications

### Community

- **GitHub**: Contribute to the project
- **Discord**: Join our community (coming soon)
- **Blog**: Follow development updates

## Tips for Best Results

### Novel Selection
- Choose novels with rich descriptions
- Ensure good chapter structure
- Verify language detection accuracy

### Content Generation
- Use specific, descriptive prompts
- Experiment with different styles
- Generate multiple versions for comparison

### Social Media
- Optimize for platform requirements
- Use trending hashtags
- Post consistently for best engagement

## Support

For questions and support:
- **Email**: support@fiction-tiktok.com
- **GitHub**: https://github.com/changshize/fiction-tiktok
- **Documentation**: Full docs in `/docs` folder

Happy content creation! 🚀
