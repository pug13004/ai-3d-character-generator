#!/usr/bin/env python3
"""
Hugging Face Integration Module
Handles all Hugging Face API interactions for AI model inference
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any, Union
from PIL import Image
import io
import base64
import time

try:
    from config import get_settings
    settings = get_settings()
except ImportError:
    # Fallback configuration
    class FallbackSettings:
        hf_token = "YOUR_HUGGINGFACE_TOKEN_HERE"
        hf_api_url = "https://api-inference.huggingface.co"
    settings = FallbackSettings()

logger = logging.getLogger(__name__)

class HuggingFaceClient:
    """Client for interacting with Hugging Face Inference API"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or settings.hf_token
        self.base_url = settings.hf_api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Available models for different tasks
        self.models = {
            'text_to_image': [
                'runwayml/stable-diffusion-v1-5',
                'stabilityai/stable-diffusion-xl-base-1.0',
                'stabilityai/stable-diffusion-2-1'
            ],
            'image_to_text': [
                'Salesforce/blip-image-captioning-large',
                'nlpconnect/vit-gpt2-image-captioning'
            ],
            'depth_estimation': [
                'Intel/dpt-large',
                'LiheYoung/depth-anything-large-hf'
            ],
            'image_enhancement': [
                'microsoft/DiT-XL-2-256',
                'stabilityai/sd-x4-upscaler'
            ],
            'text_generation': [
                'microsoft/DialoGPT-medium',
                'facebook/blenderbot-400M-distill'
            ]
        }
    
    def check_connection(self) -> bool:
        """Check if the API connection is working"""
        if self.api_token == "YOUR_HUGGINGFACE_TOKEN_HERE":
            logger.error("Hugging Face token not configured")
            return False
            
        try:
            response = requests.get(
                "https://huggingface.co/api/whoami",
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HuggingFace connection check failed: {e}")
            return False
    
    def query_model(self, model_id: str, inputs: Union[str, bytes, Dict], 
                   parameters: Dict = None, wait_for_model: bool = True) -> Optional[Any]:
        """Generic method to query any Hugging Face model"""
        try:
            url = f"{self.base_url}/models/{model_id}"
            
            # Prepare payload
            payload = {"inputs": inputs}
            if parameters:
                payload["parameters"] = parameters
            if wait_for_model:
                payload["options"] = {"wait_for_model": True}
            
            # Handle different input types
            if isinstance(inputs, bytes):
                # For image inputs
                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/octet-stream"
                }
                response = requests.post(url, headers=headers, data=inputs, timeout=60)
            else:
                # For text/JSON inputs
                response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                # Handle different response types
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    return response.json()
                elif 'image' in content_type:
                    return response.content
                else:
                    return response.content
            else:
                logger.error(f"Model query failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error querying model {model_id}: {e}")
            return None
    
    def generate_image_from_text(self, prompt: str, model: str = None, 
                               parameters: Dict = None) -> Optional[bytes]:
        """Generate image from text prompt"""
        model = model or self.models['text_to_image'][0]
        
        default_params = {
            "num_inference_steps": 50,
            "guidance_scale": 7.5,
            "width": 512,
            "height": 512
        }
        if parameters:
            default_params.update(parameters)
        
        result = self.query_model(model, prompt, default_params)
        return result if isinstance(result, bytes) else None
    
    def describe_image(self, image_path: str, model: str = None) -> Optional[str]:
        """Generate text description of an image"""
        model = model or self.models['image_to_text'][0]
        
        try:
            # Load and prepare image
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            result = self.query_model(model, image_bytes)
            
            if result and isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '')
            return None
            
        except Exception as e:
            logger.error(f"Error describing image: {e}")
            return None
    
    def estimate_depth(self, image_path: str, model: str = None) -> Optional[bytes]:
        """Estimate depth map from image"""
        model = model or self.models['depth_estimation'][0]
        
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            result = self.query_model(model, image_bytes)
            return result if isinstance(result, bytes) else None
            
        except Exception as e:
            logger.error(f"Error estimating depth: {e}")
            return None
    
    def enhance_image(self, image_path: str, model: str = None, 
                     scale_factor: int = 4) -> Optional[bytes]:
        """Enhance/upscale image quality"""
        model = model or self.models['image_enhancement'][0]
        
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            parameters = {"scale_factor": scale_factor}
            result = self.query_model(model, image_bytes, parameters)
            return result if isinstance(result, bytes) else None
            
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return None

