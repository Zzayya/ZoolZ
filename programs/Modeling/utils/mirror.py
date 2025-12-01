#!/usr/bin/env python3
"""
Mesh Mirroring - Mirror and Symmetrize Meshes
Advanced mirroring with plane specification and merge options
"""

import trimesh
import numpy as np
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MeshMirror:
    """
    Advanced mesh mirroring with multiple axis support and symmetrization.
    """

    def __init__(self, mesh: trimesh.Trimesh):
        """
        Initialize mesh mirror

        Args:
            mesh: Input mesh to mirror
        """
        self.mesh = mesh.copy()

    def mirror(
        self,
        axis: str = 'x',
        merge: bool = False,
        center_at_origin: bool = True
    ) -> trimesh.Trimesh:
        """
        Mirror mesh across specified axis.

        Args:
            axis: Axis to mirror across ('x', 'y', 'z')
            merge: If True, merge original and mirrored halves
            center_at_origin: Center mesh at origin before mirroring

        Returns:
            Mirrored mesh (or combined if merge=True)
        """
        logger.info(f"Mirroring mesh across {axis.upper()}-axis")

        mesh_to_mirror = self.mesh.copy()

        # Center at origin if requested
        if center_at_origin:
            center = mesh_to_mirror.bounds.mean(axis=0)
            mesh_to_mirror.apply_translation(-center)

        # Create reflection matrix
        reflection_matrix = self._get_reflection_matrix(axis)

        # Apply reflection
        mirrored = mesh_to_mirror.copy()
        mirrored.apply_transform(reflection_matrix)

        # Invert normals (mirroring flips them)
        mirrored.invert()

        if merge:
            # Combine original and mirrored
            combined = trimesh.util.concatenate([mesh_to_mirror, mirrored])
            logger.info(f"Merged original and mirror: {len(combined.vertices)} vertices")
            return combined
        else:
            logger.info(f"Created mirror: {len(mirrored.vertices)} vertices")
            return mirrored

    def symmetrize(
        self,
        axis: str = 'x',
        keep_side: str = 'positive'
    ) -> trimesh.Trimesh:
        """
        Make mesh symmetrical by mirroring one half.

        Args:
            axis: Axis of symmetry ('x', 'y', 'z')
            keep_side: Which side to keep ('positive' or 'negative')

        Returns:
            Symmetrized mesh
        """
        logger.info(f"Symmetrizing mesh along {axis.upper()}-axis, keeping {keep_side} side")

        # Center mesh at origin
        center = self.mesh.bounds.mean(axis=0)
        mesh_centered = self.mesh.copy()
        mesh_centered.apply_translation(-center)

        # Cut mesh in half
        axis_idx = {'x': 0, 'y': 1, 'z': 2}[axis.lower()]

        # Create cutting plane at origin perpendicular to axis
        plane_origin = np.array([0.0, 0.0, 0.0])
        plane_normal = np.array([0.0, 0.0, 0.0])
        plane_normal[axis_idx] = -1.0 if keep_side == 'positive' else 1.0

        # Slice mesh to keep only one side
        half_mesh = self._slice_mesh(mesh_centered, plane_origin, plane_normal)

        # Mirror the half to create symmetrical mesh
        reflection_matrix = self._get_reflection_matrix(axis)
        mirrored_half = half_mesh.copy()
        mirrored_half.apply_transform(reflection_matrix)
        mirrored_half.invert()

        # Combine halves
        symmetrical = trimesh.util.concatenate([half_mesh, mirrored_half])

        # Move back to original position
        symmetrical.apply_translation(center)

        logger.info(f"Symmetrization complete: {len(symmetrical.vertices)} vertices")
        return symmetrical

    def mirror_custom_plane(
        self,
        plane_origin: np.ndarray,
        plane_normal: np.ndarray,
        merge: bool = False
    ) -> trimesh.Trimesh:
        """
        Mirror mesh across a custom plane.

        Args:
            plane_origin: Point on the mirror plane
            plane_normal: Normal vector of the mirror plane
            merge: Merge original and mirrored meshes

        Returns:
            Mirrored mesh
        """
        logger.info("Mirroring across custom plane")

        # Normalize plane normal
        plane_normal = plane_normal / np.linalg.norm(plane_normal)

        # Create reflection matrix for arbitrary plane
        reflection_matrix = self._get_plane_reflection_matrix(plane_origin, plane_normal)

        # Apply reflection
        mirrored = self.mesh.copy()
        mirrored.apply_transform(reflection_matrix)
        mirrored.invert()

        if merge:
            combined = trimesh.util.concatenate([self.mesh, mirrored])
            return combined
        else:
            return mirrored

    def _get_reflection_matrix(self, axis: str) -> np.ndarray:
        """
        Get 4x4 reflection matrix for axis.

        Args:
            axis: Axis to reflect across ('x', 'y', or 'z')

        Returns:
            4x4 transformation matrix
        """
        matrix = np.eye(4)

        if axis.lower() == 'x':
            matrix[0, 0] = -1
        elif axis.lower() == 'y':
            matrix[1, 1] = -1
        elif axis.lower() == 'z':
            matrix[2, 2] = -1
        else:
            raise ValueError(f"Invalid axis: {axis}. Use 'x', 'y', or 'z'")

        return matrix

    def _get_plane_reflection_matrix(
        self,
        plane_origin: np.ndarray,
        plane_normal: np.ndarray
    ) -> np.ndarray:
        """
        Create reflection matrix for arbitrary plane.

        Args:
            plane_origin: Point on plane
            plane_normal: Plane normal (normalized)

        Returns:
            4x4 transformation matrix
        """
        # Householder reflection matrix
        n = plane_normal.reshape(3, 1)
        reflection_3x3 = np.eye(3) - 2 * n @ n.T

        # Create 4x4 matrix
        matrix = np.eye(4)
        matrix[:3, :3] = reflection_3x3

        # Add translation component to reflect through plane at origin
        matrix[:3, 3] = 2 * (plane_origin @ plane_normal) * plane_normal - 2 * plane_origin

        return matrix

    def _slice_mesh(
        self,
        mesh: trimesh.Trimesh,
        plane_origin: np.ndarray,
        plane_normal: np.ndarray
    ) -> trimesh.Trimesh:
        """
        Slice mesh, keeping only one side of the plane.

        Args:
            mesh: Mesh to slice
            plane_origin: Point on slicing plane
            plane_normal: Normal of slicing plane

        Returns:
            Sliced mesh
        """
        try:
            # Use trimesh's slice_plane method
            sliced = mesh.slice_plane(
                plane_origin=plane_origin,
                plane_normal=plane_normal,
                cap=True  # Cap the slice to keep it watertight
            )
            return sliced
        except Exception as e:
            logger.warning(f"Slicing failed: {e}, returning original mesh")
            return mesh


