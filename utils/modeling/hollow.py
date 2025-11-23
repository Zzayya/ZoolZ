#!/usr/bin/env python3
"""
Hollowing Algorithm - Create Hollow Models with Uniform Wall Thickness
Advanced mesh hollowing using dual-surface offsetting and boolean operations
"""

import trimesh
import numpy as np
from typing import Optional, Dict, List, Tuple
import logging

from .mesh_utils import offset_mesh, MeshAnalyzer

logger = logging.getLogger(__name__)


class MeshHollower:
    """
    Advanced mesh hollowing with drainage hole support and uniform wall thickness.
    """

    def __init__(self, mesh: trimesh.Trimesh):
        """
        Initialize hollower

        Args:
            mesh: Input mesh to hollow (should be watertight)
        """
        self.mesh = mesh
        self.analyzer = MeshAnalyzer(mesh)

        if not mesh.is_watertight:
            logger.warning("Input mesh is not watertight - hollowing may produce unexpected results")

    def hollow(
        self,
        wall_thickness: float,
        drainage_holes: Optional[List[Dict]] = None,
        preserve_bottom: bool = False
    ) -> trimesh.Trimesh:
        """
        Create hollow version of mesh with uniform wall thickness.

        Strategy:
        1. Create inner surface by offsetting mesh inward
        2. Invert normals of inner surface
        3. Combine outer and inner surfaces
        4. Optionally add drainage holes
        5. Optionally remove bottom for easier printing

        Args:
            wall_thickness: Desired wall thickness (mm)
            drainage_holes: List of drainage hole specs (position, diameter)
            preserve_bottom: If False, remove bottom face for drainage

        Returns:
            Hollow mesh
        """
        logger.info(f"Hollowing mesh with {wall_thickness}mm wall thickness")

        # Step 1: Create inner surface (offset inward)
        inner_mesh = offset_mesh(self.mesh, -wall_thickness)

        # Step 2: Invert inner surface normals (so it faces inward)
        inner_mesh.invert()

        # Step 3: Combine outer and inner surfaces
        hollow_mesh = trimesh.util.concatenate([self.mesh, inner_mesh])

        # Step 4: Add drainage holes if specified
        if drainage_holes:
            hollow_mesh = self._add_drainage_holes(hollow_mesh, drainage_holes)

        # Step 5: Remove bottom if requested (for easier printing and drainage)
        if preserve_bottom is False:
            hollow_mesh = self._remove_bottom_faces(hollow_mesh)

        # Clean up the result
        hollow_mesh.fix_normals()
        hollow_mesh.remove_degenerate_faces()

        logger.info(f"Hollowing complete: {len(hollow_mesh.vertices)} vertices, {len(hollow_mesh.faces)} faces")
        return hollow_mesh

    def hollow_with_infill(
        self,
        wall_thickness: float,
        infill_density: float = 0.2,
        infill_pattern: str = 'grid'
    ) -> trimesh.Trimesh:
        """
        Create hollow mesh with internal support structure (infill).

        Args:
            wall_thickness: Wall thickness (mm)
            infill_density: Infill density (0.0 to 1.0)
            infill_pattern: Pattern type ('grid', 'honeycomb', 'gyroid')

        Returns:
            Hollow mesh with infill
        """
        logger.info(f"Creating hollow mesh with {infill_density * 100}% {infill_pattern} infill")

        # Create basic hollow
        hollow = self.hollow(wall_thickness, preserve_bottom=True)

        # Generate infill structure
        infill = self._generate_infill(infill_density, infill_pattern)

        # Combine hollow shell with infill
        result = trimesh.util.concatenate([hollow, infill])

        return result

    def _add_drainage_holes(self, mesh: trimesh.Trimesh, holes: List[Dict]) -> trimesh.Trimesh:
        """
        Add drainage holes to mesh using boolean subtraction.

        Args:
            mesh: Input hollow mesh
            holes: List of hole specifications, each with:
                   - position: [x, y, z] center point
                   - diameter: hole diameter (mm)
                   - direction: [x, y, z] hole direction vector

        Returns:
            Mesh with drainage holes
        """
        result_mesh = mesh

        for hole_spec in holes:
            position = np.array(hole_spec['position'])
            diameter = hole_spec['diameter']
            direction = np.array(hole_spec.get('direction', [0, 0, -1]))
            direction = direction / np.linalg.norm(direction)

            # Create cylinder for the hole
            hole_length = max(mesh.bounds[1] - mesh.bounds[0]) * 2  # Make it long enough
            hole_cylinder = trimesh.creation.cylinder(
                radius=diameter / 2,
                height=hole_length,
                sections=16
            )

            # Orient cylinder along direction vector
            # Calculate rotation to align [0,0,1] with direction
            z_axis = np.array([0, 0, 1])
            rotation_axis = np.cross(z_axis, direction)
            if np.linalg.norm(rotation_axis) > 1e-6:
                rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
                rotation_angle = np.arccos(np.clip(np.dot(z_axis, direction), -1.0, 1.0))
                rotation_matrix = trimesh.transformations.rotation_matrix(rotation_angle, rotation_axis)
                hole_cylinder.apply_transform(rotation_matrix)

            # Position cylinder
            hole_cylinder.apply_translation(position)

            # Subtract hole from mesh (boolean operation)
            try:
                result_mesh = result_mesh.difference(hole_cylinder)
            except Exception as e:
                logger.warning(f"Failed to create drainage hole: {e}")

        return result_mesh

    def _remove_bottom_faces(self, mesh: trimesh.Trimesh, threshold: float = 0.1) -> trimesh.Trimesh:
        """
        Remove bottom-facing faces (for drainage and easier printing).

        Args:
            mesh: Input mesh
            threshold: Z-coordinate threshold relative to min Z

        Returns:
            Mesh with bottom faces removed
        """
        # Find minimum Z coordinate
        min_z = mesh.bounds[0][2]

        # Get face centers
        face_centers = mesh.triangles_center

        # Identify bottom faces (close to min_z and facing downward)
        is_bottom_face = face_centers[:, 2] < (min_z + threshold)
        faces_to_keep = ~is_bottom_face

        # Create new mesh without bottom faces
        new_faces = mesh.faces[faces_to_keep]

        # Remove unused vertices
        result = trimesh.Trimesh(vertices=mesh.vertices, faces=new_faces)
        result.remove_unreferenced_vertices()

        logger.info(f"Removed {np.sum(is_bottom_face)} bottom faces")
        return result

    def _generate_infill(self, density: float, pattern: str) -> trimesh.Trimesh:
        """
        Generate internal support structure (infill).

        Args:
            density: Infill density (0.0 to 1.0)
            pattern: Pattern type ('grid', 'honeycomb', 'gyroid')

        Returns:
            Infill mesh
        """
        bounds = self.mesh.bounds
        size = bounds[1] - bounds[0]

        # Calculate grid spacing based on density
        spacing = (size[0] * size[1] * size[2]) ** (1/3) / (density * 10)

        if pattern == 'grid':
            return self._generate_grid_infill(bounds, spacing)
        elif pattern == 'honeycomb':
            return self._generate_honeycomb_infill(bounds, spacing)
        elif pattern == 'gyroid':
            return self._generate_gyroid_infill(bounds, spacing)
        else:
            logger.warning(f"Unknown infill pattern: {pattern}, using grid")
            return self._generate_grid_infill(bounds, spacing)

    def _generate_grid_infill(self, bounds: np.ndarray, spacing: float) -> trimesh.Trimesh:
        """Generate simple grid infill pattern"""
        lines = []

        # Generate grid lines in X direction
        y = bounds[0][1]
        while y <= bounds[1][1]:
            z = bounds[0][2]
            while z <= bounds[1][2]:
                line = trimesh.creation.cylinder(
                    radius=0.4,  # Thin support beam
                    height=bounds[1][0] - bounds[0][0],
                    sections=8
                )
                line.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
                line.apply_translation([(bounds[1][0] + bounds[0][0]) / 2, y, z])
                lines.append(line)
                z += spacing
            y += spacing

        # Generate grid lines in Y direction
        x = bounds[0][0]
        while x <= bounds[1][0]:
            z = bounds[0][2]
            while z <= bounds[1][2]:
                line = trimesh.creation.cylinder(
                    radius=0.4,
                    height=bounds[1][1] - bounds[0][1],
                    sections=8
                )
                line.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0]))
                line.apply_translation([x, (bounds[1][1] + bounds[0][1]) / 2, z])
                lines.append(line)
                z += spacing
            x += spacing

        return trimesh.util.concatenate(lines) if lines else trimesh.Trimesh()

    def _generate_honeycomb_infill(self, bounds: np.ndarray, spacing: float) -> trimesh.Trimesh:
        """Generate honeycomb infill pattern (placeholder - simplified)"""
        # Simplified honeycomb using cylinders
        return self._generate_grid_infill(bounds, spacing * 1.5)

    def _generate_gyroid_infill(self, bounds: np.ndarray, spacing: float) -> trimesh.Trimesh:
        """Generate gyroid infill pattern (placeholder - simplified)"""
        # Gyroid is complex - use grid as placeholder
        return self._generate_grid_infill(bounds, spacing)


