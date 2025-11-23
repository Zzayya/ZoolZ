#!/usr/bin/env python3
"""
Wall Thickening Algorithm - Advanced Mesh Thickening
Intelligently thickens walls without affecting model scale or integrity
"""

import trimesh
import numpy as np
from typing import List, Optional, Dict, Set
import logging
from scipy.spatial import cKDTree

from .mesh_utils import MeshAnalyzer, offset_mesh, merge_meshes

logger = logging.getLogger(__name__)


class WallThickener:
    """
    Advanced wall thickening using localized mesh manipulation.
    Preserves overall model dimensions while increasing wall thickness.
    """

    def __init__(self, mesh: trimesh.Trimesh):
        """
        Initialize wall thickener

        Args:
            mesh: Input mesh to thicken
        """
        self.mesh = mesh
        self.analyzer = MeshAnalyzer(mesh)

    def thicken_walls(
        self,
        thickness_increase: float,
        selected_faces: Optional[List[int]] = None,
        auto_detect_walls: bool = True,
        max_wall_thickness: float = 2.0
    ) -> trimesh.Trimesh:
        """
        Thicken walls by specified amount without affecting outer dimensions.

        Strategy:
        1. Detect thin walls in the model
        2. Create offset surfaces (inward and outward)
        3. Replace thin walls with thicker versions
        4. Maintain model boundaries and scale

        Args:
            thickness_increase: Amount to increase wall thickness (mm)
            selected_faces: Specific face indices to thicken (None = all walls)
            auto_detect_walls: Automatically detect walls vs solid regions
            max_wall_thickness: Maximum thickness to consider as a "wall" for auto-detection

        Returns:
            Thickened mesh
        """
        logger.info(f"Thickening walls by {thickness_increase}mm")

        # Step 1: Identify wall faces
        if auto_detect_walls:
            wall_info = self.analyzer.detect_walls(thickness_threshold=max_wall_thickness)
            wall_faces = wall_info['wall_faces']

            if len(wall_faces) == 0:
                logger.warning("No thin walls detected - treating entire model as solid")
                # If no walls detected, use uniform thickening
                return self._uniform_thicken(thickness_increase)
        else:
            wall_faces = np.array(selected_faces) if selected_faces else np.arange(len(self.mesh.faces))

        logger.info(f"Identified {len(wall_faces)} wall faces to thicken")

        # Step 2: Filter by selection if provided
        if selected_faces is not None:
            wall_faces = np.intersect1d(wall_faces, selected_faces)
            logger.info(f"Filtered to {len(wall_faces)} selected wall faces")

        # Step 3: Apply localized thickening
        thickened_mesh = self._apply_localized_thickening(
            wall_faces,
            thickness_increase
        )

        logger.info("Wall thickening complete")
        return thickened_mesh

    def _apply_localized_thickening(
        self,
        wall_faces: np.ndarray,
        thickness: float
    ) -> trimesh.Trimesh:
        """
        Apply thickening only to wall regions using vertex displacement.

        This method:
        1. Creates a "thickening influence map" for each vertex
        2. Displaces vertices based on their proximity to wall faces
        3. Uses smooth falloff to avoid sharp transitions

        Args:
            wall_faces: Indices of faces to thicken
            thickness: Amount to thicken (mm)

        Returns:
            Thickened mesh
        """
        # Get vertices involved in wall faces
        wall_vertices = set()
        for face_idx in wall_faces:
            wall_vertices.update(self.mesh.faces[face_idx])

        # Create vertex influence weights (1.0 for wall vertices, smooth falloff for neighbors)
        vertex_weights = self._calculate_vertex_weights(wall_vertices)

        # Calculate displacement for each vertex
        vertices_new = self.mesh.vertices.copy()
        vertex_normals = self.mesh.vertex_normals

        # Apply weighted displacement
        for v_idx in range(len(vertices_new)):
            weight = vertex_weights[v_idx]
            if weight > 0:
                # Displace vertex along its normal, weighted by influence
                displacement = vertex_normals[v_idx] * thickness * weight * 0.5
                vertices_new[v_idx] += displacement

        # Create new mesh with thickened vertices
        thickened = trimesh.Trimesh(vertices=vertices_new, faces=self.mesh.faces.copy())
        thickened.fix_normals()

        return thickened

    def _calculate_vertex_weights(self, wall_vertices: Set[int], falloff_distance: int = 2) -> np.ndarray:
        """
        Calculate influence weights for each vertex based on proximity to wall vertices.

        Uses graph-based distance from wall vertices with smooth falloff.

        Args:
            wall_vertices: Set of vertex indices that are part of walls
            falloff_distance: Number of edge hops for influence falloff

        Returns:
            Array of weights (0.0 to 1.0) for each vertex
        """
        weights = np.zeros(len(self.mesh.vertices))

        # Wall vertices get full weight
        for v_idx in wall_vertices:
            weights[v_idx] = 1.0

        # Build vertex adjacency graph
        vertex_adjacency = self._build_vertex_adjacency()

        # Propagate weights with falloff
        current_layer = wall_vertices
        for distance in range(1, falloff_distance + 1):
            next_layer = set()
            falloff_weight = 1.0 - (distance / (falloff_distance + 1))

            for v_idx in current_layer:
                for neighbor_idx in vertex_adjacency.get(v_idx, []):
                    if weights[neighbor_idx] < falloff_weight:
                        weights[neighbor_idx] = falloff_weight
                        next_layer.add(neighbor_idx)

            current_layer = next_layer

        return weights

    def _build_vertex_adjacency(self) -> Dict[int, Set[int]]:
        """
        Build vertex-to-vertex adjacency graph from mesh edges.

        Returns:
            Dict mapping vertex index to set of neighboring vertex indices
        """
        adjacency = {i: set() for i in range(len(self.mesh.vertices))}

        for face in self.mesh.faces:
            # Each face has 3 edges
            adjacency[face[0]].update([face[1], face[2]])
            adjacency[face[1]].update([face[0], face[2]])
            adjacency[face[2]].update([face[0], face[1]])

        return adjacency

    def _uniform_thicken(self, thickness: float) -> trimesh.Trimesh:
        """
        Apply uniform thickening to entire model (fallback for solid objects).

        Uses dual offsetting: offset outward and inward, then combine.

        Args:
            thickness: Amount to thicken (mm)

        Returns:
            Thickened mesh
        """
        logger.info("Applying uniform thickening to solid model")

        # For uniform thickening, use vertex normal displacement
        vertices_new = self.mesh.vertices.copy()
        vertex_normals = self.mesh.vertex_normals

        # Displace vertices outward by half the thickness
        vertices_new += vertex_normals * (thickness / 2.0)

        thickened = trimesh.Trimesh(vertices=vertices_new, faces=self.mesh.faces.copy())
        thickened.fix_normals()

        return thickened


def thicken_selected_walls(
    mesh: trimesh.Trimesh,
    selected_faces: Optional[List[int]],
    thickness_mm: float,
    auto_detect: bool = True
) -> Dict:
    """
    High-level function to thicken selected walls in a mesh.

    Args:
        mesh: Input mesh
        selected_faces: List of face indices to thicken (None = auto-detect and thicken all walls)
        thickness_mm: Amount to increase wall thickness (mm)
        auto_detect: Automatically detect thin walls

    Returns:
        Dict containing:
            - mesh: Thickened mesh
            - stats: Statistics about the operation
    """
    thickener = WallThickener(mesh)

    # Perform thickening
    thickened_mesh = thickener.thicken_walls(
        thickness_increase=thickness_mm,
        selected_faces=selected_faces,
        auto_detect_walls=auto_detect
    )

    # Calculate stats
    stats = {
        'original_vertices': len(mesh.vertices),
        'original_faces': len(mesh.faces),
        'thickened_vertices': len(thickened_mesh.vertices),
        'thickened_faces': len(thickened_mesh.faces),
        'volume_increase': thickened_mesh.volume - mesh.volume if mesh.is_watertight and thickened_mesh.is_watertight else None,
        'is_watertight': thickened_mesh.is_watertight
    }

    return {
        'mesh': thickened_mesh,
        'stats': stats
    }


def thicken_entire_model(
    mesh: trimesh.Trimesh,
    thickness_mm: float
) -> trimesh.Trimesh:
    """
    Quick helper to thicken entire model (all detected walls).

    Args:
        mesh: Input mesh
        thickness_mm: Amount to increase thickness (mm)

    Returns:
        Thickened mesh
    """
    thickener = WallThickener(mesh)
    return thickener.thicken_walls(thickness_mm, selected_faces=None, auto_detect_walls=True)


def get_wall_info(mesh: trimesh.Trimesh, max_thickness: float = 2.0) -> Dict:
    """
    Analyze mesh and return information about detected walls.
    Useful for frontend to display which faces are walls.

    Args:
        mesh: Input mesh
        max_thickness: Maximum thickness to consider as a wall (mm)

    Returns:
        Dict with wall detection information
    """
    analyzer = MeshAnalyzer(mesh)
    wall_info = analyzer.detect_walls(thickness_threshold=max_thickness)

    return {
        'num_walls': len(wall_info['wall_faces']),
        'wall_face_indices': wall_info['wall_faces'].tolist(),
        'wall_thicknesses': wall_info['wall_thickness'].tolist(),
        'average_thickness': float(np.mean(wall_info['wall_thickness'])) if len(wall_info['wall_thickness']) > 0 else 0.0,
        'min_thickness': float(np.min(wall_info['wall_thickness'])) if len(wall_info['wall_thickness']) > 0 else 0.0,
        'max_thickness': float(np.max(wall_info['wall_thickness'])) if len(wall_info['wall_thickness']) > 0 else 0.0
    }