def mirror_mesh(
    mesh: trimesh.Trimesh,
    axis: str = 'x',
    merge: bool = False
) -> Dict:
    """
    High-level function to mirror a mesh.

    Args:
        mesh: Input mesh
        axis: Axis to mirror across ('x', 'y', 'z')
        merge: Merge original and mirrored halves

    Returns:
        Dict containing:
            - mesh: Mirrored mesh
            - stats: Statistics about the operation
    """
    mirror = MeshMirror(mesh)
    mirrored_mesh = mirror.mirror(axis=axis, merge=merge)

    stats = {
        'original_vertices': len(mesh.vertices),
        'original_faces': len(mesh.faces),
        'mirrored_vertices': len(mirrored_mesh.vertices),
        'mirrored_faces': len(mirrored_mesh.faces),
        'axis': axis,
        'merged': merge
    }

    return {
        'mesh': mirrored_mesh,
        'stats': stats
    }


def symmetrize_mesh(
    mesh: trimesh.Trimesh,
    axis: str = 'x',
    keep_side: str = 'positive'
) -> Dict:
    """
    Make mesh symmetrical along specified axis.

    Args:
        mesh: Input mesh
        axis: Axis of symmetry
        keep_side: Which side to keep ('positive' or 'negative')

    Returns:
        Dict containing:
            - mesh: Symmetrized mesh
            - stats: Statistics
    """
    mirror = MeshMirror(mesh)
    symmetrical_mesh = mirror.symmetrize(axis=axis, keep_side=keep_side)

    stats = {
        'original_vertices': len(mesh.vertices),
        'original_faces': len(mesh.faces),
        'symmetrical_vertices': len(symmetrical_mesh.vertices),
        'symmetrical_faces': len(symmetrical_mesh.faces),
        'axis': axis,
        'kept_side': keep_side
    }

    return {
        'mesh': symmetrical_mesh,
        'stats': stats
    }


def auto_symmetrize(mesh: trimesh.Trimesh) -> Tuple[trimesh.Trimesh, str]:
    """
    Automatically detect best symmetry axis and symmetrize.

    Args:
        mesh: Input mesh

    Returns:
        Tuple of (symmetrized mesh, axis used)
    """
    # Analyze mesh to find best symmetry axis
    # This is a simplified heuristic - check bounding box
    bbox_size = mesh.bounds[1] - mesh.bounds[0]

    # Use longest axis as symmetry axis
    axis_idx = np.argmax(bbox_size)
    axis = ['x', 'y', 'z'][axis_idx]

    logger.info(f"Auto-detected {axis.upper()}-axis for symmetry")

    mirror = MeshMirror(mesh)
    symmetrical = mirror.symmetrize(axis=axis, keep_side='positive')

    return symmetrical, axis
