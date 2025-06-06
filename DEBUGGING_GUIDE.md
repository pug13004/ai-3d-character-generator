# 🔧 AI 3D Character Generator - Debugging Guide

This comprehensive debugging guide will help you troubleshoot and resolve issues with the AI 3D Character Generator.

## 📋 Quick Diagnostics

### 1. Run System Tests
```bash
python test_system.py
```

### 2. Check Service Status
```bash
curl http://localhost:8080/status
```

### 3. Validate Configuration
```bash
python -c "from config import get_config; print(get_config().validate_configuration())"
```

## 🚨 Common Issues and Solutions

### Issue 1: ComfyUI Connection Failed

**Symptoms:**
- ❌ ComfyUI: Disconnected in status
- Error: "ComfyUI connection check failed"

**Solutions:**
1. **Check ComfyUI Installation Path**
   ```bash
   # Update .env file with correct path
   COMFYUI_PATH=C:\Users\jonny\OneDrive\Desktop\ComfyUI_windows_portable_nvidia (1)
   ```

2. **Start ComfyUI Manually**
   ```bash
   cd "C:\Users\jonny\OneDrive\Desktop\ComfyUI_windows_portable_nvidia (1)"
   python main.py --listen 127.0.0.1 --port 8188
   ```

3. **Check Port Availability**
   ```bash
   netstat -an | findstr :8188
   ```

### Issue 2: Hugging Face API Errors

**Symptoms:**
- ❌ Hugging Face: Disconnected
- Error: "Invalid token" or "API quota exceeded"

**Solutions:**
1. **Update API Token**
   ```bash
   # Get token from https://huggingface.co/settings/tokens
   # Update .env file:
   HF_TOKEN=hf_your_actual_token_here
   ```

2. **Test Token Manually**
   ```bash
   curl -H "Authorization: Bearer hf_your_token" https://huggingface.co/api/whoami
   ```

### Issue 3: Missing Dependencies

**Symptoms:**
- ImportError messages
- "Core modules not available"

**Solutions:**
1. **Install All Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Individual Packages**
   ```bash
   pip install fastapi uvicorn mediapipe opencv-python trimesh open3d websocket-client
   ```

3. **Check Python Version**
   ```bash
   python --version  # Should be 3.11 or 3.12
   ```

### Issue 4: Face Detection Not Working

**Symptoms:**
- Face analysis returns "No faces detected"
- MediaPipe errors

**Solutions:**
1. **Check Image Quality**
   - Use clear, well-lit images
   - Ensure face is visible and not obscured
   - Minimum resolution: 256x256 pixels

2. **Verify MediaPipe Installation**
   ```bash
   pip install mediapipe==0.10.7
   python -c "import mediapipe; print('MediaPipe OK')"
   ```

### Issue 5: 3D Model Generation Fails

**Symptoms:**
- Error: "Failed to generate 3D model"
- Depth estimation failures

**Solutions:**
1. **Check GPU Memory**
   ```bash
   nvidia-smi
   ```

2. **Reduce Quality Settings**
   - Use "medium" instead of "high" quality
   - Reduce image resolution

3. **Verify Dependencies**
   ```bash
   pip install trimesh open3d
   ```

## 🔍 Detailed Debugging Steps

### Step 1: Environment Verification

1. **Check Python Version**
   ```bash
   python --version  # Should be 3.11 or 3.12
   ```

2. **Verify Virtual Environment**
   ```bash
   # Windows
   venv\Scripts\activate
   # Check if activated
   where python
   ```

3. **Test Dependencies**
   ```bash
   python test_system.py --output test_results.json
   ```

### Step 2: Configuration Debugging

1. **Check Configuration Files**
   ```bash
   # Verify files exist
   dir .env
   dir config.json
   
   # Check content
   type .env
   ```

2. **Test Configuration Loading**
   ```bash
   python -c "from config import get_settings; print(get_settings().comfyui_path)"
   ```

### Step 3: Service Debugging

