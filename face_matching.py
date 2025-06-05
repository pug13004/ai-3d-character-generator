#!/usr/bin/env python3
"""
Face Matching Module
Handles face detection, analysis, and matching using MediaPipe and OpenCV
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import numpy as np
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import mediapipe as mp
except ImportError:
    mp = None

logger = logging.getLogger(__name__)

class FaceAnalyzer:
    """Face analysis using MediaPipe for feature extraction and matching"""
    
    def __init__(self):
        if not mp:
            logger.error("MediaPipe not installed. Install with: pip install mediapipe")
            self.available = False
            return
            
        if not cv2:
            logger.error("OpenCV not installed. Install with: pip install opencv-python")
            self.available = False
            return
            
        self.available = True
        
        # Initialize MediaPipe components
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize face detection and mesh
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect faces in an image and return bounding boxes and confidence scores"""
        if not self.available:
            return []
            
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_image)
        
        faces = []
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                confidence = detection.score[0]
                
                # Convert relative coordinates to absolute
                h, w, _ = image.shape
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                faces.append({
                    'bbox': (x, y, width, height),
                    'confidence': confidence,
                    'relative_bbox': (bbox.xmin, bbox.ymin, bbox.width, bbox.height)
                })
        
        return faces
    
    def extract_face_landmarks(self, image: np.ndarray) -> Optional[Dict[str, Any]]:
        """Extract detailed face landmarks using MediaPipe Face Mesh"""
        if not self.available:
            return None
            
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        
        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            
            # Extract key facial features
            landmarks_dict = {}
            h, w, _ = image.shape
            
            # Convert normalized landmarks to pixel coordinates
            landmarks_array = []
            for landmark in face_landmarks.landmark:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                z = landmark.z
                landmarks_array.append([x, y, z])
            
            landmarks_dict['all_landmarks'] = landmarks_array
            landmarks_dict['face_oval'] = self._get_face_oval_points(landmarks_array)
            landmarks_dict['left_eye'] = self._get_eye_points(landmarks_array, 'left')
            landmarks_dict['right_eye'] = self._get_eye_points(landmarks_array, 'right')
            landmarks_dict['nose'] = self._get_nose_points(landmarks_array)
            landmarks_dict['mouth'] = self._get_mouth_points(landmarks_array)
            landmarks_dict['eyebrows'] = self._get_eyebrow_points(landmarks_array)
            
            return landmarks_dict
        
        return None
    
    def _get_face_oval_points(self, landmarks: List[List[int]]) -> List[List[int]]:
        """Extract face oval contour points"""
        # MediaPipe face oval indices
        face_oval_indices = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                           397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                           172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
        
        return [landmarks[i] for i in face_oval_indices if i < len(landmarks)]
    
    def _get_eye_points(self, landmarks: List[List[int]], eye: str) -> List[List[int]]:
        """Extract eye contour points"""
        if eye == 'left':
            # Left eye indices
            eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        else:
            # Right eye indices  
            eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        return [landmarks[i] for i in eye_indices if i < len(landmarks)]
    
    def _get_nose_points(self, landmarks: List[List[int]]) -> List[List[int]]:
        """Extract nose contour points"""
        nose_indices = [1, 2, 5, 4, 6, 19, 20, 94, 125, 141, 235, 236, 237, 238, 239, 240, 241, 242]
        return [landmarks[i] for i in nose_indices if i < len(landmarks)]
    
    def _get_mouth_points(self, landmarks: List[List[int]]) -> List[List[int]]:
        """Extract mouth contour points"""
        mouth_indices = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
        return [landmarks[i] for i in mouth_indices if i < len(landmarks)]
    
    def _get_eyebrow_points(self, landmarks: List[List[int]]) -> Dict[str, List[List[int]]]:
        """Extract eyebrow points"""
        left_eyebrow_indices = [46, 53, 52, 51, 48, 115, 131, 134, 102, 48, 64]
        right_eyebrow_indices = [276, 283, 282, 281, 278, 344, 360, 363, 331, 278, 294]
        
        return {
            'left': [landmarks[i] for i in left_eyebrow_indices if i < len(landmarks)],
            'right': [landmarks[i] for i in right_eyebrow_indices if i < len(landmarks)]
        }
    
    def calculate_face_metrics(self, landmarks: Dict[str, Any]) -> Dict[str, float]:
        """Calculate facial metrics for comparison"""
        if not landmarks or 'all_landmarks' not in landmarks:
            return {}
        
        all_points = np.array(landmarks['all_landmarks'])
        
        # Calculate basic facial measurements
        metrics = {}
        
        # Face width and height
        face_points = np.array(landmarks['face_oval'])
        if len(face_points) > 0:
            face_width = np.max(face_points[:, 0]) - np.min(face_points[:, 0])
            face_height = np.max(face_points[:, 1]) - np.min(face_points[:, 1])
            metrics['face_width'] = float(face_width)
            metrics['face_height'] = float(face_height)
            metrics['face_ratio'] = float(face_width / face_height) if face_height > 0 else 0
        
        # Eye measurements
        if 'left_eye' in landmarks and 'right_eye' in landmarks:
            left_eye = np.array(landmarks['left_eye'])
            right_eye = np.array(landmarks['right_eye'])
            
            if len(left_eye) > 0 and len(right_eye) > 0:
                # Eye distance
                left_center = np.mean(left_eye, axis=0)
                right_center = np.mean(right_eye, axis=0)
                eye_distance = np.linalg.norm(left_center - right_center)
                metrics['eye_distance'] = float(eye_distance)
                
                # Eye sizes
                left_eye_width = np.max(left_eye[:, 0]) - np.min(left_eye[:, 0])
                left_eye_height = np.max(left_eye[:, 1]) - np.min(left_eye[:, 1])
                right_eye_width = np.max(right_eye[:, 0]) - np.min(right_eye[:, 0])
                right_eye_height = np.max(right_eye[:, 1]) - np.min(right_eye[:, 1])
                
                metrics['avg_eye_width'] = float((left_eye_width + right_eye_width) / 2)
                metrics['avg_eye_height'] = float((left_eye_height + right_eye_height) / 2)
        
        # Nose measurements
        if 'nose' in landmarks:
            nose_points = np.array(landmarks['nose'])
            if len(nose_points) > 0:
                nose_width = np.max(nose_points[:, 0]) - np.min(nose_points[:, 0])
                nose_height = np.max(nose_points[:, 1]) - np.min(nose_points[:, 1])
                metrics['nose_width'] = float(nose_width)
                metrics['nose_height'] = float(nose_height)
        
        # Mouth measurements
        if 'mouth' in landmarks:
            mouth_points = np.array(landmarks['mouth'])
            if len(mouth_points) > 0:
                mouth_width = np.max(mouth_points[:, 0]) - np.min(mouth_points[:, 0])
                mouth_height = np.max(mouth_points[:, 1]) - np.min(mouth_points[:, 1])
                metrics['mouth_width'] = float(mouth_width)
                metrics['mouth_height'] = float(mouth_height)
        
        return metrics
    
    def compare_faces(self, metrics1: Dict[str, float], metrics2: Dict[str, float]) -> float:
        """Compare two sets of facial metrics and return similarity score (0-1)"""
        if not metrics1 or not metrics2:
            return 0.0
        
        # Get common metrics
        common_keys = set(metrics1.keys()) & set(metrics2.keys())
        if not common_keys:
            return 0.0
        
        # Calculate normalized differences
        differences = []
        for key in common_keys:
            val1, val2 = metrics1[key], metrics2[key]
            if val1 > 0 and val2 > 0:
                # Normalized difference (0 = identical, 1 = completely different)
                diff = abs(val1 - val2) / max(val1, val2)
                differences.append(diff)
        
        if not differences:
            return 0.0
        
        # Calculate similarity score (1 - average difference)
        avg_difference = sum(differences) / len(differences)
        similarity = max(0.0, 1.0 - avg_difference)
        
        return similarity

