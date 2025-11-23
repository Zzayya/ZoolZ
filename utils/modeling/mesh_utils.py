#!/usr/bin/env python3
"""
Mesh Utilities - Common Functions for 3D Model Manipulation
Provides foundational mesh operations used across all modeling tools
"""

import trimesh
import numpy as np
from scipy.spatial import cKDTree
from typing import List, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class MeshAnalyzer:
    """Advanced mesh analysis and manipulation utilities"""

    def __init__(self, mesh: trimesh.Trimesh):
        """
        Initialize mesh analyzer

        Args:
            mesh: Trimesh object to analyze
        """
        self.mesh = mesh
        self.mesh.fix_normals()  # Ensure consistent normal direction

    def detect_walls(self, thickness_threshold: float = 2.0) -> Dict:
        """
        Detect thin walls in the mesh using advanced geometry analysis

        Args:
            thickness_threshold: Maximum thickness to consider as a "wall" (mm)

        Returns:
            Dict containing:
                - wall_faces: Indices of faces that are part of thin walls
                - wall_thickness: Estimated thickness for each wall face
                - wall_normals: Normal vectors for each wall face
        """
        logger.info(f"Detecting walls with thickness threshold {thickness_threshold}mm")

        # Get face centers and normals
        face_centers = self.mesh.triangles_center
        face_normals = self.mesh.face_normals

        # Build KD-tree for efficient nearest-neighbor search
        tree = cKDTree(face_centers)

        wall_faces = []
        wall_thicknesses = []

        for i, (center, normal) in enumerate(zip(face_centers, face_normals)):
            # Cast ray in opposite direction of normal to find parallel surface
            ray_origin = center - normal * 0.01  # Offset slightly

            # Find nearest faces within threshold distance
            distances, indices = tree.query(ray_origin, k=10, distance_upper_bound=thickness_threshold * 2)

            for dist, idx in zip(distances, indices):
                if idx == len(face_centers):  # No match found
                    continue

                if idx == i:  # Skip self
                    continue

                # Check if faces are parallel (opposite normals)
                dot_product = np.dot(normal, face_normals[idx])
                if dot_product < -0.8:  # Nearly opposite normals
                    estimated_thickness = np.linalg.norm(center - face_centers[idx])
                    if estimated_thickness <= thickness_threshold:
                        wall_faces.append(i)
                        wall_thicknesses.append(estimated_thickness)
                        break

        logger.info(f"Detected {len(wall_faces)} wall faces")

        return {
            'wall_faces': np.array(wall_faces),
            'wall_thickness': np.array(wall_thicknesses),
            'wall_normals': face_normals[wall_faces] if wall_faces else np.array([])
        }

    def get_face_neighbors(self, face_idx: int, depth: int = 1) -> np.ndarray:
        """
        Get neighboring faces up to specified depth

        Args:
            face_idx: Index of the face
            depth: How many layers of neighbors to include

        Returns:
            Array of neighboring face indices
        """
        neighbors = set([face_idx])
        current_layer = set([face_idx])

        for _ in range(depth):
            next_layer = set()
            for f in current_layer:
                # Find adjacent faces through face_adjacency
                if len(self.mesh.face_adjacency) > 0:
                    # face_adjacency contains pairs of adjacent face indices
                    adjacent_pairs = self.mesh.face_adjacency[
                        np.any(self.mesh.face_adjacency == f, axis=1)
                    ]
                    next_layer.update(adjacent_pairs.flatten())

            # Remove the original face and already-found neighbors
            next_layer = next_layer - neighbors
            neighbors.update(next_layer)
            current_layer = next_layer

        return np.array(list(neighbors))

    def calculate_volume(self) -> float:
        """Calculate mesh volume in mm³"""
        return self.mesh.volume if self.mesh.is_watertight else 0.0

    def calculate_surface_area(self) -> float:
        """Calculate mesh surface area in mm²"""
        return self.mesh.area

    def get_bounding_dimensions(self) -> Dict[str, float]:
        """Get bounding box dimensions"""
        bounds = self.mesh.bounds
        dimensions = bounds[1] - bounds[0]
        return {
            'width': dimensions[0],
            'height': dimensions[1],
            'depth': dimensions[2],
            'min': bounds[0].tolist(),
            'max': bounds[1].tolist()
        }


