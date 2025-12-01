#!/usr/bin/env python3
"""
Mesh Cutting - Cut meshes with planes and keep specific parts
Advanced cutting with plane positioning and part selection
"""

import trimesh
import numpy as np
from typing import Dict, Optional, Tuple, List, Union
import logging

logger = logging.getLogger(__name__)


class MeshCutter:
    """
    Advanced mesh cutting with plane specification
    """

    def __init__(self, mesh: trimesh.Trimesh):
        """
        Initialize mesh cutter

        Args:
            mesh: Input mesh to cut
        """
        self.mesh = mesh.copy()
        self.bounds = mesh.bounds.copy()
        self.center = mesh.bounds.mean(axis=0)
        self.extents = mesh.extents.copy()

    def cut_plane(
        self,
        plane_axis: str = 'z',
        plane_position: float = 0.0,
        position_mode: str = 'absolute',  # 'absolute', 'percentage', 'center'
        keep_part: str = 'top',  # 'top', 'bottom', 'both'
        cap_cut: bool = True
    ) -> Union[trimesh.Trimesh, List[trimesh.Trimesh]]:
        """
        Cut mesh with a plane

        Args:
            plane_axis: Axis perpendicular to cutting plane ('x', 'y', 'z')
            plane_position: Position of plane along axis
            position_mode: How to interpret plane_position
                - 'absolute': Use as absolute coordinate
                - 'percentage': Position as percentage of model height (0-100)
                - 'center': Offset from model center
            keep_part: Which part to keep ('top', 'bottom', 'both')
            cap_cut: Add caps to close the cut surfaces

        Returns:
            Cut mesh or list of meshes if keep_part='both'
        """
        logger.info(f"Cutting mesh along {plane_axis.upper()}-axis at position {plane_position} ({position_mode})")

        # Determine axis index
        axis_idx = {'x': 0, 'y': 1, 'z': 2}[plane_axis.lower()]

        # Calculate absolute plane position based on mode
        if position_mode == 'percentage':
            # Position as percentage of model extent
            min_val = self.bounds[0][axis_idx]
            max_val = self.bounds[1][axis_idx]
            absolute_position = min_val + (max_val - min_val) * (plane_position / 100.0)
        elif position_mode == 'center':
            # Position as offset from center
            absolute_position = self.center[axis_idx] + plane_position
        else:  # absolute
            absolute_position = plane_position

        # Create plane normal and origin
        plane_normal = np.zeros(3)
        plane_normal[axis_idx] = 1.0

        plane_origin = np.zeros(3)
        plane_origin[axis_idx] = absolute_position

        logger.info(f"Plane origin: {plane_origin}, normal: {plane_normal}")

        # Slice the mesh
        result_meshes = []

        if keep_part in ['top', 'both']:
            # Keep the part in the positive direction of the normal
            try:
                top_part = self.mesh.slice_plane(plane_origin, plane_normal, cap=cap_cut)
                if top_part is not None:
                    result_meshes.append(('top', top_part))
                    logger.info(f"Top part: {len(top_part.vertices)} vertices")
            except Exception as e:
                logger.error(f"Error creating top part: {e}")

        if keep_part in ['bottom', 'both']:
            # Keep the part in the negative direction of the normal
            try:
                bottom_part = self.mesh.slice_plane(plane_origin, -plane_normal, cap=cap_cut)
                if bottom_part is not None:
                    result_meshes.append(('bottom', bottom_part))
                    logger.info(f"Bottom part: {len(bottom_part.vertices)} vertices")
            except Exception as e:
                logger.error(f"Error creating bottom part: {e}")

        if len(result_meshes) == 0:
            logger.error("No valid mesh parts created")
            return self.mesh

        if keep_part == 'both':
            return result_meshes
        else:
            return result_meshes[0][1]

    def cut_at_height(
        self,
        height_mm: float,
        from_bottom: bool = True,
        keep_part: str = 'bottom'
    ) -> trimesh.Trimesh:
        """
        Cut mesh at a specific height

        Args:
            height_mm: Height in mm to cut at
            from_bottom: Measure from bottom (True) or top (False)
            keep_part: Which part to keep ('top' or 'bottom')

        Returns:
            Cut mesh
        """
        min_z = self.bounds[0][2]  # Bottom Z
        max_z = self.bounds[1][2]  # Top Z

        if from_bottom:
            cut_position = min_z + height_mm
        else:
            cut_position = max_z - height_mm

        return self.cut_plane(
            plane_axis='z',
            plane_position=cut_position,
            position_mode='absolute',
            keep_part=keep_part,
            cap_cut=True
        )

    def cut_remove_top(self, amount_mm: float) -> trimesh.Trimesh:
        """
        Remove the top portion of the model

        Args:
            amount_mm: How much to remove from the top (mm)

        Returns:
            Mesh with top removed
        """
        return self.cut_at_height(amount_mm, from_bottom=False, keep_part='bottom')

    def cut_remove_bottom(self, amount_mm: float) -> trimesh.Trimesh:
        """
        Remove the bottom portion of the model

        Args:
            amount_mm: How much to remove from the bottom (mm)

        Returns:
            Mesh with bottom removed
        """
        return self.cut_at_height(amount_mm, from_bottom=True, keep_part='top')

    def split_in_half(
        self,
        axis: str = 'z',
        offset: float = 0.0
    ) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
        """
        Split mesh in half along an axis

        Args:
            axis: Axis to split along ('x', 'y', 'z')
            offset: Offset from center point (mm)

        Returns:
            Tuple of (top/right part, bottom/left part)
        """
        axis_idx = {'x': 0, 'y': 1, 'z': 2}[axis.lower()]
        split_position = self.center[axis_idx] + offset

        results = self.cut_plane(
            plane_axis=axis,
            plane_position=split_position,
            position_mode='absolute',
            keep_part='both',
            cap_cut=True
        )

        if isinstance(results, list) and len(results) == 2:
            return results[0][1], results[1][1]
        else:
            logger.error("Split failed to create two parts")
            return self.mesh, self.mesh.copy()


