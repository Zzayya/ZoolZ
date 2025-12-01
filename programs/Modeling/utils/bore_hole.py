#!/usr/bin/env python3
"""
Bore/Widen Hole Utility - Widen existing holes in meshes
Perfect for pain beads, fidget pens, and any cylindrical hole modification
"""

import trimesh
import numpy as np
from typing import Dict, Optional, Tuple, List
import logging
from scipy.spatial import cKDTree

logger = logging.getLogger(__name__)


class HoleBorer:
    """
    Widen existing cylindrical holes in meshes
    """

    def __init__(self, mesh: trimesh.Trimesh):
        """
        Initialize hole borer

        Args:
            mesh: Input mesh to modify
        """
        self.mesh = mesh.copy()

    def detect_holes(self, min_radius: float = 1.0, max_radius: float = 50.0) -> List[Dict]:
        """
        Automatically detect cylindrical holes in the mesh

        Args:
            min_radius: Minimum hole radius to detect (mm)
            max_radius: Maximum hole radius to detect (mm)

        Returns:
            List of detected holes with their properties
        """
        holes = []

        # Get mesh bounds and center
        bounds = self.mesh.bounds
        center = self.mesh.centroid

        # Try to detect holes along each axis
        for axis in ['z', 'x', 'y']:
            axis_idx = {'x': 0, 'y': 1, 'z': 2}[axis]

            # Sample along axis
            axis_holes = self._detect_holes_along_axis(axis_idx, min_radius, max_radius)
            holes.extend(axis_holes)

        logger.info(f"Detected {len(holes)} potential holes")
        return holes

    def _detect_holes_along_axis(
        self,
        axis: int,
        min_radius: float,
        max_radius: float
    ) -> List[Dict]:
        """
        Detect holes along a specific axis

        Args:
            axis: Axis index (0=X, 1=Y, 2=Z)
            min_radius: Minimum radius
            max_radius: Maximum radius

        Returns:
            List of detected holes
        """
        holes = []

        # Get cross-section at mesh center
        bounds = self.mesh.bounds
        center_pos = (bounds[0][axis] + bounds[1][axis]) / 2

        # Create slicing plane perpendicular to axis
        origin = np.array([0, 0, 0], dtype=float)
        origin[axis] = center_pos

        normal = np.array([0, 0, 0], dtype=float)
        normal[axis] = 1

        try:
            # Slice mesh to get cross-section
            slice_2d = self.mesh.section(plane_origin=origin, plane_normal=normal)

            if slice_2d is not None:
                # Convert to Path2D if needed
                if hasattr(slice_2d, 'to_planar'):
                    paths_2d = slice_2d.to_planar()[0]
                else:
                    paths_2d = slice_2d

                # Analyze paths for holes
                if hasattr(paths_2d, 'entities'):
                    for entity in paths_2d.entities:
                        # Check if entity forms a closed loop (potential hole)
                        if hasattr(entity, 'closed') and entity.closed:
                            # Estimate radius
                            vertices = paths_2d.vertices[entity.points]
                            if len(vertices) > 0:
                                centroid_2d = vertices.mean(axis=0)
                                distances = np.linalg.norm(vertices - centroid_2d, axis=1)
                                avg_radius = distances.mean()

                                if min_radius <= avg_radius <= max_radius:
                                    # Convert 2D centroid back to 3D
                                    center_3d = origin.copy()
                                    other_axes = [i for i in range(3) if i != axis]
                                    center_3d[other_axes[0]] = centroid_2d[0]
                                    center_3d[other_axes[1]] = centroid_2d[1]

                                    holes.append({
                                        'center': center_3d,
                                        'axis': axis,
                                        'radius': float(avg_radius),
                                        'axis_name': ['X', 'Y', 'Z'][axis]
                                    })

        except Exception as e:
            logger.warning(f"Error detecting holes along axis {axis}: {e}")

        return holes

    def widen_hole_at_center(
        self,
        center: np.ndarray,
        axis: int,
        current_radius: float,
        new_radius: float,
        height_range: Optional[Tuple[float, float]] = None
    ) -> trimesh.Trimesh:
        """
        Widen a hole at a specific center point

        Args:
            center: Center point of the hole [x, y, z]
            axis: Axis the hole is aligned with (0=X, 1=Y, 2=Z)
            current_radius: Current radius of the hole
            new_radius: Desired new radius
            height_range: Optional (min_height, max_height) to only widen part of the hole

        Returns:
            Modified mesh
        """
        logger.info(f"Widening hole at {center} from {current_radius}mm to {new_radius}mm")

        if new_radius <= current_radius:
            logger.warning("New radius must be larger than current radius")
            return self.mesh

        # Create a cylinder to subtract from the mesh
        cylinder_height = self.mesh.bounds[1][axis] - self.mesh.bounds[0][axis] + 10

        if height_range is not None:
            # Adjust cylinder height and position for partial widening
            min_h, max_h = height_range
            cylinder_height = max_h - min_h
            center_adjusted = center.copy()
            center_adjusted[axis] = (min_h + max_h) / 2
        else:
            center_adjusted = center.copy()

        # Create cylinder aligned with axis
        if axis == 2:  # Z-axis
            cylinder = trimesh.creation.cylinder(
                radius=new_radius,
                height=cylinder_height,
                sections=64
            )
        else:
            # Create Z-aligned cylinder then rotate
            cylinder = trimesh.creation.cylinder(
                radius=new_radius,
                height=cylinder_height,
                sections=64
            )

            # Rotate to align with axis
            if axis == 0:  # X-axis
                rotation = trimesh.transformations.rotation_matrix(
                    np.pi/2, [0, 1, 0]
                )
            else:  # Y-axis (axis == 1)
                rotation = trimesh.transformations.rotation_matrix(
                    np.pi/2, [1, 0, 0]
                )
            cylinder.apply_transform(rotation)

        # Move cylinder to hole center
        cylinder.apply_translation(center_adjusted)

        # Subtract cylinder from mesh using voxel-based approach
        try:
            # Method 1: Try trimesh boolean (requires manifold backend)
            result = self.mesh.difference(cylinder, engine='scad')
            logger.info("Hole widened successfully using SCAD engine")
            return result
        except Exception as e1:
            logger.warning(f"SCAD engine failed: {e1}")

            # Method 2: Try blender engine
            try:
                result = self.mesh.difference(cylinder, engine='blender')
                logger.info("Hole widened successfully using Blender engine")
                return result
            except Exception as e2:
                logger.warning(f"Blender engine failed: {e2}")

                # Method 3: Voxel-based approach (always works)
                try:
                    logger.info("Using voxel-based approach...")
                    pitch = min(self.mesh.extents) / 100  # Adaptive pitch

                    # Voxelize both meshes
                    mesh_voxel = self.mesh.voxelized(pitch=pitch)
                    cylinder_voxel = cylinder.voxelized(pitch=pitch)

                    # Boolean difference in voxel space
                    result_voxel = mesh_voxel.difference(cylinder_voxel)

                    # Convert back to mesh
                    result = result_voxel.marching_cubes
                    logger.info("Hole widened successfully using voxel method")
                    return result
                except Exception as e3:
                    logger.error(f"All methods failed: {e3}")
                    logger.error("Returning original mesh - hole NOT widened")
                    return self.mesh

    def widen_center_hole_auto(
        self,
        new_radius: float,
        height_range: Optional[Tuple[float, float]] = None
    ) -> trimesh.Trimesh:
        """
        Automatically detect and widen the center hole

        Args:
            new_radius: Desired new radius
            height_range: Optional (min_height, max_height) to only widen part of the hole

        Returns:
            Modified mesh
        """
        # Detect holes
        holes = self.detect_holes()

        if not holes:
            logger.error("No holes detected in mesh")
            return self.mesh

        # Find hole closest to mesh centroid (usually the center hole)
        centroid = self.mesh.centroid
        closest_hole = min(holes, key=lambda h: np.linalg.norm(h['center'] - centroid))

        logger.info(f"Auto-detected center hole: {closest_hole}")

        return self.widen_hole_at_center(
            center=closest_hole['center'],
            axis=closest_hole['axis'],
            current_radius=closest_hole['radius'],
            new_radius=new_radius,
            height_range=height_range
        )


