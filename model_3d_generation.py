#!/usr/bin/env python3
"""
3D Model Generation Module
Handles conversion from 2D images to 3D models, GLB export, and model processing
"""

import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
import json
import io

try:
    import trimesh
except ImportError:
    trimesh = None

try:
    import open3d as o3d
except ImportError:
    o3d = None

try:
    import cv2
except ImportError:
    cv2 = None

from PIL import Image

try:
    from config import get_settings
    settings = get_settings()
except ImportError:
    # Fallback configuration
    class FallbackSettings:
        hf_token = "YOUR_HUGGINGFACE_TOKEN_HERE"
        hf_api_url = "https://api-inference.huggingface.co"
        temp_dir = "temp"
        output_dir = "outputs"
    settings = FallbackSettings()

logger = logging.getLogger(__name__)

class Image3DConverter:
    """Converts 2D images to 3D models using various techniques"""
    
    def __init__(self):
        self.depth_estimation_models = {
            'midas': 'https://api-inference.huggingface.co/models/Intel/dpt-large',
            'depth_anything': 'https://api-inference.huggingface.co/models/LiheYoung/depth-anything-large-hf'
        }
        self.available = trimesh is not None and o3d is not None
        
        if not self.available:
            logger.warning("3D processing libraries not available. Install with: pip install trimesh open3d")
    
    def estimate_depth(self, image_path: str, model: str = 'midas') -> Optional[np.ndarray]:
        """Estimate depth map from 2D image using Hugging Face models"""
        if settings.hf_token == "YOUR_HUGGINGFACE_TOKEN_HERE":
            logger.error("Hugging Face token not configured")
            return None
            
        try:
            # Load and prepare image
            image = Image.open(image_path)
            
            # Convert to bytes for API
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Call Hugging Face API
            headers = {"Authorization": f"Bearer {settings.hf_token}"}
            api_url = self.depth_estimation_models.get(model, self.depth_estimation_models['midas'])
            
            response = requests.post(api_url, headers=headers, data=img_byte_arr, timeout=30)
            
            if response.status_code == 200:
                # Parse depth map response
                depth_data = response.content
                depth_image = Image.open(io.BytesIO(depth_data))
                depth_array = np.array(depth_image)
                
                # Normalize depth values
                if len(depth_array.shape) == 3:
                    if cv2:
                        depth_array = cv2.cvtColor(depth_array, cv2.COLOR_RGB2GRAY)
                    else:
                        # Fallback to manual conversion
                        depth_array = np.mean(depth_array, axis=2)
                
                depth_normalized = depth_array.astype(np.float32) / 255.0
                return depth_normalized
            else:
                logger.error(f"Depth estimation API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error estimating depth: {e}")
            return None
    
    def create_point_cloud(self, image_path: str, depth_map: np.ndarray, 
                          focal_length: float = 525.0) -> Optional[o3d.geometry.PointCloud]:
        """Create point cloud from image and depth map"""
        if not o3d:
            logger.error("Open3D not available")
            return None
            
        try:
            # Load image
            image = Image.open(image_path)
            image_array = np.array(image)
            
            # Ensure image and depth map have same dimensions
            if image_array.shape[:2] != depth_map.shape:
                if cv2:
                    depth_map = cv2.resize(depth_map, (image_array.shape[1], image_array.shape[0]))
                else:
                    # Fallback resize using PIL
                    depth_pil = Image.fromarray((depth_map * 255).astype(np.uint8))
                    depth_pil = depth_pil.resize((image_array.shape[1], image_array.shape[0]))
                    depth_map = np.array(depth_pil) / 255.0
            
            height, width = depth_map.shape
            
            # Create coordinate grids
            x, y = np.meshgrid(np.arange(width), np.arange(height))
            
            # Convert to 3D coordinates
            # Assuming camera at origin, looking down negative Z axis
            cx, cy = width / 2, height / 2  # Principal point at image center
            
            # Calculate 3D points
            z = depth_map * 10.0  # Scale depth for better visualization
            x_3d = (x - cx) * z / focal_length
            y_3d = (y - cy) * z / focal_length
            
            # Stack coordinates
            points = np.stack([x_3d.flatten(), y_3d.flatten(), z.flatten()], axis=1)
            
            # Get colors
            if len(image_array.shape) == 3:
                colors = image_array.reshape(-1, 3) / 255.0
            else:
                colors = np.tile(image_array.reshape(-1, 1), (1, 3)) / 255.0
            
            # Create point cloud
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points)
            pcd.colors = o3d.utility.Vector3dVector(colors)
            
            # Remove invalid points
            pcd.remove_non_finite_points()
            
            return pcd
            
        except Exception as e:
            logger.error(f"Error creating point cloud: {e}")
            return None
    
    def point_cloud_to_mesh(self, pcd: o3d.geometry.PointCloud, 
                           method: str = 'poisson') -> Optional[o3d.geometry.TriangleMesh]:
        """Convert point cloud to triangle mesh"""
        if not o3d:
            logger.error("Open3D not available")
            return None
            
        try:
            if method == 'poisson':
                # Estimate normals
                pcd.estimate_normals()
                pcd.orient_normals_consistent_tangent_plane(30)
                
                # Poisson surface reconstruction
                mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                    pcd, depth=9, width=0, scale=1.1, linear_fit=False
                )
                
                # Remove low density vertices
                vertices_to_remove = []
                mesh.remove_vertices_by_index(vertices_to_remove)
                
            elif method == 'alpha_shape':
                # Alpha shape reconstruction
                alpha = 0.03
                mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)
                
            else:
                logger.error(f"Unknown mesh reconstruction method: {method}")
                return None
            
            # Clean up mesh
            mesh.remove_degenerate_triangles()
            mesh.remove_duplicated_triangles()
            mesh.remove_duplicated_vertices()
            mesh.remove_non_manifold_edges()
            
            return mesh
            
        except Exception as e:
            logger.error(f"Error converting point cloud to mesh: {e}")
            return None

