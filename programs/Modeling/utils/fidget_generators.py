#!/usr/bin/env python3
"""
Fidget Toy Generators - Create popular stim toys and fidgets
Includes flexi models, interlocking rings, sliding mechanisms, twisty patterns
"""

import trimesh
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FidgetGenerators:
    """Generate fidget toys and stim toys"""

    @staticmethod
    def flexi_worm(
        length: float = 100.0,
        diameter: float = 15.0,
        num_segments: int = 20,
        flex_gap: float = 0.3
    ) -> trimesh.Trimesh:
        """
        Generate a flexi worm (articulated segments that bend)

        Args:
            length: Total length
            diameter: Diameter of worm
            num_segments: Number of segments
            flex_gap: Gap between segments for flexibility

        Returns:
            Flexi worm mesh
        """
        segment_length = (length - (num_segments - 1) * flex_gap) / num_segments
        segments = []

        for i in range(num_segments):
            # Main segment body
            segment = trimesh.creation.cylinder(
                radius=diameter / 2,
                height=segment_length,
                sections=32
            )

            # Add interlocking ridges
            if i < num_segments - 1:
                ridge = trimesh.creation.cylinder(
                    radius=diameter / 2 + 0.5,
                    height=segment_length * 0.2,
                    sections=32
                )
                ridge.apply_translation([0, 0, segment_length * 0.4])
                segment = trimesh.util.concatenate([segment, ridge])

            # Add socket for previous segment
            if i > 0:
                socket = trimesh.creation.cylinder(
                    radius=diameter / 2 + 0.6,
                    height=segment_length * 0.2,
                    sections=32
                )
                socket.apply_translation([0, 0, -segment_length * 0.4])

                inner = trimesh.creation.cylinder(
                    radius=diameter / 2 + 0.2,
                    height=segment_length * 0.25,
                    sections=32
                )
                inner.apply_translation([0, 0, -segment_length * 0.4])

                try:
                    socket = socket.difference(inner)
                    segment = trimesh.util.concatenate([segment, socket])
                except:
                    pass

            # Position segment
            z_pos = i * (segment_length + flex_gap)
            segment.apply_translation([0, 0, z_pos])

            segments.append(segment)

        worm = trimesh.util.concatenate(segments)
        logger.info(f"Created flexi worm: {num_segments} segments, {len(worm.vertices)} vertices")
        return worm

    @staticmethod
    def interlocking_rings(
        ring_diameter: float = 30.0,
        ring_thickness: float = 3.0,
        num_rings: int = 5,
        ring_type: str = 'circular'  # 'circular', 'hexagonal', 'square'
    ) -> trimesh.Trimesh:
        """
        Generate interlocking rings that can rotate around each other

        Args:
            ring_diameter: Outer diameter of rings
            ring_thickness: Thickness of ring material
            num_rings: Number of rings
            ring_type: Shape of rings

        Returns:
            Interlocking rings mesh
        """
        rings = []

        for i in range(num_rings):
            if ring_type == 'circular':
                # Create torus ring
                ring = trimesh.creation.torus(
                    major_radius=ring_diameter / 2,
                    minor_radius=ring_thickness / 2,
                    sections=64,
                    tube_sections=32
                )

            elif ring_type == 'hexagonal':
                # Create hexagonal ring
                outer_hex = trimesh.creation.cylinder(
                    radius=ring_diameter / 2,
                    height=ring_thickness,
                    sections=6
                )
                inner_hex = trimesh.creation.cylinder(
                    radius=ring_diameter / 2 - ring_thickness,
                    height=ring_thickness + 1,
                    sections=6
                )
                try:
                    ring = outer_hex.difference(inner_hex)
                except:
                    ring = outer_hex

            else:  # square
                outer_square = trimesh.creation.box(
                    extents=[ring_diameter, ring_diameter, ring_thickness]
                )
                inner_square = trimesh.creation.box(
                    extents=[ring_diameter - 2*ring_thickness, ring_diameter - 2*ring_thickness, ring_thickness + 1]
                )
                try:
                    ring = outer_square.difference(inner_square)
                except:
                    ring = outer_square

            # Rotate and position each ring to interlock
            if i % 2 == 0:
                # Rotate to vertical
                rotation = trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])
                ring.apply_transform(rotation)
                ring.apply_translation([i * (ring_diameter + 2), 0, 0])
            else:
                # Keep horizontal but offset
                ring.apply_translation([i * (ring_diameter + 2), 0, 0])

            rings.append(ring)

        result = trimesh.util.concatenate(rings)
        logger.info(f"Created {num_rings} interlocking {ring_type} rings")
        return result

    @staticmethod
    def fidget_spinner(
        center_diameter: float = 22.0,
        bearing_diameter: float = 8.0,
        num_weights: int = 3,
        weight_diameter: float = 18.0,
        weight_distance: float = 40.0,
        thickness: float = 8.0
    ) -> trimesh.Trimesh:
        """
        Generate a fidget spinner

        Args:
            center_diameter: Diameter of center bearing housing
            bearing_diameter: Diameter of bearing hole
            num_weights: Number of weighted ends (usually 2-4)
            weight_diameter: Diameter of each weight
            weight_distance: Distance from center to weights
            thickness: Thickness of spinner

        Returns:
            Fidget spinner mesh
        """
        # Center bearing housing
        center = trimesh.creation.cylinder(
            radius=center_diameter / 2,
            height=thickness,
            sections=64
        )

        # Bearing hole
        bearing = trimesh.creation.cylinder(
            radius=bearing_diameter / 2,
            height=thickness + 2,
            sections=32
        )

        try:
            center = center.difference(bearing)
        except:
            pass

        # Add weights
        weights = [center]

        for i in range(num_weights):
            angle = (2 * np.pi * i) / num_weights

            # Weight mass
            weight = trimesh.creation.cylinder(
                radius=weight_diameter / 2,
                height=thickness,
                sections=32
            )

            # Position weight
            x = weight_distance * np.cos(angle)
            y = weight_distance * np.sin(angle)
            weight.apply_translation([x, y, 0])

            # Connecting arm
            arm_length = weight_distance - center_diameter / 2 - weight_diameter / 2
            arm = trimesh.creation.box(extents=[arm_length, thickness * 0.6, thickness])
            arm.apply_translation([
                (weight_distance + center_diameter / 2) / 2 * np.cos(angle),
                (weight_distance + center_diameter / 2) / 2 * np.sin(angle),
                0
            ])

            weights.extend([weight, arm])

        spinner = trimesh.util.concatenate(weights)
        logger.info(f"Created fidget spinner with {num_weights} weights")
        return spinner

    @staticmethod
    def sliding_puzzle(
        grid_size: int = 3,
        tile_size: float = 20.0,
        tile_thickness: float = 5.0,
        gap: float = 0.5
    ) -> Dict[str, trimesh.Trimesh]:
        """
        Generate a sliding puzzle (like 15-puzzle)

        Args:
            grid_size: Size of grid (3x3, 4x4, etc.)
            tile_size: Size of each tile
            tile_thickness: Thickness of tiles
            gap: Gap between tiles

        Returns:
            Dict with 'tiles' (list) and 'frame' meshes
        """
        tiles = []

        # Create tiles (one less than grid_size^2 for the empty space)
        for i in range(grid_size * grid_size - 1):
            tile = trimesh.creation.box(extents=[tile_size, tile_size, tile_thickness])

            # Add beveled edges
            # (simplified - just the basic tile)

            # Position in grid
            row = i // grid_size
            col = i % grid_size

            x = col * (tile_size + gap)
            y = row * (tile_size + gap)

            tile.apply_translation([x, y, 0])
            tiles.append(tile)

        # Create frame
        frame_width = grid_size * (tile_size + gap) + gap
        frame_thickness = 3.0

        outer_frame = trimesh.creation.box(extents=[
            frame_width + 2 * frame_thickness,
            frame_width + 2 * frame_thickness,
            tile_thickness + 2
        ])

        inner_cavity = trimesh.creation.box(extents=[
            frame_width,
            frame_width,
            tile_thickness + 3
        ])

        try:
            frame = outer_frame.difference(inner_cavity)
        except:
            frame = outer_frame

        logger.info(f"Created {grid_size}x{grid_size} sliding puzzle")

        return {
            'tiles': tiles,
            'frame': frame
        }

    @staticmethod
    def twisty_puzzle_segment(
        radius: float = 25.0,
        angle: float = 45.0,
        thickness: float = 10.0,
        num_layers: int = 1
    ) -> trimesh.Trimesh:
        """
        Generate a segment for a twisty puzzle (like Rubik's cube piece)

        Args:
            radius: Radius from center
            angle: Angular span of segment (degrees)
            thickness: Thickness/depth
            num_layers: Number of layers

        Returns:
            Puzzle segment
        """
        angle_rad = np.deg2rad(angle)

        # Create wedge shape
        # Simplified: create a cylindrical wedge

        # Outer cylinder
        outer = trimesh.creation.cylinder(
            radius=radius,
            height=thickness,
            sections=64
        )

        # Cut to create wedge
        # Create cutting box
        cut_box1 = trimesh.creation.box(extents=[radius * 3, radius * 3, thickness + 2])
        rotation1 = trimesh.transformations.rotation_matrix(angle_rad / 2, [0, 0, 1])
        cut_box1.apply_transform(rotation1)
        cut_box1.apply_translation([radius, radius, 0])

        cut_box2 = trimesh.creation.box(extents=[radius * 3, radius * 3, thickness + 2])
        rotation2 = trimesh.transformations.rotation_matrix(-angle_rad / 2, [0, 0, 1])
        cut_box2.apply_transform(rotation2)
        cut_box2.apply_translation([radius, -radius, 0])

        try:
            segment = outer.difference(cut_box1)
            segment = segment.difference(cut_box2)
        except:
            segment = outer

        # Add interlocking nubs for rotation mechanism
        nub = trimesh.creation.cylinder(
            radius=2.0,
            height=2.0,
            sections=16
        )
        nub.apply_translation([radius * 0.7, 0, thickness / 2 + 1])

        segment = trimesh.util.concatenate([segment, nub])

        logger.info(f"Created twisty puzzle segment: {angle}° span")
        return segment

    @staticmethod
    def pop_it_bubble(
        bubble_diameter: float = 15.0,
        bubble_depth: float = 5.0,
        grid_size: Tuple[int, int] = (5, 5),
        spacing: float = 3.0,
        base_thickness: float = 2.0
    ) -> trimesh.Trimesh:
        """
        Generate a pop-it fidget toy (bubble grid)

        Args:
            bubble_diameter: Diameter of each bubble
            bubble_depth: Depth of bubble dome
            grid_size: Number of bubbles (rows, cols)
            spacing: Space between bubbles
            base_thickness: Thickness of base

        Returns:
            Pop-it toy mesh
        """
        rows, cols = grid_size

        # Create base plate
        base_width = cols * (bubble_diameter + spacing) + spacing
        base_height = rows * (bubble_diameter + spacing) + spacing

        base = trimesh.creation.box(extents=[base_width, base_height, base_thickness])

        # Create bubbles and subtract from base
        bubbles = []

        for row in range(rows):
            for col in range(cols):
                # Create hemisphere bubble
                bubble = trimesh.creation.icosphere(
                    subdivisions=3,
                    radius=bubble_diameter / 2
                )

                # Keep only bottom half
                vertices = bubble.vertices
                faces = bubble.faces

                # Filter faces where all vertices have z < 0
                valid_faces = []
                for face in faces:
                    if all(vertices[v][2] <= bubble_depth):
                        valid_faces.append(face)

                if valid_faces:
                    bubble = trimesh.Trimesh(vertices=vertices, faces=valid_faces)
                else:
                    bubble = trimesh.creation.icosphere(subdivisions=2, radius=bubble_diameter / 2)

                # Position bubble
                x = -base_width/2 + spacing + col * (bubble_diameter + spacing) + bubble_diameter / 2
                y = -base_height/2 + spacing + row * (bubble_diameter + spacing) + bubble_diameter / 2
                z = base_thickness / 2

                bubble.apply_translation([x, y, z])
                bubbles.append(bubble)

        # Boolean subtract all bubbles from base
        result = base
        for bubble in bubbles:
            try:
                result = result.difference(bubble)
            except:
                logger.warning("Failed to subtract bubble, continuing...")

        logger.info(f"Created {rows}x{cols} pop-it toy")
        return result

    @staticmethod
    def infinity_cube(
        cube_size: float = 20.0,
        hinge_gap: float = 0.5
    ) -> List[trimesh.Trimesh]:
        """
        Generate an infinity cube (8 hinged cubes that fold infinitely)

        Args:
            cube_size: Size of each cube
            hinge_gap: Gap for hinges

        Returns:
            List of 8 cube pieces
        """
        cubes = []

        # Create 8 cubes in a 2x2x2 arrangement
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    cube = trimesh.creation.box(extents=[cube_size, cube_size, cube_size])

                    # Add hinge connectors on appropriate faces
                    # Simplified version - just position cubes

                    pos_x = x * (cube_size + hinge_gap)
                    pos_y = y * (cube_size + hinge_gap)
                    pos_z = z * (cube_size + hinge_gap)

                    cube.apply_translation([pos_x, pos_y, pos_z])
                    cubes.append(cube)

        logger.info(f"Created infinity cube with 8 pieces")
        return cubes

    @staticmethod
    def chain_link(
        link_length: float = 30.0,
        link_width: float = 15.0,
        link_thickness: float = 3.0,
        num_links: int = 5
    ) -> trimesh.Trimesh:
        """
        Generate an interlocking chain

        Args:
            link_length: Length of each link
            link_width: Width of link
            link_thickness: Thickness of material
            num_links: Number of links in chain

        Returns:
            Chain mesh
        """
        links = []

        for i in range(num_links):
            # Create oval link using torus and cylinders
            # Simplified: create rectangular link

            # Outer rectangle
            outer = trimesh.creation.box(extents=[link_length, link_width, link_thickness])

            # Inner hole
            inner = trimesh.creation.box(extents=[
                link_length - 2 * link_thickness,
                link_width - 2 * link_thickness,
                link_thickness + 2
            ])

            try:
                link = outer.difference(inner)
            except:
                link = outer

            # Rotate every other link 90 degrees to interlock
            if i % 2 == 1:
                rotation = trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])
                link.apply_transform(rotation)

            # Position along chain
            link.apply_translation([i * link_length * 0.7, 0, 0])

            links.append(link)

        chain = trimesh.util.concatenate(links)
        logger.info(f"Created chain with {num_links} links")
        return chain

    @staticmethod
    def gear_fidget(
        num_teeth: int = 12,
        outer_radius: float = 25.0,
        inner_radius: float = 15.0,
        tooth_height: float = 3.0,
        thickness: float = 8.0,
        num_gears: int = 3
    ) -> List[trimesh.Trimesh]:
        """
        Generate interlocking gears for a fidget toy

        Args:
            num_teeth: Number of teeth on gear
            outer_radius: Outer radius of gear
            inner_radius: Inner radius (where teeth start)
            tooth_height: Height of each tooth
            thickness: Thickness of gear
            num_gears: Number of gears to create

        Returns:
            List of gear meshes
        """
        gears = []

        for gear_idx in range(num_gears):
            # Create base cylinder
            base = trimesh.creation.cylinder(
                radius=inner_radius,
                height=thickness,
                sections=64
            )

            # Add teeth around perimeter
            teeth = []
            for i in range(num_teeth):
                angle = (2 * np.pi * i) / num_teeth
                tooth_width = (2 * np.pi * inner_radius) / (num_teeth * 2)

                tooth = trimesh.creation.box(extents=[tooth_height * 2, tooth_width, thickness])

                # Position tooth
                x = (inner_radius + tooth_height) * np.cos(angle)
                y = (inner_radius + tooth_height) * np.sin(angle)

                tooth.apply_translation([x, y, 0])

                # Rotate to align radially
                rotation = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
                tooth.apply_transform(rotation)

                teeth.append(tooth)

            # Combine base and teeth
            all_parts = [base] + teeth
            gear = trimesh.util.concatenate(all_parts)

            # Add center hole for axle
            axle_hole = trimesh.creation.cylinder(
                radius=4.0,
                height=thickness + 2,
                sections=32
            )

            try:
                gear = gear.difference(axle_hole)
            except:
                pass

            # Position gears to interlock
            if gear_idx > 0:
                # Position next gear to mesh with previous
                spacing = (inner_radius + outer_radius) * 1.8
                gear.apply_translation([gear_idx * spacing, 0, 0])

                # Rotate to mesh teeth (offset by half tooth angle)
                offset_angle = np.pi / num_teeth
                rotation = trimesh.transformations.rotation_matrix(offset_angle, [0, 0, 1])
                gear.apply_transform(rotation)

            gears.append(gear)

        logger.info(f"Created {num_gears} interlocking gears")
        return gears