def widen_hole(
    mesh: trimesh.Trimesh,
    new_radius: float,
    auto_detect: bool = True,
    center: Optional[np.ndarray] = None,
    axis: int = 2,
    current_radius: Optional[float] = None,
    height_range: Optional[Tuple[float, float]] = None
) -> Dict:
    """
    High-level function to widen a hole in a mesh

    Args:
        mesh: Input mesh
        new_radius: Desired new radius (mm)
        auto_detect: Automatically detect hole (True) or use manual params (False)
        center: Manual hole center point [x, y, z]
        axis: Manual hole axis (0=X, 1=Y, 2=Z)
        current_radius: Manual current radius
        height_range: Optional (min_height, max_height) to only widen part of hole

    Returns:
        Dict containing:
            - mesh: Modified mesh
            - stats: Statistics about the operation
    """
    borer = HoleBorer(mesh)

    if auto_detect:
        result_mesh = borer.widen_center_hole_auto(new_radius, height_range)
        detected_holes = borer.detect_holes()
    else:
        if center is None or current_radius is None:
            raise ValueError("Manual mode requires center and current_radius")

        result_mesh = borer.widen_hole_at_center(
            center=center,
            axis=axis,
            current_radius=current_radius,
            new_radius=new_radius,
            height_range=height_range
        )
        detected_holes = []

    # Calculate stats
    stats = {
        'original_vertices': len(mesh.vertices),
        'original_faces': len(mesh.faces),
        'result_vertices': len(result_mesh.vertices),
        'result_faces': len(result_mesh.faces),
        'is_watertight': result_mesh.is_watertight,
        'new_radius': float(new_radius),
        'detected_holes': len(detected_holes)
    }

    if mesh.is_watertight and result_mesh.is_watertight:
        stats['volume_removed'] = float(mesh.volume - result_mesh.volume)

    return {
        'mesh': result_mesh,
        'stats': stats,
        'detected_holes': detected_holes
    }


def get_hole_info(mesh: trimesh.Trimesh) -> Dict:
    """
    Analyze mesh and return information about detected holes

    Args:
        mesh: Input mesh

    Returns:
        Dict with hole detection information
    """
    borer = HoleBorer(mesh)
    holes = borer.detect_holes()

    return {
        'num_holes': len(holes),
        'holes': holes
    }
