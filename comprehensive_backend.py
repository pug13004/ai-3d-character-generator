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
import io

# Web framework
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import uvicorn

# AI and processing
import requests
import numpy as np
from PIL import Image

# Local modules with fallback handling
try:
    from config import get_config, get_settings
    from comfyui_integration import get_comfyui_client, get_workflow_manager
    from face_matching import get_face_matching_pipeline
    from model_3d_generation import get_character_3d_generator
    from huggingface_integration import get_hf_client, get_hf_workflow_integration
    from agentic_seek_integration import get_agentic_seek_client, get_character_assistant

    # Get global instances
    config_manager = get_config()
    settings = get_settings()
    comfyui_client = get_comfyui_client()
    workflow_manager = get_workflow_manager()
    face_pipeline = get_face_matching_pipeline()
    model_3d_generator = get_character_3d_generator()
    hf_client = get_hf_client()
    hf_workflow = get_hf_workflow_integration()
    agentic_client = get_agentic_seek_client()
    character_assistant = get_character_assistant()

    MODULES_AVAILABLE = True

except ImportError as e:
    logger.warning(f"Some modules not available: {e}")
    MODULES_AVAILABLE = False

    # Fallback configuration
    class FallbackSettings:
        app_name = "AI-Powered 3D Character Generator"
        host = "0.0.0.0"
        port = 8080
        debug = False
        comfyui_url = "http://127.0.0.1:8188"
        hf_token = "YOUR_HUGGINGFACE_TOKEN_HERE"
        agentic_seek_url = "http://127.0.0.1:8000"
        max_file_size = 10 * 1024 * 1024
        upload_dir = "uploads"
        output_dir = "outputs"
        temp_dir = "temp"

    settings = FallbackSettings()

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered 3D Character Generator",
    description="Generate 3D characters using ComfyUI, Hugging Face, and AgenticSeek",
    version="1.0.0"
)

# Input validation models
class CharacterRequest(BaseModel):
    prompt: str
    style: str = "realistic"
    quality: str = "high"
    format: str = "glb"

    @validator('prompt')
    def prompt_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v.strip()

    @validator('style')
    def style_must_be_valid(cls, v):
        valid_styles = ['realistic', 'fantasy', 'anime', 'cartoon', 'cyberpunk', 'medieval']
        if v not in valid_styles:
            raise ValueError(f'Style must be one of: {valid_styles}')
        return v

    @validator('quality')
    def quality_must_be_valid(cls, v):
        valid_qualities = ['low', 'medium', 'high', 'ultra']
        if v not in valid_qualities:
            raise ValueError(f'Quality must be one of: {valid_qualities}')
        return v

    @validator('format')
    def format_must_be_valid(cls, v):
        valid_formats = ['glb', 'fbx', 'obj', 'ply']
        if v not in valid_formats:
            raise ValueError(f'Format must be one of: {valid_formats}')
        return v

# CORS middleware with security improvements
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Enhanced Global state
class AppState:
    def __init__(self):
        self.services = {
            'comfyui': {
                'url': settings.comfyui_url if MODULES_AVAILABLE else 'http://127.0.0.1:8188',
                'connected': False,
                'last_check': None
            },
            'agentic_seek': {
                'url': settings.agentic_seek_url if MODULES_AVAILABLE else 'http://127.0.0.1:8000',
                'connected': False,
                'enabled': getattr(settings, 'agentic_seek_enabled', True),
                'last_check': None
            },
            'huggingface': {
                'url': settings.hf_api_url if MODULES_AVAILABLE else 'https://api-inference.huggingface.co',
                'token': settings.hf_token if MODULES_AVAILABLE else 'YOUR_HUGGINGFACE_TOKEN_HERE',
                'connected': False,
                'last_check': None
            }
        }

        self.tasks = {}
        self.models_loaded = False
        self.generation_queue = asyncio.Queue()
        self.active_generations = {}

app_state = AppState()

# Utility functions
async def save_uploaded_file(file: UploadFile, directory: str = None) -> str:
    """Save uploaded file and return the file path"""
    upload_dir = Path(directory or settings.upload_dir if MODULES_AVAILABLE else "uploads")
    upload_dir.mkdir(exist_ok=True)

    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / filename

    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return str(file_path)