def load_stl(file_path: str) -> trimesh.Trimesh:
    """
    Load STL file and return mesh object

    Args:
        file_path: Path to STL file

    Returns:
        Trimesh object
    """
    logger.info(f"Loading STL from {file_path}")
    mesh = trimesh.load(file_path, force='mesh')

    # Ensure mesh is valid
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Loaded file is not a valid mesh")

    logger.info(f"Loaded mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    return mesh


def save_stl(mesh: trimesh.Trimesh, output_path: str, binary: bool = True):
    """
    Save mesh as STL file

    Args:
        mesh: Trimesh object to save
        output_path: Output file path
        binary: Save as binary STL (True) or ASCII (False)
    """
    logger.info(f"Saving STL to {output_path}")
    # Export STL - trimesh automatically saves as binary by default
    mesh.export(output_path)
    logger.info(f"Saved successfully: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")


def merge_meshes(meshes: List[trimesh.Trimesh]) -> trimesh.Trimesh:
    """
    Merge multiple meshes into one

    Args:
        meshes: List of Trimesh objects

    Returns:
        Combined mesh
    """
    logger.info(f"Merging {len(meshes)} meshes")
    combined = trimesh.util.concatenate(meshes)
    logger.info(f"Merged mesh: {len(combined.vertices)} vertices, {len(combined.faces)} faces")
    return combined


def offset_mesh(mesh: trimesh.Trimesh, distance: float) -> trimesh.Trimesh:
    """
    Offset mesh surface by distance (positive=outward, negative=inward)
    Uses advanced offset algorithm with edge handling

    Args:
        mesh: Input mesh
        distance: Offset distance in mm

    Returns:
        Offset mesh
    """
    logger.info(f"Offsetting mesh by {distance}mm")

    # Method 1: Voxel-based offset (more robust for complex geometry)
    if abs(distance) > 0.5:  # Use voxel method for larger offsets
        # Determine voxel pitch based on desired offset
        pitch = abs(distance) / 3
        voxelized = mesh.voxelized(pitch=pitch)

        # Dilate or erode based on offset direction
        if distance > 0:
            # Outward offset - dilate
            voxelized = voxelized.dilate(int(distance / pitch))
        else:
            # Inward offset - erode
            voxelized = voxelized.erode(int(abs(distance) / pitch))

        offset_mesh = voxelized.marching_cubes

    else:
        # Method 2: Vertex normal displacement for small offsets
        vertices = mesh.vertices.copy()
        vertex_normals = mesh.vertex_normals

        # Offset vertices along their normals
        vertices += vertex_normals * distance

        offset_mesh = trimesh.Trimesh(vertices=vertices, faces=mesh.faces.copy())

    # Clean up result
    offset_mesh.fix_normals()
    offset_mesh.remove_degenerate_faces()

    logger.info(f"Offset complete: {len(offset_mesh.vertices)} vertices, {len(offset_mesh.faces)} faces")
    return offset_mesh


def select_faces_by_normal(mesh: trimesh.Trimesh,
                           target_normal: np.ndarray,
                           tolerance: float = 0.1) -> np.ndarray:
    """
    Select faces by normal direction

    Args:
        mesh: Input mesh
        target_normal: Target normal vector (will be normalized)
        tolerance: Dot product tolerance (0=exact, 1=any direction)

    Returns:
        Array of selected face indices
    """
    target_normal = target_normal / np.linalg.norm(target_normal)

    dot_products = np.dot(mesh.face_normals, target_normal)
    selected = np.where(dot_products > (1 - tolerance))[0]

    logger.info(f"Selected {len(selected)} faces by normal direction")
    return selected


def select_faces_by_plane(mesh: trimesh.Trimesh,
                          plane_origin: np.ndarray,
                          plane_normal: np.ndarray,
                          thickness: float = 0.5) -> np.ndarray:
    """
    Select faces near a plane

    Args:
        mesh: Input mesh
        plane_origin: Point on plane
        plane_normal: Plane normal vector
        thickness: Distance threshold from plane

    Returns:
        Array of selected face indices
    """
    plane_normal = plane_normal / np.linalg.norm(plane_normal)

    # Calculate distance from each face center to plane
    face_centers = mesh.triangles_center
    distances = np.abs(np.dot(face_centers - plane_origin, plane_normal))

    selected = np.where(distances <= thickness)[0]

    logger.info(f"Selected {len(selected)} faces near plane")
    return selected
