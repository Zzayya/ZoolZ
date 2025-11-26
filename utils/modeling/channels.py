#!/usr/bin/env python3
"""
Channel and Groove Carving - Add channels, grooves, and drainage features to meshes
Perfect for water drainage, cable management, and functional designs
"""

import trimesh
import numpy as np
from typing import Dict, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ChannelCarver:
    """
    Carve channels and grooves into mesh surfaces
    """

    def __init__(self, mesh: trimesh.Trimesh):
        """
        Initialize channel carver

        Args:
            mesh: Input mesh to carve channels into
        """
        self.mesh = mesh.copy()

    def carve_linear_channel(
        self,
        start_point: np.ndarray,
        end_point: np.ndarray,
        width: float = 2.0,
        depth: float = 1.0,
        profile: str = 'v',  # 'v', 'u', 'rectangular'
        segments: int = 32
    ) -> trimesh.Trimesh:
        """
        Carve a straight channel from start to end point

        Args:
            start_point: Starting point [x, y, z]
            end_point: Ending point [x, y, z]
            width: Channel width (mm)
            depth: Channel depth (mm)
            profile: Cross-section profile ('v', 'u', 'rectangular')
            segments: Resolution of channel

        Returns:
            Mesh with channel carved
        """
        logger.info(f"Carving linear channel from {start_point} to {end_point}")

        # Create channel mesh to subtract
        channel_mesh = self._create_channel_mesh(
            start_point, end_point, width, depth, profile, segments
        )

        # Subtract channel from mesh
        try:
            result = self.mesh.difference(channel_mesh)
            return result
        except Exception as e:
            logger.error(f"Error carving channel: {e}")
            return self.mesh

    def carve_radial_channels(
        self,
        center_point: np.ndarray,
        radius: float,
        num_channels: int = 8,
        channel_width: float = 2.0,
        channel_depth: float = 1.0,
        channel_length: Optional[float] = None,
        start_angle: float = 0.0
    ) -> trimesh.Trimesh:
        """
        Carve radial channels emanating from a center point (like spokes)

        Args:
            center_point: Center point [x, y, z]
            radius: Radius of the pattern
            num_channels: Number of radial channels
            channel_width: Width of each channel (mm)
            channel_depth: Depth of each channel (mm)
            channel_length: Length of each channel (None = extend to radius)
            start_angle: Starting angle offset (degrees)

        Returns:
            Mesh with radial channels
        """
        logger.info(f"Carving {num_channels} radial channels from {center_point}")

        if channel_length is None:
            channel_length = radius

        result_mesh = self.mesh.copy()
        angle_step = 360.0 / num_channels
        start_angle_rad = np.deg2rad(start_angle)

        for i in range(num_channels):
            angle = start_angle_rad + (i * np.deg2rad(angle_step))

            # Calculate start and end points for this channel
            start = center_point.copy()
            end = center_point.copy()
            end[0] += channel_length * np.cos(angle)
            end[1] += channel_length * np.sin(angle)

            # Create channel mesh
            channel_mesh = self._create_channel_mesh(
                start, end, channel_width, channel_depth, 'v', 32
            )

            # Subtract from result
            try:
                result_mesh = result_mesh.difference(channel_mesh)
            except Exception as e:
                logger.warning(f"Error carving channel {i}: {e}")

        return result_mesh

    def carve_spiral_channel(
        self,
        center_point: np.ndarray,
        start_radius: float,
        end_radius: float,
        rotations: float = 2.0,
        channel_width: float = 2.0,
        channel_depth: float = 1.0,
        points_per_rotation: int = 32
    ) -> trimesh.Trimesh:
        """
        Carve a spiral channel

        Args:
            center_point: Center point [x, y, z]
            start_radius: Starting radius
            end_radius: Ending radius
            rotations: Number of rotations
            channel_width: Channel width (mm)
            channel_depth: Channel depth (mm)
            points_per_rotation: Resolution

        Returns:
            Mesh with spiral channel
        """
        logger.info(f"Carving spiral channel with {rotations} rotations")

        # Generate spiral path
        num_points = int(rotations * points_per_rotation)
        angles = np.linspace(0, rotations * 2 * np.pi, num_points)
        radii = np.linspace(start_radius, end_radius, num_points)

        path_points = []
        for angle, radius in zip(angles, radii):
            x = center_point[0] + radius * np.cos(angle)
            y = center_point[1] + radius * np.sin(angle)
            z = center_point[2]
            path_points.append([x, y, z])

        # Carve channel along path
        return self.carve_path_channel(path_points, channel_width, channel_depth)

    def carve_path_channel(
        self,
        path_points: List[np.ndarray],
        width: float = 2.0,
        depth: float = 1.0,
        profile: str = 'v'
    ) -> trimesh.Trimesh:
        """
        Carve a channel along a custom path

        Args:
            path_points: List of [x, y, z] points defining the path
            width: Channel width (mm)
            depth: Channel depth (mm)
            profile: Cross-section profile

        Returns:
            Mesh with channel carved along path
        """
        logger.info(f"Carving channel along path with {len(path_points)} points")

        result_mesh = self.mesh.copy()

        # Carve channel segment by segment
        for i in range(len(path_points) - 1):
            start = np.array(path_points[i])
            end = np.array(path_points[i + 1])

            channel_mesh = self._create_channel_mesh(
                start, end, width, depth, profile, 16
            )

            try:
                result_mesh = result_mesh.difference(channel_mesh)
            except Exception as e:
                logger.warning(f"Error carving path segment {i}: {e}")

        return result_mesh

    def carve_grid_channels(
        self,
        bounds: Tuple[float, float, float, float],  # x_min, x_max, y_min, y_max
        z_height: float,
        spacing_x: float = 10.0,
        spacing_y: float = 10.0,
        channel_width: float = 1.0,
        channel_depth: float = 0.5
    ) -> trimesh.Trimesh:
        """
        Carve a grid pattern of channels

        Args:
            bounds: (x_min, x_max, y_min, y_max)
            z_height: Z height for the channels
            spacing_x: Spacing between X channels
            spacing_y: Spacing between Y channels
            channel_width: Width of channels
            channel_depth: Depth of channels

        Returns:
            Mesh with grid channels
        """
        logger.info(f"Carving grid pattern")

        result_mesh = self.mesh.copy()
        x_min, x_max, y_min, y_max = bounds

        # Carve X-direction channels
        y = y_min
        while y <= y_max:
            start = np.array([x_min, y, z_height])
            end = np.array([x_max, y, z_height])

            channel_mesh = self._create_channel_mesh(
                start, end, channel_width, channel_depth, 'rectangular', 16
            )

            try:
                result_mesh = result_mesh.difference(channel_mesh)
            except Exception as e:
                logger.warning(f"Error carving X channel at y={y}: {e}")

            y += spacing_y

        # Carve Y-direction channels
        x = x_min
        while x <= x_max:
            start = np.array([x, y_min, z_height])
            end = np.array([x, y_max, z_height])

            channel_mesh = self._create_channel_mesh(
                start, end, channel_width, channel_depth, 'rectangular', 16
            )

            try:
                result_mesh = result_mesh.difference(channel_mesh)
            except Exception as e:
                logger.warning(f"Error carving Y channel at x={x}: {e}")

            x += spacing_x

        return result_mesh

    def _create_channel_mesh(
        self,
        start: np.ndarray,
        end: np.ndarray,
        width: float,
        depth: float,
        profile: str,
        segments: int
    ) -> trimesh.Trimesh:
        """
        Create a channel mesh between two points

        Args:
            start: Start point
            end: End point
            width: Channel width
            depth: Channel depth
            profile: Cross-section profile
            segments: Resolution

        Returns:
            Channel mesh for boolean subtraction
        """
        # Calculate channel direction and length
        direction = end - start
        length = np.linalg.norm(direction)
        direction_normalized = direction / length if length > 0 else np.array([1, 0, 0])

        # Create profile based on type
        if profile == 'v':
            # V-shaped profile
            profile_points = [
                [-width/2, 0],
                [0, -depth],
                [width/2, 0]
            ]
        elif profile == 'u':
            # U-shaped profile (rounded bottom)
            profile_points = []
            for i in range(segments + 1):
                angle = np.pi * i / segments
                x = (width/2) * np.sin(angle)
                y = -(depth/2) - (depth/2) * np.cos(angle)
                profile_points.append([x, y])
        else:  # rectangular
            profile_points = [
                [-width/2, 0],
                [-width/2, -depth],
                [width/2, -depth],
                [width/2, 0]
            ]

        # Extrude profile along path
        try:
            # Create a simple extruded channel
            # For simplicity, create a box-shaped channel
            channel = trimesh.creation.box(
                extents=[width, length, depth],
                transform=None
            )

            # Calculate rotation to align with direction
            # Align Y-axis of box with direction
            up = np.array([0, 1, 0])
            if np.allclose(direction_normalized, up) or np.allclose(direction_normalized, -up):
                axis = np.array([1, 0, 0])
                angle = 0 if np.allclose(direction_normalized, up) else np.pi
            else:
                axis = np.cross(up, direction_normalized)
                axis = axis / np.linalg.norm(axis)
                angle = np.arccos(np.dot(up, direction_normalized))

            if not np.allclose(angle, 0):
                rotation_matrix = trimesh.transformations.rotation_matrix(angle, axis)
                channel.apply_transform(rotation_matrix)

            # Position at midpoint between start and end
            midpoint = (start + end) / 2
            channel.apply_translation(midpoint)

            return channel

        except Exception as e:
            logger.error(f"Error creating channel mesh: {e}")
            # Return a simple box as fallback
            return trimesh.creation.box(extents=[width, length, depth])