def cut_mesh(
    mesh: trimesh.Trimesh,
    cut_mode: str = 'plane',
    **kwargs
) -> Dict:
    """
    High-level function to cut a mesh with various options

    Args:
        mesh: Input mesh
        cut_mode: Cut mode ('plane', 'height', 'remove_top', 'remove_bottom', 'split')
        **kwargs: Mode-specific parameters

    Returns:
        Dict containing:
            - mesh: Cut mesh (or list of meshes for split)
            - stats: Statistics about the operation
    """
    cutter = MeshCutter(mesh)

    # Apply cutting based on mode
    if cut_mode == 'plane':
        result_mesh = cutter.cut_plane(
            plane_axis=kwargs.get('plane_axis', 'z'),
            plane_position=kwargs.get('plane_position', 0.0),
            position_mode=kwargs.get('position_mode', 'percentage'),
            keep_part=kwargs.get('keep_part', 'bottom'),
            cap_cut=kwargs.get('cap_cut', True)
        )

    elif cut_mode == 'height':
        result_mesh = cutter.cut_at_height(
            height_mm=kwargs.get('height_mm', 10.0),
            from_bottom=kwargs.get('from_bottom', True),
            keep_part=kwargs.get('keep_part', 'bottom')
        )

    elif cut_mode == 'remove_top':
        result_mesh = cutter.cut_remove_top(
            amount_mm=kwargs.get('amount_mm', 5.0)
        )

    elif cut_mode == 'remove_bottom':
        result_mesh = cutter.cut_remove_bottom(
            amount_mm=kwargs.get('amount_mm', 5.0)
        )

    elif cut_mode == 'split':
        top_mesh, bottom_mesh = cutter.split_in_half(
            axis=kwargs.get('axis', 'z'),
            offset=kwargs.get('offset', 0.0)
        )
        result_mesh = [('top', top_mesh), ('bottom', bottom_mesh)]

    else:
        logger.error(f"Unknown cut mode: {cut_mode}")
        return {
            'mesh': mesh,
            'stats': {'error': 'Unknown cut mode'}
        }

    # Calculate statistics
    if isinstance(result_mesh, list):
        # Multiple parts
        stats = {
            'parts_created': len(result_mesh),
            'parts': []
        }
        for name, part_mesh in result_mesh:
            part_stats = {
                'name': name,
                'vertices': len(part_mesh.vertices),
                'faces': len(part_mesh.faces),
                'is_watertight': part_mesh.is_watertight,
                'dimensions': {
                    'width': float(part_mesh.extents[0]),
                    'height': float(part_mesh.extents[1]),
                    'depth': float(part_mesh.extents[2])
                }
            }
            if part_mesh.is_watertight:
                part_stats['volume'] = float(part_mesh.volume)
            stats['parts'].append(part_stats)
    else:
        # Single part
        stats = {
            'original_vertices': len(mesh.vertices),
            'original_faces': len(mesh.faces),
            'result_vertices': len(result_mesh.vertices),
            'result_faces': len(result_mesh.faces),
            'is_watertight': result_mesh.is_watertight,
            'dimensions': {
                'width': float(result_mesh.extents[0]),
                'height': float(result_mesh.extents[1]),
                'depth': float(result_mesh.extents[2])
            }
        }
        if mesh.is_watertight and result_mesh.is_watertight:
            stats['original_volume'] = float(mesh.volume)
            stats['result_volume'] = float(result_mesh.volume)
            stats['volume_removed'] = float(mesh.volume - result_mesh.volume)

    return {
        'mesh': result_mesh,
        'stats': stats
    }
