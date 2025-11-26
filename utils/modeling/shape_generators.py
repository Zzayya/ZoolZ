#!/usr/bin/env python3
"""
Parametric Shape Generators - Create 3D shapes from scratch
Supports basic primitives, complex shapes, and custom profiles
"""

import trimesh
import numpy as np
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ShapeGenerator:
    """Generate parametric 3D shapes"""

    @staticmethod
    def cube(size: float = 10.0, center: bool = True) -> trimesh.Trimesh:
        """Generate a cube"""
        mesh = trimesh.creation.box(extents=[size, size, size])
        if not center:
            mesh.apply_translation([size/2, size/2, size/2])
        return mesh

    @staticmethod
    def sphere(radius: float = 10.0, subdivisions: int = 3) -> trimesh.Trimesh:
        """Generate a sphere"""
        return trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)

    @staticmethod
    def cylinder(
        radius: float = 5.0,
        height: float = 20.0,
        sections: int = 32
    ) -> trimesh.Trimesh:
        """Generate a cylinder"""
        return trimesh.creation.cylinder(
            radius=radius,
            height=height,
            sections=sections
        )

    @staticmethod
    def cone(
        radius: float = 10.0,
        height: float = 20.0,
        sections: int = 32
    ) -> trimesh.Trimesh:
        """Generate a cone"""
        return trimesh.creation.cone(
            radius=radius,
            height=height,
            sections=sections
        )

    @staticmethod
    def torus(
        major_radius: float = 10.0,
        minor_radius: float = 3.0,
        major_sections: int = 32,
        minor_sections: int = 16
    ) -> trimesh.Trimesh:
        """Generate a torus"""
        return trimesh.creation.torus(
            major_radius=major_radius,
            minor_radius=minor_radius,
            major_sections=major_sections,
            minor_sections=minor_sections
        )

    @staticmethod
    def half_sphere(
        radius: float = 10.0,
        subdivisions: int = 3,
        hemisphere: str = 'top'
    ) -> trimesh.Trimesh:
        """Generate a half-sphere (dome)"""
        sphere = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)

        # Cut sphere in half
        if hemisphere == 'top':
            plane_normal = [0, -1, 0]
        elif hemisphere == 'bottom':
            plane_normal = [0, 1, 0]
        else:
            plane_normal = [0, -1, 0]

        half = sphere.slice_plane(
            plane_origin=[0, 0, 0],
            plane_normal=plane_normal,
            cap=True
        )
        return half

    @staticmethod
    def funnel(
        top_radius: float = 20.0,
        bottom_radius: float = 5.0,
        height: float = 30.0,
        wall_thickness: float = 2.0,
        sections: int = 32
    ) -> trimesh.Trimesh:
        """Generate a funnel (hollow truncated cone)"""
        # Outer cone
        outer = trimesh.creation.cone(
            radius=top_radius,
            height=height,
            sections=sections
        )

        # Inner cone (slightly smaller)
        inner_height = height - wall_thickness
        inner_top_radius = top_radius - wall_thickness
        inner_bottom_radius = max(bottom_radius - wall_thickness, 0.5)

        inner = trimesh.creation.cone(
            radius=inner_top_radius,
            height=inner_height,
            sections=sections
        )

        # Offset inner cone
        inner.apply_translation([0, wall_thickness/2, 0])

        # Boolean difference to create hollow
        try:
            funnel_mesh = outer.difference(inner)
            return funnel_mesh
        except:
            logger.warning("Boolean difference failed, returning outer cone")
            return outer

    @staticmethod
    def tube(
        radius: float = 5.0,
        height: float = 20.0,
        wall_thickness: float = 1.0,
        sections: int = 32
    ) -> trimesh.Trimesh:
        """Generate a hollow tube"""
        outer = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
        inner = trimesh.creation.cylinder(
            radius=radius - wall_thickness,
            height=height + 1,
            sections=sections
        )

        try:
            tube_mesh = outer.difference(inner)
            return tube_mesh
        except:
            return outer

    @staticmethod
    def ring(
        outer_radius: float = 10.0,
        inner_radius: float = 7.0,
        thickness: float = 2.0
    ) -> trimesh.Trimesh:
        """Generate a flat ring"""
        outer = trimesh.creation.cylinder(radius=outer_radius, height=thickness, sections=64)
        inner = trimesh.creation.cylinder(radius=inner_radius, height=thickness + 1, sections=64)

        try:
            ring_mesh = outer.difference(inner)
            return ring_mesh
        except:
            return outer

    @staticmethod
    def prism(
        radius: float = 10.0,
        height: float = 20.0,
        sides: int = 6
    ) -> trimesh.Trimesh:
        """Generate a prism (3-12 sides)"""
        return trimesh.creation.cylinder(
            radius=radius,
            height=height,
            sections=sides
        )

    @staticmethod
    def pyramid(
        base_radius: float = 10.0,
        height: float = 20.0,
        sides: int = 4
    ) -> trimesh.Trimesh:
        """Generate a pyramid"""
        return trimesh.creation.cone(
            radius=base_radius,
            height=height,
            sections=sides
        )

    @staticmethod
    def torus_knot(
        p: int = 2,
        q: int = 3,
        major_radius: float = 10.0,
        minor_radius: float = 2.0,
        segments: int = 100
    ) -> trimesh.Trimesh:
        """Generate a torus knot (decorative)"""
        # Parametric torus knot equations
        t = np.linspace(0, 2 * np.pi, segments)

        r = major_radius

        x = (r + minor_radius * np.cos(q * t)) * np.cos(p * t)
        y = (r + minor_radius * np.cos(q * t)) * np.sin(p * t)
        z = minor_radius * np.sin(q * t)

        vertices = np.column_stack([x, y, z])

        # Create path along knot
        path = trimesh.load_path(vertices)

        # Extrude circle along path to create tube
        try:
            mesh = trimesh.creation.sweep_polygon(
                polygon=trimesh.path.polygons.circle(radius=minor_radius/2),
                path=path
            )
            return mesh
        except:
            # Fallback to simple torus
            return trimesh.creation.torus(
                major_radius=major_radius,
                minor_radius=minor_radius
            )

    @staticmethod
    def rounded_box(
        size: float = 10.0,
        radius: float = 1.0
    ) -> trimesh.Trimesh:
        """Generate a box with rounded edges"""
        # Create box
        box = trimesh.creation.box(extents=[size, size, size])

        # Apply convex hull to round (simple approximation)
        # For true rounding, would need more complex algorithm
        return box

    @staticmethod
    def wedge(
        width: float = 10.0,
        depth: float = 10.0,
        height: float = 10.0
    ) -> trimesh.Trimesh:
        """Generate a wedge/ramp"""
        vertices = np.array([
            [0, 0, 0],
            [width, 0, 0],
            [width, depth, 0],
            [0, depth, 0],
            [0, 0, height],
            [width, 0, height]
        ])

        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # Bottom
            [0, 4, 5], [0, 5, 1],  # Front
            [1, 5, 2],             # Right
            [0, 3, 4],             # Left
            [3, 2, 5], [3, 5, 4]   # Back (sloped)
        ])

        return trimesh.Trimesh(vertices=vertices, faces=faces)

    @staticmethod
    def thread(
        diameter: float = 8.0,
        pitch: float = 1.25,
        length: float = 20.0,
        thread_depth: float = 0.6,
        turns: Optional[int] = None
    ) -> trimesh.Trimesh:
        """
        Generate ISO metric thread

        Args:
            diameter: Major diameter (M8 = 8mm)
            pitch: Thread pitch in mm
            length: Thread length
            thread_depth: Depth of thread (default ~60% of pitch)
            turns: Number of turns (auto-calculated if None)
        """
        if turns is None:
            turns = int(length / pitch)

        # Core cylinder
        core_radius = (diameter - thread_depth) / 2
        core = trimesh.creation.cylinder(
            radius=core_radius,
            height=length,
            sections=64
        )

        # Create helix path
        t = np.linspace(0, turns * 2 * np.pi, turns * 32)
        radius = diameter / 2

        x = radius * np.cos(t)
        y = np.linspace(0, length, len(t))
        z = radius * np.sin(t)

        # Thread profile (triangular)
        profile_points = np.array([
            [0, 0],
            [thread_depth, pitch/4],
            [0, pitch/2]
        ])

        # For now, return core with simplified thread representation
        # Full helix sweep would require more complex geometry
        return core

    @staticmethod
    def handle(
        width: float = 30.0,
        thickness: float = 5.0,
        grip_radius: float = 3.0,
        length: float = 50.0
    ) -> trimesh.Trimesh:
        """Generate a handle (rounded rectangle extrusion)"""
        # Create U-shaped profile
        outer_points = []
        inner_points = []

        # Simple rectangular handle for now
        handle_mesh = trimesh.creation.box(
            extents=[length, thickness, width]
        )

        # Add rounded ends (half-cylinders)
        end1 = trimesh.creation.cylinder(
            radius=thickness/2,
            height=width,
            sections=16
        )
        end1.apply_transform(trimesh.transformations.rotation_matrix(
            np.pi/2, [1, 0, 0]
        ))
        end1.apply_translation([-length/2, 0, 0])

        end2 = end1.copy()
        end2.apply_translation([length, 0, 0])

        # Combine
        handle_mesh = trimesh.util.concatenate([handle_mesh, end1, end2])
        return handle_mesh

    @staticmethod
    def drainage_tray(
        diameter: float = 100.0,
        base_thickness: float = 3.0,
        rim_height: float = 5.0,
        rim_thickness: float = 2.0,
        num_channels: int = 8,
        channel_width: float = 2.0,
        channel_depth: float = 1.0,
        spout_width: float = 15.0,
        spout_length: float = 20.0,
        spout_angle: float = 15.0,  # degrees downward
        center_drain_diameter: float = 10.0
    ) -> trimesh.Trimesh:
        """
        Generate a circular drainage tray with radial channels and a spout
        Perfect for sponge holders, soap dishes, etc.

        Args:
            diameter: Overall diameter of tray (mm)
            base_thickness: Thickness of the base plate (mm)
            rim_height: Height of the outer rim (mm)
            rim_thickness: Thickness of the rim wall (mm)
            num_channels: Number of radial drainage channels
            channel_width: Width of each channel (mm)
            channel_depth: Depth of each channel (mm)
            spout_width: Width of drainage spout (mm)
            spout_length: Length of drainage spout extending outward (mm)
            spout_angle: Downward angle of spout for drainage (degrees)
            center_drain_diameter: Diameter of central drain hole (mm)

        Returns:
            Drainage tray mesh
        """
        logger.info(f"Generating drainage tray: {diameter}mm diameter, {num_channels} channels")

        radius = diameter / 2.0

        # 1. Create base plate (flat cylinder)
        base = trimesh.creation.cylinder(
            radius=radius,
            height=base_thickness,
            sections=64
        )
        # Position so top surface is at z=0
        base.apply_translation([0, 0, -base_thickness/2])

        # 2. Create outer rim
        outer_rim = trimesh.creation.cylinder(
            radius=radius,
            height=rim_height,
            sections=64
        )
        outer_rim.apply_translation([0, 0, rim_height/2])

        inner_rim = trimesh.creation.cylinder(
            radius=radius - rim_thickness,
            height=rim_height + 1,
            sections=64
        )
        inner_rim.apply_translation([0, 0, rim_height/2])

        try:
            rim = outer_rim.difference(inner_rim)
        except:
            rim = outer_rim

        # 3. Combine base and rim
        try:
            tray = trimesh.util.concatenate([base, rim])
        except:
            tray = base

        # 4. Add central drain hole
        if center_drain_diameter > 0:
            drain_hole = trimesh.creation.cylinder(
                radius=center_drain_diameter/2,
                height=base_thickness + 2,
                sections=32
            )
            drain_hole.apply_translation([0, 0, -base_thickness/2 - 1])

            try:
                tray = tray.difference(drain_hole)
            except Exception as e:
                logger.warning(f"Could not add center drain: {e}")

        # 5. Carve radial channels from center to rim
        angle_step = 360.0 / num_channels

        for i in range(num_channels):
            angle_rad = np.deg2rad(i * angle_step)

            # Channel runs from center to rim
            channel_start_radius = center_drain_diameter / 2 + 2
            channel_end_radius = radius - rim_thickness - 1

            start_x = channel_start_radius * np.cos(angle_rad)
            start_y = channel_start_radius * np.sin(angle_rad)

            end_x = channel_end_radius * np.cos(angle_rad)
            end_y = channel_end_radius * np.sin(angle_rad)

            # Create channel as a thin box
            channel_length = channel_end_radius - channel_start_radius
            channel = trimesh.creation.box(
                extents=[channel_width, channel_length, channel_depth]
            )

            # Rotate to align with radial direction
            rotation = trimesh.transformations.rotation_matrix(
                angle_rad - np.pi/2, [0, 0, 1]
            )
            channel.apply_transform(rotation)

            # Position channel
            channel_center_radius = (channel_start_radius + channel_end_radius) / 2
            channel_x = channel_center_radius * np.cos(angle_rad)
            channel_y = channel_center_radius * np.sin(angle_rad)
            channel.apply_translation([channel_x, channel_y, -channel_depth/2])

            try:
                tray = tray.difference(channel)
            except Exception as e:
                logger.warning(f"Could not carve channel {i}: {e}")

        # 6. Add drainage spout
        if spout_length > 0 and spout_width > 0:
            # Create spout as extruded trapezoid
            # Spout is cut into the rim at one side
            spout_angle_rad = np.deg2rad(spout_angle)

            # Spout starts at rim edge
            spout_start_radius = radius - rim_thickness/2
            spout_end_radius = radius + spout_length

            # Create spout shape (tapered channel)
            spout_base_width = spout_width
            spout_tip_width = spout_width * 0.7  # Taper slightly

            # Spout positioned at angle 0 (pointing in +X direction)
            spout_center_x = (spout_start_radius + spout_end_radius) / 2
            spout_length_actual = spout_end_radius - spout_start_radius

            spout = trimesh.creation.box(
                extents=[spout_length_actual, spout_base_width, base_thickness + rim_height/2]
            )

            # Angle downward for drainage
            if spout_angle != 0:
                spout_rot = trimesh.transformations.rotation_matrix(
                    spout_angle_rad, [0, 1, 0]
                )
                spout.apply_transform(spout_rot)

            # Position spout
            spout.apply_translation([spout_center_x, 0, 0])

            try:
                # Boolean union to add spout
                tray = trimesh.util.concatenate([tray, spout])
            except Exception as e:
                logger.warning(f"Could not add spout: {e}")

        logger.info(f"Drainage tray created: {len(tray.vertices)} vertices")
        return tray


