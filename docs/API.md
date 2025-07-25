# Fiction TikTok API Documentation

## Overview

The Fiction TikTok API provides endpoints for managing novels, generating multimedia content, and publishing to social media platforms.

## Base URL

```
http://localhost:8000/api
```

## Authentication

The API uses JWT token authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Authentication

#### POST /auth/register
Register a new user.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string"
}
```

#### POST /auth/token
Login and get access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

### Novels

#### POST /novels
Create a new novel.

**Request Body:**
```json
{
  "title": "string",
  "author": "string",
  "description": "string",
  "language": "en|zh|ja",
  "source_url": "string",
  "genre": "string",
  "tags": ["string"]
}
```

#### GET /novels
List all novels.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100)
- `language`: Filter by language

#### GET /novels/{novel_id}
Get a specific novel.

#### POST /novels/{novel_id}/chapters
Add a chapter to a novel.

**Request Body:**
```json
{
  "chapter_number": 1,
  "title": "string",
  "content": "string"
}
```

#### POST /novels/{novel_id}/upload
Upload a novel file and extract chapters.

**Form Data:**
- `file`: Novel file (txt, epub, etc.)

#### POST /novels/scrape
Scrape a novel from a URL.

**Form Data:**
- `url`: Novel URL
- `language`: Language code

### Content Generation

#### POST /content/generate
Generate content from novel.

**Request Body:**
```json
{
  "novel_id": 1,
  "chapter_id": 1,
  "content_type": "illustration|audio|video|social_post",
  "prompt": "string",
  "generation_params": {
    "style": "anime",
    "voice": "alloy",
    "resolution": "1080x1920"
  }
}
```

#### GET /content
List generated content.

**Query Parameters:**
- `novel_id`: Filter by novel
- `content_type`: Filter by type
- `status`: Filter by status

#### POST /content/batch-generate
Generate multiple types of content.

**Request Body:**
```json
{
  "novel_id": 1,
  "content_types": ["illustration", "audio", "video"],
  "chapter_ids": [1, 2, 3]
}
```

### Projects

#### POST /projects
Create a new project.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "target_language": "en",
  "voice_settings": {},
  "video_settings": {},
  "illustration_style": "anime",
  "target_platforms": ["tiktok", "youtube"],
  "auto_publish": false
}
```

#### GET /projects
List user's projects.

#### GET /projects/{project_id}/stats
Get project statistics.

## Response Format

### Success Response
```json
{
  "id": 1,
  "title": "Example Novel",
  "status": "completed",
  "created_at": "2023-01-01T00:00:00Z"
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```

## Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Rate Limiting

API requests are rate limited to prevent abuse:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users

## Content Types

### Illustration
- **Type**: `illustration`
- **Parameters**: `style`, `size`, `mood`
- **Output**: PNG image file

### Audio
- **Type**: `audio`
- **Parameters**: `voice`, `speed`, `language`
- **Output**: MP3 audio file

### Video
- **Type**: `video`
- **Parameters**: `resolution`, `style`, `voice`
- **Output**: MP4 video file

## Generation Parameters

### Illustration Parameters
```json
{
  "style": "anime|realistic|fantasy|cyberpunk",
  "size": "1024x1024|1920x1080",
  "mood": "happy|sad|mysterious|action"
}
```

### Audio Parameters
```json
{
  "voice": "alloy|echo|fable|onyx|nova|shimmer",
  "speed": 0.5-2.0,
  "language": "en|zh|ja"
}
```

### Video Parameters
```json
{
  "resolution": "1080x1920|1920x1080",
  "style": "anime|realistic",
  "voice": "alloy|echo|fable"
}
```

## Webhooks

Configure webhooks to receive notifications when content generation is complete:

```json
{
  "event": "content.completed",
  "data": {
    "content_id": 1,
    "status": "completed",
    "file_path": "/path/to/file"
  }
}
```

## SDKs

Official SDKs are available for:
- Python
- JavaScript/TypeScript
- Go

## Support

For API support, please contact:
- Email: support@fiction-tiktok.com
- Documentation: https://docs.fiction-tiktok.com
- GitHub Issues: https://github.com/changshize/fiction-tiktok/issues
