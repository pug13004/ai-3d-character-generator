#!/usr/bin/env python3
"""
AgenticSeek Integration Module
Provides AI assistance and optimization for the 3D character generation process
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from config import get_settings
    settings = get_settings()
except ImportError:
    # Fallback configuration
    class FallbackSettings:
        agentic_seek_url = "http://127.0.0.1:8000"
        agentic_seek_enabled = True
    settings = FallbackSettings()

logger = logging.getLogger(__name__)

class AgenticSeekClient:
    """Client for AgenticSeek AI assistance service"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.agentic_seek_url
        self.enabled = settings.agentic_seek_enabled
        self.session = requests.Session()
        
        # Set up headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AI-3D-Character-Generator/1.0'
        })
    
    def check_connection(self) -> bool:
        """Check if AgenticSeek service is available"""
        if not self.enabled:
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"AgenticSeek connection check failed: {e}")
            return False
    
    def get_assistance(self, query: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Get AI assistance for a specific query"""
        if not self.enabled or not self.check_connection():
            return None
        
        try:
            payload = {
                "query": query,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
                "service": "ai-3d-character-generator"
            }
            
            response = self.session.post(
                f"{self.base_url}/assist",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"AgenticSeek assistance failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting AgenticSeek assistance: {e}")
            return None
    
    def optimize_prompt(self, prompt: str, style: str, quality: str) -> Optional[str]:
        """Optimize character generation prompt using AI"""
        query = f"Optimize this character generation prompt for {style} style and {quality} quality: {prompt}"
        
        context = {
            "task": "prompt_optimization",
            "original_prompt": prompt,
            "style": style,
            "quality": quality,
            "target": "3d_character_generation"
        }
        
        result = self.get_assistance(query, context)
        if result and "optimized_prompt" in result:
            return result["optimized_prompt"]
        
        return None
    
    def suggest_improvements(self, generation_data: Dict[str, Any]) -> List[str]:
        """Suggest improvements for character generation"""
        query = "Suggest improvements for this 3D character generation process"
        
        context = {
            "task": "improvement_suggestions",
            "generation_data": generation_data,
            "target": "3d_character_generation"
        }
        
        result = self.get_assistance(query, context)
        if result and "suggestions" in result:
            return result["suggestions"]
        
        return []
    
    def analyze_generation_quality(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze the quality of a generation task"""
        query = "Analyze the quality and success of this 3D character generation"
        
        context = {
            "task": "quality_analysis",
            "task_data": task_data,
            "target": "3d_character_generation"
        }
        
        result = self.get_assistance(query, context)
        return result
    
    def get_troubleshooting_help(self, error_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get troubleshooting help for errors"""
        query = f"Help troubleshoot this error in 3D character generation: {error_info.get('error', 'Unknown error')}"
        
        context = {
            "task": "troubleshooting",
            "error_info": error_info,
            "target": "3d_character_generation"
        }
        
        result = self.get_assistance(query, context)
        return result

class CharacterGenerationAssistant:
    """AI assistant specifically for character generation tasks"""
    
    def __init__(self):
        self.agentic_client = AgenticSeekClient()
        self.assistance_cache = {}
    
    def get_style_recommendations(self, prompt: str) -> List[str]:
        """Get style recommendations based on prompt"""
        cache_key = f"style_rec_{hash(prompt)}"
        if cache_key in self.assistance_cache:
            return self.assistance_cache[cache_key]
        
        query = f"Recommend the best art styles for this character: {prompt}"
        context = {
            "task": "style_recommendation",
            "prompt": prompt
        }
        
        result = self.agentic_client.get_assistance(query, context)
        recommendations = []
        
        if result and "recommendations" in result:
            recommendations = result["recommendations"]
        else:
            # Fallback recommendations
            recommendations = ["realistic", "fantasy", "anime", "cartoon"]
        
        self.assistance_cache[cache_key] = recommendations
        return recommendations
    
    def enhance_character_description(self, basic_prompt: str, style: str) -> str:
        """Enhance a basic character description"""
        query = f"Enhance this character description for {style} style 3D generation: {basic_prompt}"
        context = {
            "task": "description_enhancement",
            "basic_prompt": basic_prompt,
            "style": style
        }
        
        result = self.agentic_client.get_assistance(query, context)
        if result and "enhanced_description" in result:
            return result["enhanced_description"]
        
        # Fallback enhancement
        style_modifiers = {
            "realistic": "photorealistic, highly detailed, professional quality",
            "fantasy": "fantasy art, magical, ethereal, detailed character design",
            "anime": "anime style, manga art, cel shading, vibrant colors",
            "cartoon": "cartoon style, stylized, colorful, animated character",
            "cyberpunk": "cyberpunk style, futuristic, neon lights, high-tech",
            "medieval": "medieval fantasy, historical accuracy, detailed armor"
        }
        
        modifier = style_modifiers.get(style, "high quality, detailed")
        return f"{basic_prompt}, {modifier}"
    
    def suggest_workflow_optimizations(self, workflow_name: str, parameters: Dict) -> Dict[str, Any]:
        """Suggest optimizations for ComfyUI workflow parameters"""
        query = f"Optimize parameters for {workflow_name} workflow"
        context = {
            "task": "workflow_optimization",
            "workflow_name": workflow_name,
            "current_parameters": parameters
        }
        
        result = self.agentic_client.get_assistance(query, context)
        if result and "optimized_parameters" in result:
            return result["optimized_parameters"]
        
        return parameters
    
    def analyze_face_matching_quality(self, reference_data: Dict, generated_data: Dict) -> Dict[str, Any]:
        """Analyze the quality of face matching"""
        query = "Analyze how well the generated character matches the reference face"
        context = {
            "task": "face_matching_analysis",
            "reference_data": reference_data,
            "generated_data": generated_data
        }
        
        result = self.agentic_client.get_assistance(query, context)
        if result:
            return result
        
        # Fallback analysis
        return {
            "match_quality": "unknown",
            "suggestions": ["Ensure reference image has clear facial features", "Try adjusting IPAdapter weight"]
        }
    
    def get_3d_generation_tips(self, image_analysis: Dict) -> List[str]:
        """Get tips for 3D model generation based on image analysis"""
        query = "Provide tips for generating a good 3D model from this image analysis"
        context = {
            "task": "3d_generation_tips",
            "image_analysis": image_analysis
        }
        
        result = self.agentic_client.get_assistance(query, context)
        if result and "tips" in result:
            return result["tips"]
        
        # Fallback tips
        return [
            "Ensure the image has good lighting and contrast",
            "Clear facial features improve 3D reconstruction",
            "Higher resolution images produce better 3D models",
            "Avoid images with heavy shadows or occlusions"
        ]
    
    def provide_user_guidance(self, user_query: str, context: Dict = None) -> str:
        """Provide guidance to users about the 3D character generation process"""
        query = f"User question about 3D character generation: {user_query}"
        assistance_context = {
            "task": "user_guidance",
            "user_query": user_query,
            "context": context or {}
        }
        
        result = self.agentic_client.get_assistance(query, assistance_context)
        if result and "guidance" in result:
            return result["guidance"]
        
        # Fallback guidance
        return "I'm here to help with your 3D character generation. Please provide more specific details about what you need assistance with."

class QualityAssessment:
    """Assess and improve generation quality using AI"""
    
    def __init__(self):
        self.assistant = CharacterGenerationAssistant()
    
    def assess_task_quality(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive quality assessment of a generation task"""
        assessment = {
            "overall_score": 0.0,
            "component_scores": {},
            "issues": [],
            "recommendations": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Assess different components
        if task_data.get("status") == "completed":
            assessment["component_scores"]["completion"] = 1.0
        else:
            assessment["component_scores"]["completion"] = 0.0
            assessment["issues"].append("Task did not complete successfully")
        
        # Check for errors
        errors = task_data.get("errors", [])
        if errors:
            assessment["component_scores"]["error_rate"] = max(0.0, 1.0 - len(errors) * 0.2)
            assessment["issues"].extend(errors)
        else:
            assessment["component_scores"]["error_rate"] = 1.0
        
        # Assess processing time
        if "created_at" in task_data and task_data.get("status") == "completed":
            # This would calculate actual processing time
            assessment["component_scores"]["efficiency"] = 0.8  # Placeholder
        
        # Get AI assessment if available
        ai_assessment = self.assistant.agentic_client.analyze_generation_quality(task_data)
        if ai_assessment:
            assessment.update(ai_assessment)
        
        # Calculate overall score
        scores = list(assessment["component_scores"].values())
        if scores:
            assessment["overall_score"] = sum(scores) / len(scores)
        
        return assessment
    
    def suggest_improvements(self, assessment: Dict[str, Any]) -> List[str]:
        """Suggest improvements based on quality assessment"""
        suggestions = []
        
        if assessment["overall_score"] < 0.7:
            suggestions.append("Consider using higher quality settings")
            suggestions.append("Try different style parameters")
        
        if assessment["component_scores"].get("error_rate", 1.0) < 0.8:
            suggestions.append("Check system requirements and dependencies")
            suggestions.append("Verify ComfyUI and model configurations")
        
        # Get AI suggestions
        ai_suggestions = self.assistant.suggest_workflow_optimizations("general", {})
        if ai_suggestions:
            suggestions.extend(ai_suggestions.get("suggestions", []))
        
        return suggestions

# Global instances
agentic_seek_client = AgenticSeekClient()
character_assistant = CharacterGenerationAssistant()
quality_assessment = QualityAssessment()

def get_agentic_seek_client() -> AgenticSeekClient:
    """Get the global AgenticSeek client instance"""
    return agentic_seek_client

def get_character_assistant() -> CharacterGenerationAssistant:
    """Get the global character generation assistant instance"""
    return character_assistant

def get_quality_assessment() -> QualityAssessment:
    """Get the global quality assessment instance"""
    return quality_assessment