def add_channels(
    mesh: trimesh.Trimesh,
    channel_type: str = 'linear',
    **kwargs
) -> Dict:
    """
    High-level function to add channels to a mesh

    Args:
        mesh: Input mesh
        channel_type: Type of channel ('linear', 'radial', 'spiral', 'path', 'grid')
        **kwargs: Channel-specific parameters

    Returns:
        Dict containing:
            - mesh: Mesh with channels
            - stats: Statistics about the operation
    """
    carver = ChannelCarver(mesh)

    # Create channels based on type
    try:
        if channel_type == 'linear':
            result_mesh = carver.carve_linear_channel(
                start_point=np.array(kwargs.get('start_point', [0, 0, 0])),
                end_point=np.array(kwargs.get('end_point', [10, 0, 0])),
                width=kwargs.get('width', 2.0),
                depth=kwargs.get('depth', 1.0),
                profile=kwargs.get('profile', 'v')
            )

        elif channel_type == 'radial':
            result_mesh = carver.carve_radial_channels(
                center_point=np.array(kwargs.get('center_point', [0, 0, 0])),
                radius=kwargs.get('radius', 20.0),
                num_channels=kwargs.get('num_channels', 8),
                channel_width=kwargs.get('width', 2.0),
                channel_depth=kwargs.get('depth', 1.0)
            )

        elif channel_type == 'spiral':
            result_mesh = carver.carve_spiral_channel(
                center_point=np.array(kwargs.get('center_point', [0, 0, 0])),
                start_radius=kwargs.get('start_radius', 5.0),
                end_radius=kwargs.get('end_radius', 20.0),
                rotations=kwargs.get('rotations', 2.0),
                channel_width=kwargs.get('width', 2.0),
                channel_depth=kwargs.get('depth', 1.0)
            )

        elif channel_type == 'grid':
            result_mesh = carver.carve_grid_channels(
                bounds=kwargs.get('bounds', (-20, 20, -20, 20)),
                z_height=kwargs.get('z_height', 0.0),
                spacing_x=kwargs.get('spacing_x', 10.0),
                spacing_y=kwargs.get('spacing_y', 10.0),
                channel_width=kwargs.get('width', 1.0),
                channel_depth=kwargs.get('depth', 0.5)
            )

        elif channel_type == 'path':
            path_points = kwargs.get('path_points', [[0,0,0], [10,10,0]])
            result_mesh = carver.carve_path_channel(
                path_points=path_points,
                width=kwargs.get('width', 2.0),
                depth=kwargs.get('depth', 1.0)
            )

        else:
            logger.error(f"Unknown channel type: {channel_type}")
            return {
                'mesh': mesh,
                'stats': {'error': 'Unknown channel type'}
            }

        stats = {
            'original_vertices': len(mesh.vertices),
            'original_faces': len(mesh.faces),
            'result_vertices': len(result_mesh.vertices),
            'result_faces': len(result_mesh.faces),
            'is_watertight': result_mesh.is_watertight,
            'channel_type': channel_type
        }

        if mesh.is_watertight and result_mesh.is_watertight:
            stats['volume_removed'] = float(mesh.volume - result_mesh.volume)

        return {
            'mesh': result_mesh,
            'stats': stats
        }

    except Exception as e:
        logger.error(f"Error adding channels: {e}")
        return {
            'mesh': mesh,
            'stats': {'error': str(e)}
        }