1. **Test Each Service Individually**
   ```bash
   # Test ComfyUI
   curl http://127.0.0.1:8188/system_stats
   
   # Test Hugging Face
   python -c "from huggingface_integration import get_hf_client; print(get_hf_client().check_connection())"
   ```

2. **Check Logs**
   ```bash
   # Application logs
   type logs\app.log
   
   # ComfyUI logs
   type "C:\Users\jonny\OneDrive\Desktop\ComfyUI_windows_portable_nvidia (1)\comfyui.log"
   ```

### Step 4: Network and Firewall

1. **Check Port Accessibility**
   ```bash
   telnet localhost 8080
   telnet localhost 8188
   ```

2. **Firewall Settings**
   - Allow Python through Windows Firewall
   - Allow ports 8080 and 8188

## 📊 Performance Optimization

### GPU Optimization

1. **Check GPU Usage**
   ```bash
   nvidia-smi -l 1
   ```

2. **Optimize Memory Settings**
   ```python
   # In .env file
   GPU_MEMORY_FRACTION=0.8
   USE_GPU=true
   ```

### Processing Optimization

1. **Adjust Quality Settings**
   ```python
   # For faster processing
   DEFAULT_QUALITY=medium
   
   # For better quality (slower)
   DEFAULT_QUALITY=high
   ```

2. **Batch Processing**
   - Process multiple characters in sequence
   - Use lower resolution for testing

## 🛠️ Advanced Troubleshooting

### Enable Debug Mode

1. **Update Configuration**
   ```bash
   # In .env file
   DEBUG=true
   ```

2. **Run with Verbose Logging**
   ```bash
   python comprehensive_backend.py --log-level debug
   ```

### Memory Issues

1. **Monitor Memory Usage**
   ```bash
   # Windows Task Manager
   taskmgr
   
   # Or use Python
   python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
   ```

2. **Clear Cache**
   ```bash
   # Clear temporary files
   rmdir /s temp
   mkdir temp
   
   # Clear model cache
   python -c "import torch; torch.cuda.empty_cache()"
   ```

### Database/State Issues

1. **Reset Application State**
   ```bash
   # Stop application
   # Delete state files
   del app_state.json
   
   # Restart application
   python comprehensive_backend.py
   ```

## 📞 Getting Help

### Log Collection

1. **Collect System Information**
   ```bash
   python test_system.py --output system_report.json
   ```

2. **Generate Debug Report**
   ```bash
   python -c "
   import sys, platform, torch
   print(f'Python: {sys.version}')
   print(f'Platform: {platform.platform()}')
   print(f'PyTorch: {torch.__version__}')
   print(f'CUDA Available: {torch.cuda.is_available()}')
   "
   ```

### Support Channels

1. **GitHub Issues**: [Create an issue](https://github.com/pug13004/ai-3d-character-generator/issues)
2. **Documentation**: Check README.md for setup instructions
3. **Community**: Join discussions for community support

### Before Reporting Issues

Please include:
- System information (OS, Python version, GPU)
- Error messages and logs
- Steps to reproduce the issue
- Configuration files (remove sensitive tokens)
- Output from `python test_system.py`

## 🔄 Recovery Procedures

### Complete Reset

1. **Backup Important Data**
   ```bash
   xcopy outputs backup_outputs /E /I
   xcopy uploads backup_uploads /E /I
   ```

2. **Clean Installation**
   ```bash
   # Remove virtual environment
   rmdir /s venv
   
   # Reinstall
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   
   # Reconfigure
   python -c "from config import get_config; get_config().save_config()"
   ```

### Partial Reset

1. **Reset Configuration Only**
   ```bash
   del .env
   del config.json
   python -c "from config import get_config; get_config().save_config()"
   ```

2. **Reset Models Only**
   ```bash
   rmdir /s models
   # Re-download models as needed
   ```

---

**Remember**: Most issues can be resolved by ensuring all dependencies are properly installed and configured. When in doubt, run the system tests first!