def hollow_mesh(
    mesh: trimesh.Trimesh,
    wall_thickness: float,
    add_drainage: bool = True,
    drainage_diameter: float = 5.0
) -> Dict:
    """
    High-level function to hollow a mesh.

    Args:
        mesh: Input mesh (should be watertight)
        wall_thickness: Wall thickness (mm)
        add_drainage: Add automatic drainage holes at bottom
        drainage_diameter: Diameter of drainage holes (mm)

    Returns:
        Dict containing:
            - mesh: Hollowed mesh
            - stats: Statistics about the operation
    """
    hollower = MeshHollower(mesh)

    # Prepare drainage holes if requested
    drainage_holes = None
    if add_drainage:
        # Add 2-3 drainage holes at bottom
        bounds = mesh.bounds
        center = (bounds[0] + bounds[1]) / 2
        drainage_holes = [
            {
                'position': [center[0], center[1], bounds[0][2]],
                'diameter': drainage_diameter,
                'direction': [0, 0, -1]
            }
        ]

    # Perform hollowing
    hollow_mesh = hollower.hollow(
        wall_thickness=wall_thickness,
        drainage_holes=drainage_holes,
        preserve_bottom=False
    )

    # Calculate stats
    stats = {
        'original_volume': mesh.volume if mesh.is_watertight else None,
        'hollow_volume': hollow_mesh.volume if hollow_mesh.is_watertight else None,
        'volume_reduction': (mesh.volume - hollow_mesh.volume) if mesh.is_watertight and hollow_mesh.is_watertight else None,
        'wall_thickness': wall_thickness,
        'vertices': len(hollow_mesh.vertices),
        'faces': len(hollow_mesh.faces),
        'is_watertight': hollow_mesh.is_watertight
    }

    return {
        'mesh': hollow_mesh,
        'stats': stats
    }