def generate_task_id() -> str:
    """Generate unique task ID"""
    return str(uuid.uuid4())

def create_directories():
    """Create necessary directories"""
    if MODULES_AVAILABLE:
        config_manager.create_directories()
    else:
        # Fallback directory creation
        dirs = ['outputs', 'uploads', 'models', 'logs', 'temp']
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)

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
    """Get comprehensive service status"""
    current_time = datetime.now()

    if MODULES_AVAILABLE:
        # Check ComfyUI
        try:
            app_state.services['comfyui']['connected'] = comfyui_client.check_connection()
            app_state.services['comfyui']['last_check'] = current_time.isoformat()
        except Exception as e:
            logger.error(f"ComfyUI status check failed: {e}")
            app_state.services['comfyui']['connected'] = False

        # Check Hugging Face
        try:
            app_state.services['huggingface']['connected'] = hf_client.check_connection()
            app_state.services['huggingface']['last_check'] = current_time.isoformat()
        except Exception as e:
            logger.error(f"HuggingFace status check failed: {e}")
            app_state.services['huggingface']['connected'] = False

        # Check AgenticSeek (if enabled)
        if app_state.services['agentic_seek']['enabled']:
            try:
                app_state.services['agentic_seek']['connected'] = agentic_client.check_connection()
                app_state.services['agentic_seek']['last_check'] = current_time.isoformat()
            except Exception as e:
                logger.error(f"AgenticSeek status check failed: {e}")
                app_state.services['agentic_seek']['connected'] = False

        # Get workflow status
        available_workflows = workflow_manager.list_workflows()

        # Get configuration validation
        config_validation = config_manager.validate_configuration()

        return {
            "status": "running",
            "timestamp": current_time.isoformat(),
            "services": app_state.services,
            "models_loaded": app_state.models_loaded,
            "active_tasks": len(app_state.tasks),
            "active_generations": len(app_state.active_generations),
            "available_workflows": available_workflows,
            "configuration": config_validation,
            "queue_size": app_state.generation_queue.qsize(),
            "modules_available": True
        }
    else:
        # Fallback status check
        return {
            "status": "running",
            "timestamp": current_time.isoformat(),
            "services": app_state.services,
            "models_loaded": False,
            "active_tasks": len(app_state.tasks),
            "modules_available": False,
            "error": "Core modules not available - check dependencies"
        }

@app.post("/generate/character")
async def generate_character(
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
    style: str = Form("realistic"),
    quality: str = Form("high"),
    format: str = Form("glb"),
    reference_image: Optional[UploadFile] = File(None)
):
    """Generate 3D character from text prompt with optional reference image"""
    task_id = generate_task_id()

    # Validate inputs
    try:
        char_request = CharacterRequest(
            prompt=prompt,
            style=style,
            quality=quality,
            format=format
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save reference image if provided
    reference_image_path = None
    if reference_image:
        if not reference_image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Reference file must be an image")

        if reference_image.size > settings.max_file_size:
            raise HTTPException(status_code=400, detail="File too large")

        reference_image_path = await save_uploaded_file(reference_image)

    # Create task
    task_data = {
        "id": task_id,
        "status": "queued",
        "prompt": char_request.prompt,
        "style": char_request.style,
        "quality": char_request.quality,
        "format": char_request.format,
        "reference_image": reference_image_path,
        "created_at": datetime.now().isoformat(),
        "progress": 0,
        "steps": [],
        "current_step": None,
        "output_files": [],
        "errors": []
    }

    app_state.tasks[task_id] = task_data

    if MODULES_AVAILABLE:
        # Start generation in background
        background_tasks.add_task(process_character_generation, task_id)
        estimated_time = "5-10 minutes"
    else:
        # Fallback - mark as failed
        task_data["status"] = "failed"
        task_data["errors"].append("Core modules not available")
        estimated_time = "N/A"

    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Character generation started",
        "estimated_time": estimated_time,
        "modules_available": MODULES_AVAILABLE
    }

