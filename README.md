# 🎮 AI-Powered 3D Character Generator

A comprehensive standalone application that integrates ComfyUI, Hugging Face, and AgenticSeek to automatically generate 3D models, characters, and assets from text prompts, images, or 3D files. Perfect for game development, 3D modeling, and creative projects.

## 🌟 Features

### 🎯 Core Capabilities
- **Text-to-3D Generation**: Create 3D characters from text descriptions
- **Image-to-3D Conversion**: Transform 2D images into 3D models
- **Face Matching**: Generate characters with exact facial features from uploaded photos
- **Real-time AI Processing**: Live workflow execution with progress monitoring
- **Multi-format Export**: GLB, FBX, OBJ formats for Unity, Unreal, Blender

### 🤖 AI Integrations
- **ComfyUI**: Advanced AI image generation and processing workflows
- **Hugging Face**: State-of-the-art AI models and transformers
- **AgenticSeek**: Intelligent AI assistance and optimization
- **Stable Diffusion**: High-quality image generation
- **MediaPipe**: Advanced face detection and analysis

### 🎨 Professional Features
- **Real-time 3D Viewer**: Interactive model preview with controls
- **Material System**: Automatic texture and material generation
- **Animation Support**: Basic rigging and animation capabilities
- **Game Engine Ready**: Direct export to Unity and Unreal Engine
- **Batch Processing**: Generate multiple characters simultaneously

## 🚀 Quick Start

### Prerequisites
- Windows 10/11 (64-bit)
- NVIDIA GPU with 6GB+ VRAM (recommended)
- Python 3.11 or 3.12
- 20GB+ free disk space

### One-Click Installation
```bash
# Clone the repository
git clone https://github.com/pug13004/ai-3d-character-generator.git
cd ai-3d-character-generator

# Run the automated installer
./install.bat

# Start the application
./start.bat
```

### Manual Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Download AI models
python download_ai_models.py

# Configure services
python setup_config.py

# Start the application
python comprehensive_backend.py
```

## 📖 Usage

### Web Interface
1. Open your browser to `http://localhost:8080`
2. Choose generation method:
   - **Text Prompt**: Describe your character
   - **Image Upload**: Upload a reference image
   - **Face Matching**: Upload a photo for exact face replication
3. Configure settings (style, quality, format)
4. Click "Generate Character"
5. Monitor real-time progress
6. Download your 3D model

### API Usage
```python
import requests

# Generate character from text
response = requests.post('http://localhost:8080/generate/character', json={
    'prompt': 'a mystical wizard with glowing staff',
    'style': 'fantasy',
    'quality': 'high',
    'format': 'glb'
})

# Get generation status
status = requests.get(f'http://localhost:8080/status/{response.json()["task_id"]}')
```

## 🛠️ Configuration

### Hugging Face Setup
1. Create account at [huggingface.co](https://huggingface.co)
2. Generate API token
3. Add to environment variables or config file

### ComfyUI Configuration
ComfyUI is included and pre-configured. Custom workflows can be added to `/workflows/` directory.

### GPU Optimization
For NVIDIA GPUs, CUDA acceleration is automatically enabled. For optimal performance:
- Use RTX 3060 or better
- Ensure 8GB+ VRAM for high-quality generation
- Update to latest NVIDIA drivers

## 📁 Project Structure

```
ai-3d-character-generator/
├── comprehensive_backend.py    # Main application server
├── requirements.txt           # Python dependencies
├── install.bat               # Automated installer
├── start.bat                 # Application launcher
├── outputs/                  # Generated 3D models
├── uploads/                  # User uploaded images
└── models/                   # AI models (downloaded separately)
```

## 🎯 Supported Formats

### Input
- **Text**: Natural language descriptions
- **Images**: JPG, PNG, WebP (up to 10MB)
- **3D Models**: OBJ, FBX, GLB for enhancement

### Output
- **GLB**: Optimized for web and mobile
- **FBX**: Industry standard for game engines
- **OBJ**: Universal 3D format

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ComfyUI Team**: For the amazing workflow system
- **Hugging Face**: For democratizing AI
- **Stability AI**: For Stable Diffusion
- **Open Source Community**: For countless contributions

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/pug13004/ai-3d-character-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pug13004/ai-3d-character-generator/discussions)

## 🔄 Updates

- **v1.0.0**: Initial release with ComfyUI integration

---

**Made with ❤️ for the 3D and AI community**
