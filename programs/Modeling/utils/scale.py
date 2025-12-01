#!/usr/bin/env python3
"""
Mesh Scaling - Resize meshes with various options
Supports uniform and non-uniform scaling, maintaining proportions
"""

import trimesh
import numpy as np
from typing import Dict, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class MeshScaler:
    """
    Advanced mesh scaling with dimension targeting and proportions
    """

    def __init__(self, mesh: trimesh.Trimesh):
        """
        Initialize mesh scaler

        Args:
            mesh: Input mesh to scale
        """
        self.mesh = mesh.copy()
        self.original_bounds = mesh.bounds.copy()
        self.original_extents = mesh.extents.copy()

    def scale_uniform(self, scale_factor: float) -> trimesh.Trimesh:
        """
        Scale mesh uniformly by a factor

        Args:
            scale_factor: Scaling factor (2.0 = double size, 0.5 = half size)

        Returns:
            Scaled mesh
        """
        logger.info(f"Scaling mesh uniformly by factor {scale_factor}")

        scaled = self.mesh.copy()
        scaled.apply_scale(scale_factor)

        return scaled

    def scale_to_dimensions(
        self,
        target_width: Optional[float] = None,
        target_height: Optional[float] = None,
        target_depth: Optional[float] = None,
        maintain_aspect: bool = True
    ) -> trimesh.Trimesh:
        """
        Scale mesh to specific dimensions (in mm)

        Args:
            target_width: Desired width (X dimension) in mm
            target_height: Desired height (Y dimension) in mm
            target_depth: Desired depth (Z dimension) in mm
            maintain_aspect: Keep aspect ratio when only one dimension is specified

        Returns:
            Scaled mesh
        """
        logger.info(f"Scaling mesh to dimensions: W={target_width}, H={target_height}, D={target_depth}")

        current_extents = self.mesh.extents  # [X, Y, Z]
        scale_factors = np.ones(3)

        if target_width is not None:
            scale_factors[0] = target_width / current_extents[0]

        if target_height is not None:
            scale_factors[1] = target_height / current_extents[1]

        if target_depth is not None:
            scale_factors[2] = target_depth / current_extents[2]

        # If maintaining aspect ratio and only one dimension specified
        if maintain_aspect:
            # Find which dimensions were specified
            specified = []
            if target_width is not None:
                specified.append(scale_factors[0])
            if target_height is not None:
                specified.append(scale_factors[1])
            if target_depth is not None:
                specified.append(scale_factors[2])

            if len(specified) > 0:
                # Use the average of specified scale factors for all dimensions
                uniform_scale = np.mean(specified)
                scale_factors = np.array([uniform_scale, uniform_scale, uniform_scale])

        scaled = self.mesh.copy()
        scaled.apply_scale(scale_factors)

        logger.info(f"Applied scale factors: X={scale_factors[0]:.3f}, Y={scale_factors[1]:.3f}, Z={scale_factors[2]:.3f}")

        return scaled

    def scale_non_uniform(
        self,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        scale_z: float = 1.0
    ) -> trimesh.Trimesh:
        """
        Scale mesh with different factors for each axis

        Args:
            scale_x: X-axis scale factor
            scale_y: Y-axis scale factor
            scale_z: Z-axis scale factor

        Returns:
            Scaled mesh
        """
        logger.info(f"Scaling mesh non-uniformly: X={scale_x}, Y={scale_y}, Z={scale_z}")

        scale_factors = np.array([scale_x, scale_y, scale_z])
        scaled = self.mesh.copy()
        scaled.apply_scale(scale_factors)

        return scaled

    def scale_to_fit(
        self,
        max_dimension: float,
        maintain_aspect: bool = True
    ) -> trimesh.Trimesh:
        """
        Scale mesh to fit within a maximum dimension

        Args:
            max_dimension: Maximum allowed dimension in any axis (mm)
            maintain_aspect: Keep aspect ratio

        Returns:
            Scaled mesh
        """
        logger.info(f"Scaling mesh to fit within {max_dimension}mm")

        current_max = np.max(self.mesh.extents)

        if current_max <= max_dimension:
            logger.info("Mesh already fits within max dimension")
            return self.mesh.copy()

        scale_factor = max_dimension / current_max

        return self.scale_uniform(scale_factor)

    def scale_to_volume(
        self,
        target_volume: float
    ) -> trimesh.Trimesh:
        """
        Scale mesh to achieve a target volume (for watertight meshes only)

        Args:
            target_volume: Desired volume in mm³

        Returns:
            Scaled mesh
        """
        if not self.mesh.is_watertight:
            logger.warning("Cannot scale to volume - mesh is not watertight")
            return self.mesh.copy()

        current_volume = self.mesh.volume

        # Volume scales with the cube of linear dimensions
        scale_factor = (target_volume / current_volume) ** (1/3)

        logger.info(f"Scaling mesh to volume {target_volume}mm³ (factor: {scale_factor:.3f})")

        return self.scale_uniform(scale_factor)