async def process_character_generation(task_id: str):
    """Process character generation in background"""
    task = app_state.tasks.get(task_id)
    if not task or not MODULES_AVAILABLE:
        return

    try:
        # Update task status
        task["status"] = "processing"
        task["current_step"] = "Initializing"
        task["progress"] = 5

        # Step 1: Process reference image if provided
        face_data = None
        if task.get("reference_image"):
            task["current_step"] = "Analyzing reference image"
            task["progress"] = 15

            face_data = face_pipeline.process_reference_image(task["reference_image"])
            if face_data:
                task["steps"].append("✓ Face analysis completed")
            else:
                task["errors"].append("Failed to analyze reference image")

        # Step 2: Generate enhanced prompt using HuggingFace
        task["current_step"] = "Enhancing prompt"
        task["progress"] = 25

        hf_results = hf_workflow.process_character_request(
            task["prompt"],
            task["style"],
            task["quality"],
            task.get("reference_image")
        )

        if hf_results["errors"]:
            task["errors"].extend(hf_results["errors"])

        task["steps"].append("✓ Prompt enhancement completed")

        # Step 3: Generate character images using ComfyUI
        task["current_step"] = "Generating character images"
        task["progress"] = 40

        # Create workflow based on whether we have reference image
        if face_data:
            workflow = workflow_manager.create_face_matching_workflow(
                hf_results.get("final_prompt", task["prompt"]),
                task["reference_image"]
            )
        else:
            workflow = workflow_manager.create_text_to_image_workflow(
                hf_results.get("final_prompt", task["prompt"]),
                task["style"],
                task["quality"]
            )

        # Execute ComfyUI workflow
        prompt_id, generated_images = comfyui_client.execute_workflow(
            workflow,
            callback=lambda step, data: update_task_progress(task_id, step, data)
        )

        if generated_images:
            task["steps"].append(f"✓ Generated {len(generated_images)} character images")
            task["progress"] = 70
        else:
            task["errors"].append("Failed to generate character images")
            task["status"] = "failed"
            return

        # Step 4: Convert to 3D model
        task["current_step"] = "Converting to 3D model"
        task["progress"] = 80

        # Save the best generated image
        best_image_data = None
        for node_id, images in generated_images.items():
            if images:
                best_image_data = images[0]
                break

        if best_image_data:
            # Save image temporarily
            temp_dir = Path(settings.temp_dir)
            temp_dir.mkdir(exist_ok=True)
            temp_image_path = temp_dir / f"{task_id}_character.png"
            with open(temp_image_path, 'wb') as f:
                f.write(best_image_data)

            # Generate 3D model
            output_dir = Path(settings.output_dir)
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"{task_id}_character"
            model_path = model_3d_generator.generate_from_image(
                str(temp_image_path),
                str(output_path),
                task["format"],
                task["quality"]
            )

            if model_path:
                task["output_files"].append(model_path)
                task["steps"].append("✓ 3D model generation completed")
                task["progress"] = 95

                # Enhance with face data if available
                if face_data:
                    enhanced_path = model_3d_generator.enhance_with_face_data(
                        model_path, face_data, str(output_path) + "_enhanced"
                    )
                    if enhanced_path:
                        task["output_files"].append(enhanced_path)
                        task["steps"].append("✓ Face enhancement applied")
            else:
                task["errors"].append("Failed to generate 3D model")

            # Clean up temporary file
            if temp_image_path.exists():
                temp_image_path.unlink()

        # Final status
        if task["output_files"] and not task["errors"]:
            task["status"] = "completed"
            task["current_step"] = "Completed"
            task["progress"] = 100
            task["steps"].append("🎉 Character generation completed successfully!")
        else:
            task["status"] = "failed"
            task["current_step"] = "Failed"

    except Exception as e:
        logger.error(f"Error processing character generation {task_id}: {e}")
        task["status"] = "failed"
        task["current_step"] = "Error"
        task["errors"].append(f"Processing error: {str(e)}")

def update_task_progress(task_id: str, step: str, data: Any):
    """Update task progress during ComfyUI execution"""
    task = app_state.tasks.get(task_id)
    if task:
        if step == "executing":
            task["current_step"] = f"Executing node: {data}"
        elif step == "progress":
            # Update progress based on ComfyUI progress
            if isinstance(data, dict) and "value" in data and "max" in data:
                comfyui_progress = (data["value"] / data["max"]) * 30  # 30% of total progress
                task["progress"] = min(40 + comfyui_progress, 70)

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get detailed task status"""
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
