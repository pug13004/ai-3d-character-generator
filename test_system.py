#!/usr/bin/env python3
"""
System Testing Script
Comprehensive testing for the AI 3D Character Generator
"""

import sys
import asyncio
import logging
import requests
import json
from pathlib import Path
from typing import Dict, List, Any
import time
import tempfile
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemTester:
    """Comprehensive system testing"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.test_results = {}
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all system tests"""
        print("🧪 Starting Comprehensive System Tests")
        print("=" * 60)
        
        tests = [
            ("Configuration", self.test_configuration),
            ("Dependencies", self.test_dependencies),
            ("Service Connections", self.test_service_connections),
            ("API Endpoints", self.test_api_endpoints),
            ("File Operations", self.test_file_operations),
            ("Module Integration", self.test_module_integration),
            ("Face Detection", self.test_face_detection),
            ("3D Generation", self.test_3d_generation),
            ("Workflow Loading", self.test_workflow_loading)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            print("-" * 40)
            
            try:
                result = test_func()
                self.test_results[test_name] = result
                
                if result.get("success", False):
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
                    if "error" in result:
                        print(f"   Error: {result['error']}")
                        
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                self.test_results[test_name] = {"success": False, "error": str(e)}
        
        self.print_summary()
        return self.test_results
    
    def test_configuration(self) -> Dict[str, Any]:
        """Test configuration setup"""
        try:
            # Test if config module can be imported
            try:
                from config import get_config, get_settings
                config_available = True
                
                config_manager = get_config()
                settings = get_settings()
                
                # Check if config files exist
                config_file_exists = config_manager.config_file.exists()
                env_file_exists = Path('.env').exists()
                
                # Validate configuration
                validation_results = config_manager.validate_configuration()
                
                return {
                    "success": True,
                    "config_available": config_available,
                    "config_file_exists": config_file_exists,
                    "env_file_exists": env_file_exists,
                    "validation_results": validation_results,
                    "settings": {
                        "comfyui_url": settings.comfyui_url,
                        "hf_token_set": bool(settings.hf_token and settings.hf_token != 'YOUR_HUGGINGFACE_TOKEN_HERE')
                    }
                }
            except ImportError as e:
                return {
                    "success": False,
                    "config_available": False,
                    "error": f"Config module not available: {e}"
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_dependencies(self) -> Dict[str, Any]:
        """Test required dependencies"""
        required_modules = [
            ('fastapi', 'FastAPI web framework'),
            ('uvicorn', 'ASGI server'),
            ('requests', 'HTTP library'),
            ('numpy', 'Numerical computing'),
            ('PIL', 'Image processing'),
            ('pydantic', 'Data validation'),
            ('mediapipe', 'Face detection'),
            ('cv2', 'Computer vision'),
            ('trimesh', '3D mesh processing'),
            ('open3d', '3D data processing'),
            ('websocket', 'WebSocket client')
        ]
        
        available_modules = []
        missing_modules = []
        
        for module_name, description in required_modules:
            try:
                if module_name == 'PIL':
                    import PIL
                elif module_name == 'cv2':
                    import cv2
                elif module_name == 'websocket':
                    import websocket
                else:
                    __import__(module_name)
                available_modules.append((module_name, description))
            except ImportError:
                missing_modules.append((module_name, description))
        
        return {
            "success": len(missing_modules) == 0,
            "available_modules": available_modules,
            "missing_modules": missing_modules,
            "total_required": len(required_modules),
            "availability_rate": len(available_modules) / len(required_modules)
        }
    
    def test_service_connections(self) -> Dict[str, Any]:
        """Test connections to external services"""
        try:
            # Test main application
            response = requests.get(f"{self.base_url}/status", timeout=10)
            app_running = response.status_code == 200
            
            if app_running:
                status_data = response.json()
                services = status_data.get("services", {})
                
                return {
                    "success": app_running,
                    "app_running": app_running,
                    "services": services,
                    "modules_available": status_data.get("modules_available", False),
                    "comfyui_connected": services.get("comfyui", {}).get("connected", False),
                    "huggingface_connected": services.get("huggingface", {}).get("connected", False),
                    "agentic_seek_connected": services.get("agentic_seek", {}).get("connected", False)
                }
            else:
                return {
                    "success": False,
                    "app_running": False,
                    "error": f"Application not responding: {response.status_code}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints"""
        endpoints = [
            ("GET", "/", "Main page"),
            ("GET", "/status", "Status endpoint"),
            ("GET", "/docs", "API documentation")
        ]
        
        results = {}
        all_success = True
        
        for method, endpoint, description in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                
                success = response.status_code == 200
                results[endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "description": description
                }
                
                if not success:
                    all_success = False
                    
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "error": str(e),
                    "description": description
                }
                all_success = False
        
        return {
            "success": all_success,
            "endpoints": results
        }
    
    def test_file_operations(self) -> Dict[str, Any]:
        """Test file operations"""
        try:
            # Test directory creation
            test_dirs = ["uploads", "outputs", "temp", "logs"]
            dirs_created = []
            
            for dir_name in test_dirs:
                path = Path(dir_name)
                if path.exists() or path.mkdir(parents=True, exist_ok=True):
                    dirs_created.append(str(path))
            
            # Test file write/read
            test_file = Path("temp") / "test_file.txt"
            test_content = "Test content for system testing"
            
            try:
                test_file.parent.mkdir(exist_ok=True)
                test_file.write_text(test_content)
                read_content = test_file.read_text()
                file_ops_success = read_content == test_content
                test_file.unlink()  # Clean up
            except Exception as e:
                file_ops_success = False
            
            return {
                "success": len(dirs_created) == len(test_dirs) and file_ops_success,
                "directories_created": dirs_created,
                "file_operations": file_ops_success
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_module_integration(self) -> Dict[str, Any]:
        """Test integration between modules"""
        try:
            # Test if all main modules can be imported together
            modules_status = {}
            
            try:
                from config import get_settings
                modules_status['config'] = True
            except ImportError:
                modules_status['config'] = False
            
            try:
                from comfyui_integration import get_comfyui_client
                modules_status['comfyui_integration'] = True
            except ImportError:
                modules_status['comfyui_integration'] = False
            
            try:
                from face_matching import get_face_matching_pipeline
                modules_status['face_matching'] = True
            except ImportError:
                modules_status['face_matching'] = False
            
            try:
                from model_3d_generation import get_character_3d_generator
                modules_status['model_3d_generation'] = True
            except ImportError:
                modules_status['model_3d_generation'] = False
            
            try:
                from huggingface_integration import get_hf_client
                modules_status['huggingface_integration'] = True
            except ImportError:
                modules_status['huggingface_integration'] = False
            
            available_modules = sum(modules_status.values())
            total_modules = len(modules_status)
            
            return {
                "success": available_modules == total_modules,
                "modules_status": modules_status,
                "available_modules": available_modules,
                "total_modules": total_modules,
                "integration_rate": available_modules / total_modules
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_face_detection(self) -> Dict[str, Any]:
        """Test face detection capabilities"""
        try:
            from face_matching import get_face_matching_pipeline
            import numpy as np
            from PIL import Image
            
            # Create a simple test image
            test_image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            test_image_path = Path("temp/test_face_image.png")
            test_image_path.parent.mkdir(exist_ok=True)
            
            Image.fromarray(test_image).save(test_image_path)
            
            face_pipeline = get_face_matching_pipeline()
            
            # Test face detection (will likely fail on random image, but tests the pipeline)
            result = face_pipeline.process_reference_image(str(test_image_path))
            
            # Clean up
            test_image_path.unlink()
            
            return {
                "success": True,  # Success if no errors thrown
                "pipeline_loaded": True,
                "test_completed": True,
                "face_detected": result is not None,
                "pipeline_available": face_pipeline.analyzer.available
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_3d_generation(self) -> Dict[str, Any]:
        """Test 3D model generation capabilities"""
        try:
            from model_3d_generation import get_character_3d_generator
            
            generator = get_character_3d_generator()
            
            # Test if the generator is properly initialized
            return {
                "success": True,
                "generator_loaded": True,
                "generator_available": generator.available,
                "image_converter_available": hasattr(generator, 'image_converter'),
                "model_processor_available": hasattr(generator, 'model_processor')
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_workflow_loading(self) -> Dict[str, Any]:
        """Test ComfyUI workflow loading"""
        try:
            from comfyui_integration import get_workflow_manager
            
            workflow_manager = get_workflow_manager()
            workflows = workflow_manager.list_workflows()
            
            # Test loading a basic workflow
            basic_workflow = workflow_manager.get_workflow("basic_character_generation")
            
            return {
                "success": True,
                "workflows_found": workflows,
                "workflow_count": len(workflows),
                "basic_workflow_available": basic_workflow is not None,
                "workflow_manager_loaded": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for test_name, result in self.test_results.items():
                if not result.get("success", False):
                    print(f"  - {test_name}: {result.get('error', 'Unknown error')}")
        
        print("\n💡 Recommendations:")
        if failed_tests == 0:
            print("  🎉 All tests passed! Your system is ready for 3D character generation.")
        else:
            print("  🔧 Fix the failed tests before using the system in production.")
            print("  📖 Check the README.md for setup instructions.")
            print("  🆘 Run 'pip install -r requirements.txt' to install missing dependencies.")

def main():
    """Main testing function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test AI 3D Character Generator system")
    parser.add_argument('--url', default='http://localhost:8080', help='Base URL for testing')
    parser.add_argument('--output', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    tester = SystemTester(args.url)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")
    
    # Exit with error code if tests failed
    failed_count = sum(1 for result in results.values() if not result.get("success", False))
    sys.exit(failed_count)

if __name__ == "__main__":
    main()