def scale_mesh(
    mesh: trimesh.Trimesh,
    scale_mode: str = 'uniform',
    **kwargs
) -> Dict:
    """
    High-level function to scale a mesh with various options

    Args:
        mesh: Input mesh
        scale_mode: Scaling mode ('uniform', 'dimensions', 'non_uniform', 'fit', 'volume')
        **kwargs: Mode-specific parameters

    Returns:
        Dict containing:
            - mesh: Scaled mesh
            - stats: Statistics about the scaling operation
    """
    scaler = MeshScaler(mesh)

    # Apply scaling based on mode
    if scale_mode == 'uniform':
        scale_factor = kwargs.get('scale_factor', 1.0)
        scaled_mesh = scaler.scale_uniform(scale_factor)

    elif scale_mode == 'dimensions':
        scaled_mesh = scaler.scale_to_dimensions(
            target_width=kwargs.get('target_width'),
            target_height=kwargs.get('target_height'),
            target_depth=kwargs.get('target_depth'),
            maintain_aspect=kwargs.get('maintain_aspect', True)
        )

    elif scale_mode == 'non_uniform':
        scaled_mesh = scaler.scale_non_uniform(
            scale_x=kwargs.get('scale_x', 1.0),
            scale_y=kwargs.get('scale_y', 1.0),
            scale_z=kwargs.get('scale_z', 1.0)
        )

    elif scale_mode == 'fit':
        scaled_mesh = scaler.scale_to_fit(
            max_dimension=kwargs.get('max_dimension', 100.0),
            maintain_aspect=kwargs.get('maintain_aspect', True)
        )

    elif scale_mode == 'volume':
        scaled_mesh = scaler.scale_to_volume(
            target_volume=kwargs.get('target_volume', 1000.0)
        )

    else:
        logger.error(f"Unknown scale mode: {scale_mode}")
        return {
            'mesh': mesh,
            'stats': {'error': 'Unknown scale mode'}
        }

    # Calculate statistics
    original_extents = mesh.extents
    new_extents = scaled_mesh.extents

    stats = {
        'original_dimensions': {
            'width': float(original_extents[0]),
            'height': float(original_extents[1]),
            'depth': float(original_extents[2])
        },
        'new_dimensions': {
            'width': float(new_extents[0]),
            'height': float(new_extents[1]),
            'depth': float(new_extents[2])
        },
        'scale_factors': {
            'x': float(new_extents[0] / original_extents[0]),
            'y': float(new_extents[1] / original_extents[1]),
            'z': float(new_extents[2] / original_extents[2])
        },
        'vertices': len(scaled_mesh.vertices),
        'faces': len(scaled_mesh.faces),
        'is_watertight': scaled_mesh.is_watertight
    }

    if mesh.is_watertight and scaled_mesh.is_watertight:
        stats['original_volume'] = float(mesh.volume)
        stats['new_volume'] = float(scaled_mesh.volume)
        stats['volume_ratio'] = float(scaled_mesh.volume / mesh.volume)

    return {
        'mesh': scaled_mesh,
        'stats': stats
    }