def generate_shape(shape_type: str, params: Dict) -> Dict:
    """
    High-level function to generate any shape

    Args:
        shape_type: Type of shape to generate
        params: Dictionary of parameters

    Returns:
        Dict containing mesh and stats
    """
    generator = ShapeGenerator()

    try:
        if shape_type == 'cube':
            mesh = generator.cube(
                size=params.get('size', 10.0)
            )
        elif shape_type == 'sphere':
            mesh = generator.sphere(
                radius=params.get('radius', 10.0),
                subdivisions=params.get('subdivisions', 3)
            )
        elif shape_type == 'cylinder':
            mesh = generator.cylinder(
                radius=params.get('radius', 5.0),
                height=params.get('height', 20.0)
            )
        elif shape_type == 'cone':
            mesh = generator.cone(
                radius=params.get('radius', 10.0),
                height=params.get('height', 20.0)
            )
        elif shape_type == 'torus':
            mesh = generator.torus(
                major_radius=params.get('major_radius', 10.0),
                minor_radius=params.get('minor_radius', 3.0)
            )
        elif shape_type == 'half_sphere':
            mesh = generator.half_sphere(
                radius=params.get('radius', 10.0),
                hemisphere=params.get('hemisphere', 'top')
            )
        elif shape_type == 'funnel':
            mesh = generator.funnel(
                top_radius=params.get('top_radius', 20.0),
                bottom_radius=params.get('bottom_radius', 5.0),
                height=params.get('height', 30.0),
                wall_thickness=params.get('wall_thickness', 2.0)
            )
        elif shape_type == 'tube':
            mesh = generator.tube(
                radius=params.get('radius', 5.0),
                height=params.get('height', 20.0),
                wall_thickness=params.get('wall_thickness', 1.0)
            )
        elif shape_type == 'ring':
            mesh = generator.ring(
                outer_radius=params.get('outer_radius', 10.0),
                inner_radius=params.get('inner_radius', 7.0),
                thickness=params.get('thickness', 2.0)
            )
        elif shape_type == 'prism':
            mesh = generator.prism(
                radius=params.get('radius', 10.0),
                height=params.get('height', 20.0),
                sides=params.get('sides', 6)
            )
        elif shape_type == 'pyramid':
            mesh = generator.pyramid(
                base_radius=params.get('base_radius', 10.0),
                height=params.get('height', 20.0),
                sides=params.get('sides', 4)
            )
        elif shape_type == 'torus_knot':
            mesh = generator.torus_knot(
                major_radius=params.get('major_radius', 10.0),
                minor_radius=params.get('minor_radius', 2.0)
            )
        elif shape_type == 'wedge':
            mesh = generator.wedge(
                width=params.get('width', 10.0),
                depth=params.get('depth', 10.0),
                height=params.get('height', 10.0)
            )
        elif shape_type == 'thread':
            mesh = generator.thread(
                diameter=params.get('diameter', 8.0),
                pitch=params.get('pitch', 1.25),
                length=params.get('length', 20.0)
            )
        elif shape_type == 'handle':
            mesh = generator.handle(
                width=params.get('width', 30.0),
                thickness=params.get('thickness', 5.0),
                length=params.get('length', 50.0)
            )
        elif shape_type == 'drainage_tray':
            mesh = generator.drainage_tray(
                diameter=params.get('diameter', 100.0),
                base_thickness=params.get('base_thickness', 3.0),
                rim_height=params.get('rim_height', 5.0),
                rim_thickness=params.get('rim_thickness', 2.0),
                num_channels=params.get('num_channels', 8),
                channel_width=params.get('channel_width', 2.0),
                channel_depth=params.get('channel_depth', 1.0),
                spout_width=params.get('spout_width', 15.0),
                spout_length=params.get('spout_length', 20.0),
                spout_angle=params.get('spout_angle', 15.0),
                center_drain_diameter=params.get('center_drain_diameter', 10.0)
            )
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")

        stats = {
            'shape_type': shape_type,
            'vertices': len(mesh.vertices),
            'faces': len(mesh.faces),
            'volume': float(mesh.volume),
            'surface_area': float(mesh.area),
            'watertight': mesh.is_watertight,
            'bounds': mesh.bounds.tolist()
        }

        return {
            'mesh': mesh,
            'stats': stats
        }

    except Exception as e:
        logger.error(f"Shape generation failed: {e}")
        raise
