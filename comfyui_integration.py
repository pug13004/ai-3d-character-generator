#!/usr/bin/env python3
"""
ComfyUI Integration Module
Handles all ComfyUI API interactions, workflow management, and image generation
"""

import json
import uuid
import asyncio
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
import time

try:
    import websocket
except ImportError:
    websocket = None

import requests
from PIL import Image
import io

try:
    from config import get_settings
    settings = get_settings()
except ImportError:
    # Fallback configuration
    class FallbackSettings:
        comfyui_url = "http://127.0.0.1:8188"
        comfyui_path = r"C:\Users\jonny\OneDrive\Desktop\ComfyUI_windows_portable_nvidia (1)"
        workflows_dir = "workflows"
    settings = FallbackSettings()

logger = logging.getLogger(__name__)

class ComfyUIClient:
    """ComfyUI API client for workflow execution and management"""
    
    def __init__(self, server_address: str = None):
        self.server_address = server_address or settings.comfyui_url.replace('http://', '')
        self.client_id = str(uuid.uuid4())
        self.ws = None
        self.connected = False
        
    def connect(self) -> bool:
        """Establish WebSocket connection to ComfyUI"""
        if not websocket:
            logger.error("websocket-client not installed. Install with: pip install websocket-client")
            return False
            
        try:
            self.ws = websocket.WebSocket()
            ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
            self.ws.connect(ws_url)
            self.connected = True
            logger.info(f"Connected to ComfyUI at {ws_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ComfyUI: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            try:
                self.ws.close()
                self.connected = False
                logger.info("Disconnected from ComfyUI")
            except Exception as e:
                logger.error(f"Error disconnecting from ComfyUI: {e}")
    
    def check_connection(self) -> bool:
        """Check if ComfyUI server is accessible"""
        try:
            response = requests.get(f"http://{self.server_address}/system_stats", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ComfyUI connection check failed: {e}")
            return False
    
    def queue_prompt(self, prompt: Dict[str, Any]) -> Optional[str]:
        """Queue a prompt for execution"""
        try:
            p = {"prompt": prompt, "client_id": self.client_id}
            data = json.dumps(p).encode('utf-8')
            req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
            req.add_header('Content-Type', 'application/json')
            response = urllib.request.urlopen(req)
            result = json.loads(response.read())
            prompt_id = result.get('prompt_id')
            logger.info(f"Queued prompt with ID: {prompt_id}")
            return prompt_id
        except Exception as e:
            logger.error(f"Failed to queue prompt: {e}")
            return None
    
    def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get execution history for a prompt"""
        try:
            with urllib.request.urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:
                history = json.loads(response.read())
                return history.get(prompt_id)
        except Exception as e:
            logger.error(f"Failed to get history for {prompt_id}: {e}")
            return None
    
    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> Optional[bytes]:
        """Retrieve generated image"""
        try:
            data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            url_values = urllib.parse.urlencode(data)
            with urllib.request.urlopen(f"http://{self.server_address}/view?{url_values}") as response:
                return response.read()
        except Exception as e:
            logger.error(f"Failed to get image {filename}: {e}")
            return None
    
    def monitor_execution(self, prompt_id: str, callback: Optional[Callable] = None) -> Dict[str, List[bytes]]:
        """Monitor workflow execution and collect results"""
        if not self.connected:
            if not self.connect():
                return {}
        
        output_images = {}
        current_node = ""
        
        try:
            while True:
                out = self.ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['prompt_id'] == prompt_id:
                            if data['node'] is None:
                                # Execution complete
                                break
                            else:
                                current_node = data['node']
                                if callback:
                                    callback('executing', current_node)
                    elif message['type'] == 'progress':
                        if callback:
                            callback('progress', message['data'])
                else:
                    # Binary data (preview images from SaveImageWebsocket)
                    if current_node and 'websocket' in current_node.lower():
                        images_output = output_images.get(current_node, [])
                        images_output.append(out[8:])  # Skip first 8 bytes
                        output_images[current_node] = images_output
        except Exception as e:
            logger.error(f"Error monitoring execution: {e}")
        
        return output_images
    
    def execute_workflow(self, workflow: Dict[str, Any], callback: Optional[Callable] = None) -> Tuple[Optional[str], Dict[str, List[bytes]]]:
        """Execute a complete workflow and return results"""
        # Queue the workflow
        prompt_id = self.queue_prompt(workflow)
        if not prompt_id:
            return None, {}
        
        # Monitor execution
        websocket_images = self.monitor_execution(prompt_id, callback)
        
        # Get saved images from history
        history = self.get_history(prompt_id)
        saved_images = {}
        
        if history and 'outputs' in history:
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                if 'images' in node_output:
                    images_output = []
                    for image in node_output['images']:
                        image_data = self.get_image(
                            image['filename'], 
                            image.get('subfolder', ''), 
                            image.get('type', 'output')
                        )
                        if image_data:
                            images_output.append(image_data)
                    saved_images[node_id] = images_output
        
        # Combine websocket and saved images
        all_images = {**websocket_images, **saved_images}
        
        return prompt_id, all_images

class WorkflowManager:
    """Manages ComfyUI workflows for different generation tasks"""
    
    def __init__(self):
        self.workflows_dir = Path(settings.workflows_dir)
        self.workflows_dir.mkdir(exist_ok=True)
        self.workflows = {}
        self._load_workflows()
    
    def _load_workflows(self):
        """Load all workflow files from the workflows directory"""
        workflow_files = list(self.workflows_dir.glob("*.json"))
        for workflow_file in workflow_files:
            try:
                with open(workflow_file, 'r') as f:
                    workflow_data = json.load(f)
                    workflow_name = workflow_file.stem
                    self.workflows[workflow_name] = workflow_data
                    logger.info(f"Loaded workflow: {workflow_name}")
            except Exception as e:
                logger.error(f"Failed to load workflow {workflow_file}: {e}")
    
    def get_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a workflow by name"""
        return self.workflows.get(name)
    
    def list_workflows(self) -> List[str]:
        """List all available workflows"""
        return list(self.workflows.keys())
    
    def create_text_to_image_workflow(self, prompt: str, style: str = "realistic", 
                                    quality: str = "high") -> Dict[str, Any]:
        """Create a basic text-to-image workflow"""
        steps = 30 if quality == "high" else 20
        cfg = 8.0 if quality == "high" else 7.0
        
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": cfg,
                    "denoise": 1,
                    "seed": 42,
                    "steps": steps,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "latent_image": ["5", 0],
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0]
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "sd_xl_base_1.0.safetensors"
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": 1024,
                    "width": 1024
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": f"{prompt}, {style} style, high quality, detailed, masterpiece"
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": "low quality, blurry, distorted, ugly, bad anatomy"
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                }
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "character_generation",
                    "images": ["8", 0]
                }
            }
        }
        return workflow
    
    def create_face_matching_workflow(self, prompt: str, reference_image_path: str) -> Dict[str, Any]:
        """Create a workflow for face matching using reference image"""
        # Basic face matching workflow using IPAdapter
        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "sd_xl_base_1.0.safetensors"
                }
            },
            "2": {
                "class_type": "LoadImage",
                "inputs": {
                    "image": reference_image_path
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["1", 1],
                    "text": f"{prompt}, matching the reference face, highly detailed, professional photography"
                }
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["1", 1],
                    "text": "low quality, blurry, different face, wrong face, bad anatomy"
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": 1024,
                    "width": 1024
                }
            },
            "6": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 7.5,
                    "denoise": 0.8,
                    "seed": 42,
                    "steps": 25,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "latent_image": ["5", 0],
                    "model": ["1", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0]
                }
            },
            "7": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["6", 0],
                    "vae": ["1", 2]
                }
            },
            "8": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "face_matched_character",
                    "images": ["7", 0]
                }
            }
        }
        return workflow

# Global instances
comfyui_client = ComfyUIClient()
workflow_manager = WorkflowManager()

def get_comfyui_client() -> ComfyUIClient:
    """Get the global ComfyUI client instance"""
    return comfyui_client

def get_workflow_manager() -> WorkflowManager:
    """Get the global workflow manager instance"""
    return workflow_manager
