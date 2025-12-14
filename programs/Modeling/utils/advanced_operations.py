#!/usr/bin/env python3
"""
Advanced Operations - Boolean operations, negatives, symmetry, creases, ridges
Essential tools for complex 3D modeling and design
"""

import trimesh
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AdvancedOperations:
    """Advanced 3D modeling operations"""

    @staticmethod
    def boolean_union(mesh1: trimesh.Trimesh, mesh2: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Combine two meshes into one (OR operation)

        Args:
            mesh1: First mesh
            mesh2: Second mesh

        Returns:
            Combined mesh
        """
        try:
            result = mesh1.union(mesh2)
            logger.info(f"Boolean union: {len(result.vertices)} vertices")
            return result
        except Exception as e:
            logger.warning(f"Boolean union failed, using concatenation: {e}")
            return trimesh.util.concatenate([mesh1, mesh2])

    @staticmethod
    def boolean_difference(mesh1: trimesh.Trimesh, mesh2: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Subtract mesh2 from mesh1

        Args:
            mesh1: Base mesh
            mesh2: Mesh to subtract

        Returns:
            Result mesh
        """
        try:
            result = mesh1.difference(mesh2)
            logger.info(f"Boolean difference: {len(result.vertices)} vertices")
            return result
        except Exception as e:
            logger.error(f"Boolean difference failed: {e}")
            return mesh1

    @staticmethod
    def boolean_intersection(mesh1: trimesh.Trimesh, mesh2: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Keep only the overlapping volume (AND operation)

        Args:
            mesh1: First mesh
            mesh2: Second mesh

        Returns:
            Intersection mesh
        """
        try:
            result = mesh1.intersection(mesh2)
            logger.info(f"Boolean intersection: {len(result.vertices)} vertices")
            return result
        except Exception as e:
            logger.error(f"Boolean intersection failed: {e}")
            return mesh1

    @staticmethod
    def create_negative(mesh: trimesh.Trimesh, shell_thickness: float = 2.0) -> trimesh.Trimesh:
        """
        Create a negative/mold of the mesh (inverse cavity)

        Args:
            mesh: Input mesh
            shell_thickness: Thickness of negative shell walls

        Returns:
            Negative mesh
        """
        # Get bounding box
        bounds = mesh.bounds
        size = bounds[1] - bounds[0]

        # Create containing box
        box_size = size + shell_thickness * 4
        containing_box = trimesh.creation.box(extents=box_size)
        containing_box.apply_translation(mesh.centroid)

        # Create inner box (cavity)
        inner_size = size + shell_thickness * 0.5
        inner_box = trimesh.creation.box(extents=inner_size)
        inner_box.apply_translation(mesh.centroid)

        try:
            # Create shell
            shell = containing_box.difference(inner_box)

            # Subtract original mesh to create cavity
            negative = shell.difference(mesh)

            logger.info(f"Created negative: {len(negative.vertices)} vertices")
            return negative
        except Exception as e:
            logger.error(f"Create negative failed: {e}")
            return containing_box

    @staticmethod
    def mirror_mesh(
        mesh: trimesh.Trimesh,
        plane: str = 'xy',
        merge: bool = True
    ) -> trimesh.Trimesh:
        """
        Mirror mesh across a plane

        Args:
            mesh: Input mesh
            plane: Plane to mirror across ('xy', 'xz', 'yz')
            merge: If True, merge with original

        Returns:
            Mirrored mesh (or merged)
        """
        # Create mirror matrix
        if plane == 'xy':  # Mirror across Z
            mirror_matrix = np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, -1, 0],
                [0, 0, 0, 1]
            ])
        elif plane == 'xz':  # Mirror across Y
            mirror_matrix = np.array([
                [1, 0, 0, 0],
                [0, -1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
        else:  # 'yz' - Mirror across X
            mirror_matrix = np.array([
                [-1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])

        mirrored = mesh.copy()
        mirrored.apply_transform(mirror_matrix)

        if merge:
            result = trimesh.util.concatenate([mesh, mirrored])
            logger.info(f"Mirrored and merged mesh: {len(result.vertices)} vertices")
            return result
        else:
            logger.info(f"Mirrored mesh: {len(mirrored.vertices)} vertices")
            return mirrored

    @staticmethod
    def apply_symmetry(
        mesh: trimesh.Trimesh,
        axes: List[str] = ['x']
    ) -> trimesh.Trimesh:
        """
        Apply symmetry across multiple axes

        Args:
            mesh: Input mesh
            axes: List of axes to apply symmetry ('x', 'y', 'z')

        Returns:
            Symmetrical mesh
        """
        result = mesh.copy()

        for axis in axes:
            if axis == 'x':
                plane = 'yz'
            elif axis == 'y':
                plane = 'xz'
            else:  # 'z'
                plane = 'xy'

            result = AdvancedOperations.mirror_mesh(result, plane=plane, merge=True)

        logger.info(f"Applied {len(axes)}-axis symmetry: {len(result.vertices)} vertices")
        return result

    @staticmethod
    def add_crease(
        mesh: trimesh.Trimesh,
        start_point: np.ndarray,
        end_point: np.ndarray,
        crease_angle: float = 90.0,
        crease_width: float = 1.0
    ) -> trimesh.Trimesh:
        """
        Add a crease/fold line to the mesh

        Args:
            mesh: Input mesh
            start_point: Start of crease line
            end_point: End of crease line
            crease_angle: Angle of the crease in degrees
            crease_width: Width of crease effect

        Returns:
            Mesh with crease
        """
        start = np.array(start_point)
        end = np.array(end_point)

        # Create crease direction
        crease_dir = end - start
        crease_length = np.linalg.norm(crease_dir)
        crease_dir = crease_dir / crease_length

        # Find vertices along the crease line
        affected_vertices = []
        for i, vertex in enumerate(mesh.vertices):
            # Distance from vertex to line
            vec_to_point = vertex - start
            projection = np.dot(vec_to_point, crease_dir)

            if 0 <= projection <= crease_length:
                closest_point = start + projection * crease_dir
                distance = np.linalg.norm(vertex - closest_point)

                if distance <= crease_width:
                    affected_vertices.append(i)

        # Apply crease transformation
        angle_rad = np.deg2rad(crease_angle)

        # Get perpendicular to crease direction
        if abs(crease_dir[2]) < 0.9:
            perp = np.cross(crease_dir, [0, 0, 1])
        else:
            perp = np.cross(crease_dir, [0, 1, 0])
        perp = perp / np.linalg.norm(perp)

        # Create rotation matrix for crease
        rotation_matrix = trimesh.transformations.rotation_matrix(
            angle_rad,
            crease_dir,
            start
        )

        # Apply to affected vertices
        for idx in affected_vertices:
            vec_to_point = mesh.vertices[idx] - start
            projection = np.dot(vec_to_point, crease_dir)
            distance_from_line = np.linalg.norm(vec_to_point - projection * crease_dir)

            # Fade effect based on distance
            fade_factor = 1.0 - (distance_from_line / crease_width)
            fade_factor = max(0, min(1, fade_factor))

            # Apply rotation with fade
            if fade_factor > 0:
                point_4d = np.append(mesh.vertices[idx], 1)
                transformed = rotation_matrix @ point_4d
                mesh.vertices[idx] = mesh.vertices[idx] + (transformed[:3] - mesh.vertices[idx]) * fade_factor

        logger.info(f"Added crease affecting {len(affected_vertices)} vertices")
        return mesh

    @staticmethod
    def add_ridge(
        mesh: trimesh.Trimesh,
        start_point: np.ndarray,
        end_point: np.ndarray,
        ridge_height: float = 2.0,
        ridge_width: float = 3.0
    ) -> trimesh.Trimesh:
        """
        Add a raised ridge to the mesh surface

        Args:
            mesh: Input mesh
            start_point: Start of ridge
            end_point: End of ridge
            ridge_height: Height of ridge
            ridge_width: Width of ridge

        Returns:
            Mesh with ridge
        """
        start = np.array(start_point)
        end = np.array(end_point)

        # Create ridge direction
        ridge_dir = end - start
        ridge_length = np.linalg.norm(ridge_dir)
        ridge_dir = ridge_dir / ridge_length

        # Find vertices along the ridge line
        affected_vertices = []
        for i, vertex in enumerate(mesh.vertices):
            # Distance from vertex to line
            vec_to_point = vertex - start
            projection = np.dot(vec_to_point, ridge_dir)

            if 0 <= projection <= ridge_length:
                closest_point = start + projection * ridge_dir
                distance = np.linalg.norm(vertex - closest_point)

                if distance <= ridge_width / 2:
                    affected_vertices.append((i, distance))

        # Get surface normal direction (average)
        face_normals = mesh.face_normals
        avg_normal = np.mean(face_normals, axis=0)
        avg_normal = avg_normal / np.linalg.norm(avg_normal)

        # Displace vertices to create ridge
        for idx, distance in affected_vertices:
            # Parabolic height profile
            height_factor = 1.0 - (2 * distance / ridge_width) ** 2
            height_factor = max(0, height_factor)

            displacement = avg_normal * ridge_height * height_factor
            mesh.vertices[idx] += displacement

        logger.info(f"Added ridge affecting {len(affected_vertices)} vertices")
        return mesh

    @staticmethod
    def create_linking_connector(
        diameter: float = 10.0,
        length: float = 20.0,
        connector_type: str = 'socket'  # 'socket' or 'pin'
    ) -> trimesh.Trimesh:
        """
        Create interlocking connectors for joining parts

        Args:
            diameter: Diameter of connector
            length: Length of connector
            connector_type: Type ('socket' for female, 'pin' for male)

        Returns:
            Connector mesh
        """
        if connector_type == 'pin':
            # Male connector - tapered pin
            base = trimesh.creation.cylinder(
                radius=diameter / 2,
                height=length * 0.6,
                sections=32
            )
            base.apply_translation([0, 0, length * 0.3])

            tip = trimesh.creation.cone(
                radius=diameter / 2,
                height=length * 0.4,
                sections=32
            )
            tip.apply_translation([0, 0, length * 0.8])

            connector = trimesh.util.concatenate([base, tip])

        else:
            # Female connector - socket with retention groove
            outer = trimesh.creation.cylinder(
                radius=diameter / 2 + 2,
                height=length,
                sections=32
            )

            inner = trimesh.creation.cylinder(
                radius=diameter / 2 + 0.3,  # Clearance
                height=length + 2,
                sections=32
            )

            try:
                connector = outer.difference(inner)

                # Add retention groove
                groove = trimesh.creation.cylinder(
                    radius=diameter / 2 + 1,
                    height=length * 0.1,
                    sections=32
                )
                groove.apply_translation([0, 0, length * 0.7])

                connector = connector.difference(groove)

            except:
                connector = outer

        logger.info(f"Created {connector_type} connector: {len(connector.vertices)} vertices")
        return connector

    @staticmethod
    def create_hinge(
        width: float = 30.0,
        pin_diameter: float = 5.0,
        num_knuckles: int = 3,
        knuckle_length: float = 10.0
    ) -> Dict[str, trimesh.Trimesh]:
        """
        Create a working hinge with interlocking knuckles

        Args:
            width: Total width of hinge
            pin_diameter: Diameter of hinge pin
            num_knuckles: Number of knuckle segments
            knuckle_length: Length of each knuckle

        Returns:
            Dict with 'part1', 'part2', and 'pin' meshes
        """
        knuckles_part1 = []
        knuckles_part2 = []

        for i in range(num_knuckles):
            # Alternating pattern
            if i % 2 == 0:
                # Part 1 knuckle
                knuckle = trimesh.creation.cylinder(
                    radius=pin_diameter,
                    height=knuckle_length,
                    sections=32
                )
                knuckle.apply_translation([0, i * (knuckle_length + 1), 0])

                # Add mounting tab
                tab = trimesh.creation.box(extents=[pin_diameter * 2, knuckle_length, pin_diameter * 0.5])
                tab.apply_translation([pin_diameter, i * (knuckle_length + 1), 0])

                knuckle = trimesh.util.concatenate([knuckle, tab])
                knuckles_part1.append(knuckle)
            else:
                # Part 2 knuckle
                knuckle = trimesh.creation.cylinder(
                    radius=pin_diameter,
                    height=knuckle_length,
                    sections=32
                )
                knuckle.apply_translation([0, i * (knuckle_length + 1), 0])

                # Add mounting tab
                tab = trimesh.creation.box(extents=[pin_diameter * 2, knuckle_length, pin_diameter * 0.5])
                tab.apply_translation([-pin_diameter, i * (knuckle_length + 1), 0])

                knuckle = trimesh.util.concatenate([knuckle, tab])
                knuckles_part2.append(knuckle)

        # Create hinge pin
        pin_length = num_knuckles * (knuckle_length + 1)
        pin = trimesh.creation.cylinder(
            radius=pin_diameter / 2 - 0.2,  # Clearance
            height=pin_length,
            sections=32
        )
        pin.apply_translation([0, pin_length / 2, 0])

        part1 = trimesh.util.concatenate(knuckles_part1) if knuckles_part1 else trimesh.Trimesh()
        part2 = trimesh.util.concatenate(knuckles_part2) if knuckles_part2 else trimesh.Trimesh()

        logger.info(f"Created hinge with {num_knuckles} knuckles")

        return {
            'part1': part1,
            'part2': part2,
            'pin': pin
        }

    @staticmethod
    def smooth_vertices(
        mesh: trimesh.Trimesh,
        vertex_indices: List[int],
        iterations: int = 1
    ) -> trimesh.Trimesh:
        """
        Smooth specific vertices using Laplacian smoothing

        Args:
            mesh: Input mesh
            vertex_indices: Vertices to smooth
            iterations: Number of smoothing iterations

        Returns:
            Smoothed mesh
        """
        # Build adjacency list
        edges = mesh.edges_unique
        adjacency = {i: set() for i in range(len(mesh.vertices))}
        for edge in edges:
            adjacency[edge[0]].add(edge[1])
            adjacency[edge[1]].add(edge[0])

        # Laplacian smoothing
        for _ in range(iterations):
            new_positions = mesh.vertices.copy()

            for idx in vertex_indices:
                if idx in adjacency and len(adjacency[idx]) > 0:
                    # Average position of neighbors
                    neighbors = list(adjacency[idx])
                    avg_pos = np.mean(mesh.vertices[neighbors], axis=0)
                    new_positions[idx] = avg_pos

            mesh.vertices = new_positions

        logger.info(f"Smoothed {len(vertex_indices)} vertices with {iterations} iterations")
        return mesh
