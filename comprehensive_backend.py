#!/usr/bin/env python3
"""
AI-Powered 3D Character Generator - Comprehensive Backend
Integrates ComfyUI, Hugging Face, and AgenticSeek for complete 3D character generation
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

# Web framework
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# AI and processing
import requests
import numpy as np
from PIL import Image
import trimesh

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered 3D Character Generator",
    description="Generate 3D characters using ComfyUI, Hugging Face, and AgenticSeek",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class AppState:
    def __init__(self):
        self.services = {
            'comfyui': {
                'url': 'http://127.0.0.1:8188',
                'connected': False
            },
            'agentic_seek': {
                'url': 'http://127.0.0.1:8000',
                'connected': False
            },
            'huggingface': {
                'url': 'https://huggingface.co/api',
                'token': os.getenv('HF_TOKEN', 'YOUR_HUGGINGFACE_TOKEN_HERE'),
                'connected': False
            }
        }
        
        self.tasks = {}
        self.models_loaded = False

app_state = AppState()

# Utility functions
def create_directories():
    """Create necessary directories"""
    dirs = ['outputs', 'uploads', 'models', 'logs', 'temp']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)

def generate_task_id() -> str:
    """Generate unique task ID"""
    return str(uuid.uuid4())

# API Routes
@app.get("/")
async def root():
    """Serve main application page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI-Powered 3D Character Generator</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .feature { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 AI-Powered 3D Character Generator</h1>
            
            <div class="feature">
                <h3>🎯 Core Features</h3>
                <ul>
                    <li><strong>Text-to-3D Generation</strong>: Create characters from descriptions</li>
                    <li><strong>Image-to-3D Conversion</strong>: Transform 2D images to 3D models</li>
                    <li><strong>Face Matching</strong>: Generate characters with exact facial features</li>
                    <li><strong>Real-time Processing</strong>: Live workflow execution monitoring</li>
                    <li><strong>Multi-format Export</strong>: GLB, FBX, OBJ for Unity/Unreal/Blender</li>
                </ul>
            </div>
            
            <div class="feature">
                <h3>🔧 Service Status</h3>
                <div id="status-container">
                    <div class="status disconnected">🔴 ComfyUI: Checking connection...</div>
                    <div class="status disconnected">🔴 Hugging Face: Checking connection...</div>
                    <div class="status disconnected">🔴 AgenticSeek: Checking connection...</div>
                </div>
            </div>
            
            <div class="feature">
                <h3>🚀 Quick Actions</h3>
                <button class="button" onclick="checkServices()">🔄 Check Services</button>
                <button class="button" onclick="generateSample()">🎨 Generate Sample</button>
                <button class="button" onclick="viewDocs()">📚 View Documentation</button>
            </div>
            
            <div class="feature">
                <h3>📖 API Endpoints</h3>
                <ul>
                    <li><code>GET /status</code> - Check service status</li>
                    <li><code>POST /generate/character</code> - Generate 3D character</li>
                    <li><code>POST /upload/image</code> - Upload reference image</li>
                    <li><code>GET /tasks/{task_id}</code> - Check task status</li>
                </ul>
            </div>
        </div>
        
        <script>
            async function checkServices() {
                try {
                    const response = await fetch('/status');
                    const data = await response.json();
                    updateStatus(data);
                } catch (error) {
                    console.error('Error checking services:', error);
                }
            }
            
            function updateStatus(data) {
                const container = document.getElementById('status-container');
                container.innerHTML = '';
                
                for (const [service, info] of Object.entries(data.services)) {
                    const statusClass = info.connected ? 'connected' : 'disconnected';
                    const icon = info.connected ? '🟢' : '🔴';
                    const div = document.createElement('div');
                    div.className = `status ${statusClass}`;
                    div.textContent = `${icon} ${service}: ${info.connected ? 'Connected' : 'Disconnected'}`;
                    container.appendChild(div);
                }
            }
            
            async function generateSample() {
                alert('Sample generation feature coming soon!');
            }
            
            function viewDocs() {
                window.open('https://github.com/pug13004/ai-3d-character-generator', '_blank');
            }
            
            // Check services on page load
            checkServices();
            setInterval(checkServices, 30000); // Check every 30 seconds
        </script>
    </body>
    </html>
    """)

@app.get("/status")
async def get_status():
    """Get service status"""
    # Check ComfyUI
    try:
        response = requests.get(f"{app_state.services['comfyui']['url']}/system_stats", timeout=5)
        app_state.services['comfyui']['connected'] = response.status_code == 200
    except:
        app_state.services['comfyui']['connected'] = False
    
    # Check Hugging Face
    try:
        headers = {"Authorization": f"Bearer {app_state.services['huggingface']['token']}"}
        response = requests.get("https://huggingface.co/api/whoami", headers=headers, timeout=5)
        app_state.services['huggingface']['connected'] = response.status_code == 200
    except:
        app_state.services['huggingface']['connected'] = False
    
    # Check AgenticSeek
    try:
        response = requests.get(f"{app_state.services['agentic_seek']['url']}/health", timeout=5)
        app_state.services['agentic_seek']['connected'] = response.status_code == 200
    except:
        app_state.services['agentic_seek']['connected'] = False
    
    return {
        "status": "running",
        "services": app_state.services,
        "models_loaded": app_state.models_loaded,
        "active_tasks": len(app_state.tasks)
    }

@app.post("/generate/character")
async def generate_character(
    prompt: str = Form(...),
    style: str = Form("realistic"),
    quality: str = Form("high"),
    format: str = Form("glb")
):
    """Generate 3D character from text prompt"""
    task_id = generate_task_id()
    
    # Store task
    app_state.tasks[task_id] = {
        "id": task_id,
        "status": "queued",
        "prompt": prompt,
        "style": style,
        "quality": quality,
        "format": format,
        "created_at": datetime.now().isoformat(),
        "progress": 0
    }
    
    # TODO: Implement actual generation logic
    # This would integrate with ComfyUI workflows
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Character generation started"
    }

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status"""
    if task_id not in app_state.tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return app_state.tasks[task_id]

@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload reference image"""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {
        "filename": file.filename,
        "path": str(file_path),
        "size": len(content),
        "message": "Image uploaded successfully"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    logger.info("Starting AI-Powered 3D Character Generator")
    create_directories()
    logger.info("Application initialized successfully")

# Main execution
if __name__ == "__main__":
    print("🚀 Starting AI-Powered 3D Character Generator")
    print("🌐 Web interface: http://localhost:8080")
    print("📚 API docs: http://localhost:8080/docs")
    print("🔧 Status: http://localhost:8080/status")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