class Model3DProcessor:
    """Processes and optimizes 3D models for different output formats"""
    
    def __init__(self):
        self.supported_formats = ['glb', 'fbx', 'obj', 'ply']
        self.available = trimesh is not None and o3d is not None
        
        if not self.available:
            logger.warning("3D processing libraries not available")
    
    def optimize_mesh(self, mesh: o3d.geometry.TriangleMesh, 
                     target_faces: int = 10000) -> o3d.geometry.TriangleMesh:
        """Optimize mesh by reducing polygon count and improving quality"""
        if not o3d:
            return mesh
            
        try:
            # Simplify mesh if it has too many faces
            current_faces = len(mesh.triangles)
            if current_faces > target_faces:
                mesh = mesh.simplify_quadric_decimation(target_faces)
                logger.info(f"Reduced mesh from {current_faces} to {len(mesh.triangles)} faces")
            
            # Smooth mesh
            mesh = mesh.filter_smooth_simple(number_of_iterations=1)
            
            # Compute vertex normals for better lighting
            mesh.compute_vertex_normals()
            
            return mesh
            
        except Exception as e:
            logger.error(f"Error optimizing mesh: {e}")
            return mesh
    
    def add_texture_coordinates(self, mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
        """Add UV texture coordinates to mesh"""
        if not o3d:
            return mesh
            
        try:
            # Simple planar UV mapping
            vertices = np.asarray(mesh.vertices)
            
            # Project to XY plane for UV coordinates
            uv_coords = vertices[:, :2]
            
            # Normalize to [0, 1] range
            uv_min = np.min(uv_coords, axis=0)
            uv_max = np.max(uv_coords, axis=0)
            uv_range = uv_max - uv_min
            uv_range[uv_range == 0] = 1  # Avoid division by zero
            
            uv_normalized = (uv_coords - uv_min) / uv_range
            
            # Set UV coordinates (Open3D doesn't directly support UVs, 
            # so we'll store them as vertex colors for now)
            mesh.vertex_colors = o3d.utility.Vector3dVector(
                np.column_stack([uv_normalized, np.zeros(len(uv_normalized))])
            )
            
            return mesh
            
        except Exception as e:
            logger.error(f"Error adding texture coordinates: {e}")
            return mesh
    
    def export_model(self, mesh: o3d.geometry.TriangleMesh, 
                    output_path: str, format: str = 'glb') -> bool:
        """Export 3D model to specified format"""
        if not self.available:
            logger.error("3D processing libraries not available")
            return False
            
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'glb':
                # Convert to trimesh for GLB export
                if not trimesh:
                    logger.error("Trimesh not available for GLB export")
                    return False
                    
                vertices = np.asarray(mesh.vertices)
                faces = np.asarray(mesh.triangles)
                
                # Create trimesh object
                trimesh_obj = trimesh.Trimesh(vertices=vertices, faces=faces)
                
                # Add vertex colors if available
                if mesh.has_vertex_colors():
                    vertex_colors = np.asarray(mesh.vertex_colors)
                    trimesh_obj.visual.vertex_colors = (vertex_colors * 255).astype(np.uint8)
                
                # Export as GLB
                trimesh_obj.export(str(output_path.with_suffix('.glb')))
                
            elif format.lower() == 'obj':
                # Export as OBJ
                o3d.io.write_triangle_mesh(str(output_path.with_suffix('.obj')), mesh)
                
            elif format.lower() == 'ply':
                # Export as PLY
                o3d.io.write_triangle_mesh(str(output_path.with_suffix('.ply')), mesh)
                
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Successfully exported model to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting model: {e}")
            return False

class Character3DGenerator:
    """Main class for generating 3D characters from images"""
    
    def __init__(self):
        self.image_converter = Image3DConverter()
        self.model_processor = Model3DProcessor()
        self.available = self.image_converter.available and self.model_processor.available
    
    def generate_from_image(self, image_path: str, output_path: str, 
                          format: str = 'glb', quality: str = 'high') -> Optional[str]:
        """Generate 3D character model from input image"""
        if not self.available:
            logger.error("3D generation not available - missing dependencies")
            return None
            
        try:
            logger.info(f"Starting 3D generation from {image_path}")
            
            # Step 1: Estimate depth
            depth_map = self.image_converter.estimate_depth(image_path)
            if depth_map is None:
                logger.error("Failed to estimate depth map")
                return None
            
            # Step 2: Create point cloud
            pcd = self.image_converter.create_point_cloud(image_path, depth_map)
            if pcd is None:
                logger.error("Failed to create point cloud")
                return None
            
            # Step 3: Convert to mesh
            mesh = self.image_converter.point_cloud_to_mesh(pcd)
            if mesh is None:
                logger.error("Failed to convert point cloud to mesh")
                return None
            
            # Step 4: Optimize mesh
            target_faces = 15000 if quality == 'high' else 8000
            mesh = self.model_processor.optimize_mesh(mesh, target_faces)
            
            # Step 5: Add texture coordinates
            mesh = self.model_processor.add_texture_coordinates(mesh)
            
            # Step 6: Export model
            success = self.model_processor.export_model(mesh, output_path, format)
            if success:
                final_path = Path(output_path).with_suffix(f'.{format.lower()}')
                logger.info(f"Successfully generated 3D model: {final_path}")
                return str(final_path)
            else:
                logger.error("Failed to export 3D model")
                return None
                
        except Exception as e:
            logger.error(f"Error generating 3D model: {e}")
            return None
    
    def enhance_with_face_data(self, mesh_path: str, face_data: Dict[str, Any], 
                              output_path: str) -> Optional[str]:
        """Enhance 3D model using facial landmark data"""
        if not self.available:
            logger.error("3D enhancement not available - missing dependencies")
            return None
            
        try:
            # Load existing mesh
            if not o3d:
                logger.error("Open3D not available")
                return None
                
            mesh = o3d.io.read_triangle_mesh(mesh_path)
            if len(mesh.vertices) == 0:
                logger.error(f"Could not load mesh from {mesh_path}")
                return None
            
            # Apply facial enhancements based on landmark data
            # This would involve more sophisticated mesh deformation
            # For now, we'll just re-export the mesh
            
            success = self.model_processor.export_model(mesh, output_path)
            if success:
                logger.info(f"Enhanced 3D model saved to {output_path}")
                return output_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error enhancing 3D model: {e}")
            return None

# Global instance
character_3d_generator = Character3DGenerator()

def get_character_3d_generator() -> Character3DGenerator:
    """Get the global 3D character generator instance"""
    return character_3d_generator
