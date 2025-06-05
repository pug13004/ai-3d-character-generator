#!/usr/bin/env python3
"""
Configuration Management for AI 3D Character Generator
Handles all service configurations, paths, and API keys
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    app_name: str = "AI-Powered 3D Character Generator"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8080, env="PORT")
    
    # ComfyUI Configuration
    comfyui_url: str = Field(default="http://127.0.0.1:8188", env="COMFYUI_URL")
    comfyui_path: str = Field(
        default=r"C:\Users\jonny\OneDrive\Desktop\ComfyUI_windows_portable_nvidia (1)",
        env="COMFYUI_PATH"
    )
    
    # Hugging Face Configuration
    hf_token: str = Field(default="YOUR_HUGGINGFACE_TOKEN_HERE", env="HF_TOKEN")
    hf_api_url: str = Field(default="https://api-inference.huggingface.co", env="HF_API_URL")
    
    # AgenticSeek Configuration
    agentic_seek_url: str = Field(default="http://127.0.0.1:8000", env="AGENTIC_SEEK_URL")
    agentic_seek_enabled: bool = Field(default=True, env="AGENTIC_SEEK_ENABLED")
    
    # File Storage Configuration
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    output_dir: str = Field(default="outputs", env="OUTPUT_DIR")
    models_dir: str = Field(default="models", env="MODELS_DIR")
    workflows_dir: str = Field(default="workflows", env="WORKFLOWS_DIR")
    temp_dir: str = Field(default="temp", env="TEMP_DIR")
    logs_dir: str = Field(default="logs", env="LOGS_DIR")
    
    # Processing Configuration
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    supported_image_formats: list = ["jpg", "jpeg", "png", "webp", "bmp"]
    supported_3d_formats: list = ["glb", "fbx", "obj", "ply"]
    
    # AI Model Configuration
    default_style: str = Field(default="realistic", env="DEFAULT_STYLE")
    default_quality: str = Field(default="high", env="DEFAULT_QUALITY")
    default_format: str = Field(default="glb", env="DEFAULT_FORMAT")
    
    # GPU Configuration
    use_gpu: bool = Field(default=True, env="USE_GPU")
    gpu_memory_fraction: float = Field(default=0.8, env="GPU_MEMORY_FRACTION")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

class ConfigManager:
    """Configuration manager for the application"""
    
    def __init__(self):
        self.config_file = Path("config.json")
        self.settings = settings
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file if it exists"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    # Update settings with config file data
                    for key, value in config_data.items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, value)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            "comfyui_url": self.settings.comfyui_url,
            "comfyui_path": self.settings.comfyui_path,
            "hf_token": self.settings.hf_token,
            "agentic_seek_url": self.settings.agentic_seek_url,
            "default_style": self.settings.default_style,
            "default_quality": self.settings.default_quality,
            "default_format": self.settings.default_format,
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def update_comfyui_path(self, path: str) -> bool:
        """Update ComfyUI installation path"""
        if Path(path).exists():
            self.settings.comfyui_path = path
            self.save_config()
            return True
        return False
    
    def update_hf_token(self, token: str) -> bool:
        """Update Hugging Face API token"""
        if token and token.startswith('hf_'):
            self.settings.hf_token = token
            self.save_config()
            return True
        return False
    
    def get_directories(self) -> Dict[str, Path]:
        """Get all configured directories as Path objects"""
        return {
            'upload': Path(self.settings.upload_dir),
            'output': Path(self.settings.output_dir),
            'models': Path(self.settings.models_dir),
            'workflows': Path(self.settings.workflows_dir),
            'temp': Path(self.settings.temp_dir),
            'logs': Path(self.settings.logs_dir),
        }
    
    def create_directories(self):
        """Create all necessary directories"""
        directories = self.get_directories()
        for name, path in directories.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✓ Created directory: {path}")
            except Exception as e:
                print(f"✗ Failed to create directory {path}: {e}")
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate current configuration"""
        validation_results = {}
        
        # Check ComfyUI path
        comfyui_path = Path(self.settings.comfyui_path)
        validation_results['comfyui_path_exists'] = comfyui_path.exists()
        
        # Check Hugging Face token format
        validation_results['hf_token_valid'] = (
            self.settings.hf_token and 
            self.settings.hf_token.startswith('hf_') and 
            len(self.settings.hf_token) > 10
        )
        
        # Check directories
        directories = self.get_directories()
        for name, path in directories.items():
            validation_results[f'{name}_dir_exists'] = path.exists()
        
        return validation_results

# Global config manager instance
config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """Get the global configuration manager instance"""
    return config_manager

def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings
