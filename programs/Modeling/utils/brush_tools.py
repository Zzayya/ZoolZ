#!/usr/bin/env python3
"""
Brush Tools - Advanced selection and manipulation tools
Supports vertex selection, face selection, click-drag highlighting, quadrant selection
"""

import trimesh
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class BrushTools:
    """Advanced selection and manipulation tools for 3D meshes"""

    @staticmethod
    def select_vertices_in_radius(
        mesh: trimesh.Trimesh,
        center_point: np.ndarray,
        radius: float
    ) -> List[int]:
        """
        Select all vertices within a spherical radius from center point

        Args:
            mesh: Input mesh
            center_point: Center of selection sphere [x, y, z]
            radius: Selection radius

        Returns:
            List of vertex indices
        """
        center = np.array(center_point)
        distances = np.linalg.norm(mesh.vertices - center, axis=1)
        selected_indices = np.where(distances <= radius)[0]

        logger.info(f"Selected {len(selected_indices)} vertices within radius {radius}")
        return selected_indices.tolist()

    @staticmethod
    def select_vertices_in_box(
        mesh: trimesh.Trimesh,
        min_corner: np.ndarray,
        max_corner: np.ndarray
    ) -> List[int]:
        """
        Select all vertices within a box region

        Args:
            mesh: Input mesh
            min_corner: Minimum corner [x, y, z]
            max_corner: Maximum corner [x, y, z]

        Returns:
            List of vertex indices
        """
        min_c = np.array(min_corner)
        max_c = np.array(max_corner)

        in_box = np.all((mesh.vertices >= min_c) & (mesh.vertices <= max_c), axis=1)
        selected_indices = np.where(in_box)[0]

        logger.info(f"Selected {len(selected_indices)} vertices in box")
        return selected_indices.tolist()

    @staticmethod
    def select_face_by_point(
        mesh: trimesh.Trimesh,
        point: np.ndarray,
        direction: Optional[np.ndarray] = None
    ) -> Optional[int]:
        """
        Select face closest to a point (or by ray intersection)

        Args:
            mesh: Input mesh
            point: Point in 3D space
            direction: Optional ray direction for intersection

        Returns:
            Face index or None
        """
        if direction is not None:
            # Ray intersection method
            ray_dir = np.array(direction) / np.linalg.norm(direction)
            locations, index_ray, index_tri = mesh.ray.intersects_location(
                ray_origins=[point],
                ray_directions=[ray_dir]
            )

            if len(index_tri) > 0:
                return int(index_tri[0])
        else:
            # Closest point method
            closest_point, distance, face_index = mesh.nearest.on_surface([point])
            return int(face_index[0])

        return None

    @staticmethod
    def select_faces_in_region(
        mesh: trimesh.Trimesh,
        center_point: np.ndarray,
        radius: float
    ) -> List[int]:
        """
        Select all faces with centers within radius

        Args:
            mesh: Input mesh
            center_point: Center of selection
            radius: Selection radius

        Returns:
            List of face indices
        """
        # Get face centers
        face_centers = mesh.triangles_center
        center = np.array(center_point)

        distances = np.linalg.norm(face_centers - center, axis=1)
        selected_faces = np.where(distances <= radius)[0]

        logger.info(f"Selected {len(selected_faces)} faces within radius")
        return selected_faces.tolist()

    @staticmethod
    def select_quadrant_of_face(
        mesh: trimesh.Trimesh,
        face_index: int,
        quadrant: str = 'bottom_right'
    ) -> Dict:
        """
        Divide a face into quadrants and select one

        Args:
            mesh: Input mesh
            face_index: Face to divide
            quadrant: Which quadrant ('top_left', 'top_right', 'bottom_left', 'bottom_right')

        Returns:
            Dict with new sub-face info
        """
        # Get the three vertices of the triangle
        face_verts = mesh.vertices[mesh.faces[face_index]]

        # Calculate center of triangle
        center = np.mean(face_verts, axis=0)

        # Calculate midpoints of edges
        midpoint_01 = (face_verts[0] + face_verts[1]) / 2
        midpoint_12 = (face_verts[1] + face_verts[2]) / 2
        midpoint_20 = (face_verts[2] + face_verts[0]) / 2

        # Define quadrants (simplified for triangle)
        # We'll create 4 sub-triangles by connecting center to midpoints
        sub_triangles = {
            'center_0': [center, face_verts[0], midpoint_01],
            'center_1': [center, face_verts[1], midpoint_12],
            'center_2': [center, face_verts[2], midpoint_20],
            'center_mid': [center, midpoint_01, midpoint_12]
        }

        # Map quadrant names to sub-triangles (simplified)
        quadrant_map = {
            'top_left': 'center_0',
            'top_right': 'center_1',
            'bottom_left': 'center_2',
            'bottom_right': 'center_mid'
        }

        selected_quadrant = quadrant_map.get(quadrant, 'center_0')

        return {
            'vertices': sub_triangles[selected_quadrant],
            'quadrant': quadrant,
            'original_face': face_index
        }

    @staticmethod
    def select_corner_vertices(
        mesh: trimesh.Trimesh
    ) -> List[int]:
        """
        Select corner vertices (vertices with highest curvature or at extremes)

        Returns:
            List of corner vertex indices
        """
        # Find extreme vertices (min/max in each dimension)
        corners = []

        for dim in range(3):
            min_idx = np.argmin(mesh.vertices[:, dim])
            max_idx = np.argmax(mesh.vertices[:, dim])
            corners.extend([int(min_idx), int(max_idx)])

        # Remove duplicates
        corners = list(set(corners))

        logger.info(f"Found {len(corners)} corner vertices")
        return corners

    @staticmethod
    def highlight_selection(
        mesh: trimesh.Trimesh,
        selected_vertices: List[int],
        highlight_color: List[int] = [255, 215, 0, 180]  # Gold with transparency
    ) -> trimesh.Trimesh:
        """
        Color selected vertices to create highlight effect

        Args:
            mesh: Input mesh
            selected_vertices: Vertex indices to highlight
            highlight_color: RGBA color for highlight

        Returns:
            Mesh with vertex colors applied
        """
        # Create vertex colors array (default to white)
        if not hasattr(mesh.visual, 'vertex_colors') or mesh.visual.vertex_colors is None:
            vertex_colors = np.ones((len(mesh.vertices), 4), dtype=np.uint8) * 200
        else:
            vertex_colors = np.array(mesh.visual.vertex_colors)

        # Apply highlight color to selected vertices
        vertex_colors[selected_vertices] = highlight_color

        mesh.visual.vertex_colors = vertex_colors

        logger.info(f"Highlighted {len(selected_vertices)} vertices")
        return mesh

    @staticmethod
    def paint_brush(
        mesh: trimesh.Trimesh,
        brush_center: np.ndarray,
        brush_radius: float,
        paint_color: List[int] = [255, 0, 0, 255],
        strength: float = 1.0
    ) -> trimesh.Trimesh:
        """
        Paint vertices within brush radius with color (with falloff)

        Args:
            mesh: Input mesh
            brush_center: Center of brush
            brush_radius: Brush radius
            paint_color: RGBA color to paint
            strength: Paint strength (0-1), affects color blending

        Returns:
            Mesh with painted vertices
        """
        center = np.array(brush_center)
        distances = np.linalg.norm(mesh.vertices - center, axis=1)

        # Create vertex colors if they don't exist
        if not hasattr(mesh.visual, 'vertex_colors') or mesh.visual.vertex_colors is None:
            vertex_colors = np.ones((len(mesh.vertices), 4), dtype=np.uint8) * 200
        else:
            vertex_colors = np.array(mesh.visual.vertex_colors)

        # Apply paint with falloff
        affected = distances <= brush_radius
        falloff = 1.0 - (distances[affected] / brush_radius)  # Linear falloff
        falloff = np.power(falloff, 2)  # Square for smoother falloff

        paint_color = np.array(paint_color, dtype=np.uint8)

        for i, idx in enumerate(np.where(affected)[0]):
            blend_factor = falloff[i] * strength
            vertex_colors[idx] = (
                vertex_colors[idx] * (1 - blend_factor) +
                paint_color * blend_factor
            ).astype(np.uint8)

        mesh.visual.vertex_colors = vertex_colors

        logger.info(f"Painted {np.sum(affected)} vertices with brush")
        return mesh

    @staticmethod
    def select_connected_vertices(
        mesh: trimesh.Trimesh,
        seed_vertex: int,
        max_distance: Optional[float] = None
    ) -> List[int]:
        """
        Select all vertices connected to seed vertex (flood fill)

        Args:
            mesh: Input mesh
            seed_vertex: Starting vertex index
            max_distance: Optional maximum geodesic distance

        Returns:
            List of connected vertex indices
        """
        # Get adjacency information
        edges = mesh.edges_unique

        # Build adjacency list
        adjacency = {i: set() for i in range(len(mesh.vertices))}
        for edge in edges:
            adjacency[edge[0]].add(edge[1])
            adjacency[edge[1]].add(edge[0])

        # Flood fill
        visited = set([seed_vertex])
        queue = [seed_vertex]

        if max_distance is not None:
            distances = {seed_vertex: 0.0}

        while queue:
            current = queue.pop(0)

            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    if max_distance is not None:
                        # Calculate geodesic distance (approximate with edge length)
                        dist = distances[current] + np.linalg.norm(
                            mesh.vertices[current] - mesh.vertices[neighbor]
                        )
                        if dist <= max_distance:
                            visited.add(neighbor)
                            distances[neighbor] = dist
                            queue.append(neighbor)
                    else:
                        visited.add(neighbor)
                        queue.append(neighbor)

        logger.info(f"Selected {len(visited)} connected vertices from seed {seed_vertex}")
        return list(visited)

    @staticmethod
    def create_selection_outline(
        mesh: trimesh.Trimesh,
        selected_vertices: List[int],
        outline_thickness: float = 0.5
    ) -> trimesh.Trimesh:
        """
        Create an outline around selected vertices (border glow effect)

        Args:
            mesh: Input mesh
            selected_vertices: Vertices to outline
            outline_thickness: Thickness of outline

        Returns:
            Mesh with outline applied
        """
        # Find boundary edges of selection
        selected_set = set(selected_vertices)
        boundary_vertices = set()

        edges = mesh.edges_unique
        for edge in edges:
            v1, v2 = edge
            # Edge is on boundary if one vertex is selected and other isn't
            if (v1 in selected_set) != (v2 in selected_set):
                boundary_vertices.add(v1 if v1 in selected_set else v2)

        # Highlight boundary vertices with animated color (pulsing effect)
        outline_color = [255, 215, 0, 255]  # Gold
        mesh = BrushTools.highlight_selection(mesh, list(boundary_vertices), outline_color)

        logger.info(f"Created outline with {len(boundary_vertices)} boundary vertices")
        return mesh


class SelectionManager:
    """Manage selection state across operations"""

    def __init__(self):
        self.current_selection = []
        self.selection_history = []
        self.max_history = 10

    def select(self, indices: List[int], add_to_selection: bool = False):
        """Add new selection"""
        if not add_to_selection:
            self.selection_history.append(self.current_selection.copy())
            self.current_selection = indices
        else:
            self.current_selection.extend(indices)
            self.current_selection = list(set(self.current_selection))  # Remove duplicates

        # Limit history size
        if len(self.selection_history) > self.max_history:
            self.selection_history.pop(0)

    def deselect(self, indices: List[int]):
        """Remove from selection"""
        self.selection_history.append(self.current_selection.copy())
        self.current_selection = [idx for idx in self.current_selection if idx not in indices]

    def undo(self):
        """Undo last selection change"""
        if self.selection_history:
            self.current_selection = self.selection_history.pop()

    def clear(self):
        """Clear current selection"""
        self.selection_history.append(self.current_selection.copy())
        self.current_selection = []

    def get_selection(self) -> List[int]:
        """Get current selection"""
        return self.current_selection.copy()
