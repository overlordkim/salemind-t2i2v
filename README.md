# Salemind T2I2V - Text to Image to Video Generation System

A complete pipeline for generating videos from text prompts using LibLib AI for image generation and Kling AI for video generation.

## Features

- 🎨 **Text-to-Image Generation**: Use LibLib AI to generate high-quality images from text prompts
- 🎬 **Image-to-Video Generation**: Convert generated images to videos using Kling AI  
- 🔄 **Batch Processing**: Generate multiple videos with automated cycling through prompts
- 📝 **Easy Prompt Management**: Python-based prompt configuration for easy editing
- 🛡️ **Secure Configuration**: Separate API keys from public settings
- 📁 **Organized Output**: Timestamped sessions with automatic file naming

## Project Structure

```
salemind-t2i2v/
├── config/
│   ├── api_config.json          # API keys (ignored by git)
│   ├── kling_config.json        # Kling AI model settings
│   ├── model_config.json        # LibLib AI model settings
│   └── prompts.py              # Prompt configurations
├── static/
│   └── test.png                # Test image
├── liblib.py                   # LibLib AI image generation
├── kling.py                    # Kling AI video generation
├── generate_videos.sh          # Simple video generation
├── generate_full_videos.sh     # Complete T2I2V pipeline
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install requests PyJWT
```

### 2. Configure API Keys

Create `config/api_config.json` with your API credentials:

```json
{
  "liblib_access_key": "your_liblib_access_key",
  "liblib_secret_key": "your_liblib_secret_key", 
  "kling_access_key": "your_kling_access_key",
  "kling_secret_key": "your_kling_secret_key"
}
```

### 3. Configure Prompts

Edit `config/prompts.py` to add your own prompts:

```python
prompts = [
    {
        "image_prompt": """
Your image generation prompt here
""",
        "video_prompt": """
Your video generation prompt here
""",
    },
    # Add more prompt pairs...
]
```

## Usage

### Generate Single Image
```bash
python liblib.py "your text prompt"
```

### Generate Single Video  
```bash
python kling.py /path/to/image.png "your video prompt"
```

### Generate Multiple Videos (Image-to-Video only)
```bash
./generate_videos.sh 5  # Generate 5 videos
```

### Complete Text-to-Image-to-Video Pipeline
```bash
./generate_full_videos.sh 3  # Generate 3 complete videos
```

## Configuration Files

### Model Settings

- **LibLib Settings** (`config/model_config.json`): Configure checkpoint, dimensions, steps, etc.
- **Kling Settings** (`config/kling_config.json`): Configure model version, mode, duration, etc.

### Prompt Management

The `config/prompts.py` file uses Python triple-quote strings for easy copying and pasting of long prompts. Each prompt object contains both `image_prompt` and `video_prompt` fields.

## Output

Generated files are saved to timestamped session folders:
- `static/session_YYYYMMDD_HHMMSS/`
- Images: `video_001_prompt_00.png`
- Videos: `video_001_prompt_00.mp4`
- Info files: `video_001_prompt_00_info.txt`

## API Providers

- **LibLib AI**: High-quality image generation
- **Kling AI**: Advanced image-to-video conversion

## Security

- API keys are stored in `config/api_config.json` which is ignored by git
- Only non-sensitive configuration files are tracked in version control

## License

MIT License