class CharacterPromptGenerator:
    """Generates optimized prompts for character generation"""
    
    def __init__(self, hf_client: HuggingFaceClient):
        self.hf_client = hf_client
        
        # Style templates
        self.style_templates = {
            'realistic': "photorealistic, highly detailed, professional photography, 8k resolution",
            'fantasy': "fantasy art, magical, ethereal, detailed fantasy character design",
            'anime': "anime style, manga art, cel shading, vibrant colors",
            'cartoon': "cartoon style, stylized, colorful, animated character design",
            'cyberpunk': "cyberpunk style, futuristic, neon lights, high-tech",
            'medieval': "medieval fantasy, armor, weapons, historical accuracy"
        }
        
        # Quality modifiers
        self.quality_modifiers = {
            'low': "simple, basic",
            'medium': "detailed, good quality",
            'high': "highly detailed, masterpiece, best quality, ultra-detailed",
            'ultra': "ultra-detailed, masterpiece, best quality, 8k, photorealistic"
        }
    
    def generate_character_prompt(self, base_prompt: str, style: str = 'realistic', 
                                quality: str = 'high', face_description: str = None) -> str:
        """Generate optimized prompt for character generation"""
        prompt_parts = [base_prompt]
        
        # Add face description if provided
        if face_description:
            prompt_parts.append(face_description)
        
        # Add style
        if style in self.style_templates:
            prompt_parts.append(self.style_templates[style])
        
        # Add quality modifiers
        if quality in self.quality_modifiers:
            prompt_parts.append(self.quality_modifiers[quality])
        
        final_prompt = ", ".join(prompt_parts)
        return final_prompt
    
    def generate_negative_prompt(self) -> str:
        """Generate negative prompt to avoid unwanted features"""
        negative_elements = [
            "low quality", "worst quality", "blurry", "out of focus",
            "distorted", "deformed", "ugly", "bad anatomy", "wrong anatomy",
            "extra limbs", "missing limbs", "floating limbs", "disconnected limbs",
            "bad hands", "bad fingers", "extra fingers", "missing fingers",
            "bad face", "bad eyes", "cross-eyed", "bad mouth", "bad teeth",
            "watermark", "signature", "text", "logo", "copyright"
        ]
        return ", ".join(negative_elements)
    
    def enhance_prompt_with_ai(self, base_prompt: str) -> str:
        """Use AI to enhance and expand the prompt"""
        try:
            enhancement_prompt = f"""
            Enhance this character description for AI image generation. 
            Make it more detailed and specific while keeping the core concept:
            
            Original: {base_prompt}
            
            Enhanced description:
            """
            
            # Use text generation model to enhance prompt
            model = self.hf_client.models['text_generation'][0]
            result = self.hf_client.query_model(
                model, 
                enhancement_prompt,
                {"max_length": 200, "temperature": 0.7}
            )
            
            if result and isinstance(result, list) and len(result) > 0:
                enhanced = result[0].get('generated_text', base_prompt)
                # Extract only the enhanced part
                if 'Enhanced description:' in enhanced:
                    enhanced = enhanced.split('Enhanced description:')[-1].strip()
                return enhanced
            
            return base_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing prompt: {e}")
            return base_prompt

class HuggingFaceWorkflowIntegration:
    """Integrates Hugging Face models with the 3D character generation workflow"""
    
    def __init__(self):
        self.client = HuggingFaceClient()
        self.prompt_generator = CharacterPromptGenerator(self.client)
    
    def process_character_request(self, prompt: str, style: str, quality: str,
                                reference_image: str = None) -> Dict[str, Any]:
        """Process a complete character generation request"""
        results = {
            'original_prompt': prompt,
            'style': style,
            'quality': quality,
            'enhanced_prompt': None,
            'negative_prompt': None,
            'reference_description': None,
            'generated_images': [],
            'depth_maps': [],
            'errors': []
        }
        
        try:
            # Enhance the prompt
            enhanced_prompt = self.prompt_generator.enhance_prompt_with_ai(prompt)
            results['enhanced_prompt'] = enhanced_prompt
            
            # Generate negative prompt
            results['negative_prompt'] = self.prompt_generator.generate_negative_prompt()
            
            # Process reference image if provided
            if reference_image:
                description = self.client.describe_image(reference_image)
                if description:
                    results['reference_description'] = description
                    # Incorporate reference description into prompt
                    enhanced_prompt = f"{enhanced_prompt}, {description}"
            
            # Generate final character prompt
            final_prompt = self.prompt_generator.generate_character_prompt(
                enhanced_prompt, style, quality
            )
            results['final_prompt'] = final_prompt
            
            # Generate character images
            for i in range(2):  # Generate 2 variations
                image_data = self.client.generate_image_from_text(
                    final_prompt,
                    parameters={
                        "num_inference_steps": 50 if quality == 'high' else 30,
                        "guidance_scale": 7.5,
                        "width": 1024 if quality == 'high' else 512,
                        "height": 1024 if quality == 'high' else 512
                    }
                )
                
                if image_data:
                    results['generated_images'].append(image_data)
                else:
                    results['errors'].append(f"Failed to generate image variation {i+1}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing character request: {e}")
            results['errors'].append(str(e))
            return results

# Global instances
hf_client = HuggingFaceClient()
hf_workflow_integration = HuggingFaceWorkflowIntegration()

def get_hf_client() -> HuggingFaceClient:
    """Get the global Hugging Face client instance"""
    return hf_client

def get_hf_workflow_integration() -> HuggingFaceWorkflowIntegration:
    """Get the global Hugging Face workflow integration instance"""
    return hf_workflow_integration