class FaceMatchingPipeline:
    """Complete face matching pipeline for 3D character generation"""
    
    def __init__(self):
        self.analyzer = FaceAnalyzer()
    
    def process_reference_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Process reference image and extract facial features"""
        if not self.analyzer.available:
            logger.error("Face analyzer not available - missing dependencies")
            return None
            
        try:
            # Load image
            if not cv2:
                logger.error("OpenCV not available")
                return None
                
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return None
            
            # Detect faces
            faces = self.analyzer.detect_faces(image)
            if not faces:
                logger.warning(f"No faces detected in {image_path}")
                return None
            
            # Use the face with highest confidence
            best_face = max(faces, key=lambda x: x['confidence'])
            
            # Extract landmarks
            landmarks = self.analyzer.extract_face_landmarks(image)
            if not landmarks:
                logger.warning(f"Could not extract landmarks from {image_path}")
                return None
            
            # Calculate metrics
            metrics = self.analyzer.calculate_face_metrics(landmarks)
            
            return {
                'image_path': image_path,
                'face_detection': best_face,
                'landmarks': landmarks,
                'metrics': metrics,
                'image_shape': image.shape
            }
            
        except Exception as e:
            logger.error(f"Error processing reference image {image_path}: {e}")
            return None
    
    def generate_face_description(self, face_data: Dict[str, Any]) -> str:
        """Generate text description of facial features for ComfyUI prompts"""
        if not face_data or 'metrics' not in face_data:
            return ""
        
        metrics = face_data['metrics']
        description_parts = []
        
        # Face shape analysis
        if 'face_ratio' in metrics:
            ratio = metrics['face_ratio']
            if ratio < 0.75:
                description_parts.append("narrow face")
            elif ratio > 1.3:
                description_parts.append("wide face")
            else:
                description_parts.append("oval face")
        
        # Eye analysis
        if 'eye_distance' in metrics and 'avg_eye_width' in metrics:
            eye_ratio = metrics['eye_distance'] / metrics['avg_eye_width'] if metrics['avg_eye_width'] > 0 else 0
            if eye_ratio > 3.5:
                description_parts.append("wide-set eyes")
            elif eye_ratio < 2.5:
                description_parts.append("close-set eyes")
        
        # Nose analysis
        if 'nose_width' in metrics and 'nose_height' in metrics:
            nose_ratio = metrics['nose_width'] / metrics['nose_height'] if metrics['nose_height'] > 0 else 0
            if nose_ratio > 0.8:
                description_parts.append("wide nose")
            elif nose_ratio < 0.5:
                description_parts.append("narrow nose")
        
        # Mouth analysis
        if 'mouth_width' in metrics:
            description_parts.append("proportional mouth")
        
        return ", ".join(description_parts) if description_parts else "balanced facial features"

# Global instance
face_matching_pipeline = FaceMatchingPipeline()

def get_face_matching_pipeline() -> FaceMatchingPipeline:
    """Get the global face matching pipeline instance"""
    return face_matching_pipeline
