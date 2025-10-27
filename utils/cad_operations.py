#!/usr/bin/env python3
"""
CAD Operations
Parametric CAD using trimesh for OpenSCAD-like functionality
"""

from typing import Dict, List, Any, Optional
import trimesh
import numpy as np

# Shape registry to store created shapes
SHAPE_REGISTRY = {}
_shape_counter = 0


class Shape3D:
    """Wrapper class for 3D shapes with metadata"""

    def __init__(self, geometry: trimesh.Trimesh, shape_type: str, params: Dict, operations: List = None):
        global _shape_counter
        self.id = f"shape_{_shape_counter}"
        _shape_counter += 1

        self.geometry = geometry  # trimesh.Trimesh object
        self.shape_type = shape_type
        self.params = params
        self.operations = operations or []

        # Store in registry
        SHAPE_REGISTRY[self.id] = self

    def to_preview(self) -> Dict:
        """Convert to Three.js-compatible format"""
        mesh = self.geometry

        # Flatten vertices and faces for Three.js
        vertices = mesh.vertices.flatten().tolist()
        faces = mesh.faces.flatten().tolist()

        # Calculate normals
        mesh.vertex_normals  # This ensures normals are computed
        normals = mesh.vertex_normals.flatten().tolist()

        return {
            'vertices': vertices,
            'faces': faces,
            'normals': normals
        }

    def to_trimesh(self) -> trimesh.Trimesh:
        """Get trimesh object"""
        return self.geometry


def create_shape(shape_type: str, params: Dict, operations: List = None) -> Shape3D:
    """
    Create a parametric shape using build123d
    
    Args:
        shape_type: Type of shape (box, cylinder, sphere, etc.)
        params: Dictionary of shape parameters
        operations: List of operations to apply
        
    Returns:
        Shape3D object
    """
    # TODO: Implement with build123d
    
    if shape_type == 'box':
        return create_box(params, operations)
    elif shape_type == 'cylinder':
        return create_cylinder(params, operations)
    elif shape_type == 'sphere':
        return create_sphere(params, operations)
    elif shape_type == 'cone':
        return create_cone(params, operations)
    elif shape_type == 'torus':
        return create_torus(params, operations)
    elif shape_type == 'prism':
        return create_prism(params, operations)
    else:
        raise ValueError(f"Unknown shape type: {shape_type}")


def create_box(params: Dict, operations: List = None) -> Shape3D:
    """
    Create a box/cube

    Params:
        width, height, depth: Dimensions in mm
        center: Center at origin (default True)
    """
    width = params.get('width', 10)
    height = params.get('height', 10)
    depth = params.get('depth', 10)
    center = params.get('center', True)

    # Create box using trimesh
    box = trimesh.creation.box(extents=[width, depth, height])

    if not center:
        # Move to positive octant
        box.apply_translation([width/2, depth/2, height/2])

    return Shape3D(box, 'box', params, operations)


def create_cylinder(params: Dict, operations: List = None) -> Shape3D:
    """
    Create a cylinder

    Params:
        radius: Radius in mm
        height: Height in mm
        segments: Number of segments (default 32)
        center: Center at origin (default True)
    """
    radius = params.get('radius', 5)
    height = params.get('height', 10)
    segments = params.get('segments', 32)
    center = params.get('center', True)

    # Create cylinder using trimesh
    cylinder = trimesh.creation.cylinder(radius=radius, height=height, sections=segments)

    if not center:
        # Move to sit on XY plane
        cylinder.apply_translation([0, 0, height/2])

    return Shape3D(cylinder, 'cylinder', params, operations)


def create_sphere(params: Dict, operations: List = None) -> Shape3D:
    """
    Create a sphere

    Params:
        radius: Radius in mm
        subdivisions: Level of detail (default 3)
    """
    radius = params.get('radius', 5)
    subdivisions = params.get('subdivisions', 3)

    # Create sphere using trimesh (icosphere for smoothness)
    sphere = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)

    return Shape3D(sphere, 'sphere', params, operations)


def create_cone(params: Dict, operations: List = None) -> Shape3D:
    """
    Create a cone

    Params:
        radius: Bottom radius in mm
        height: Height in mm
        segments: Number of segments (default 32)
        center: Center at origin (default True)
    """
    radius = params.get('radius', 5)
    height = params.get('height', 10)
    segments = params.get('segments', 32)
    center = params.get('center', True)

    # Create cone using trimesh
    cone = trimesh.creation.cone(radius=radius, height=height, sections=segments)

    if not center:
        # Move to sit on XY plane
        cone.apply_translation([0, 0, height/2])

    return Shape3D(cone, 'cone', params, operations)


def create_torus(params: Dict, operations: List = None) -> Shape3D:
    """
    Create a torus

    Params:
        major_radius: Major radius (ring radius) in mm
        minor_radius: Minor radius (tube radius) in mm
        major_sections: Number of sections around ring (default 32)
        minor_sections: Number of sections around tube (default 16)
    """
    major_radius = params.get('major_radius', 10)
    minor_radius = params.get('minor_radius', 3)
    major_sections = params.get('major_sections', 32)
    minor_sections = params.get('minor_sections', 16)

    # Create torus using trimesh
    torus = trimesh.creation.torus(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_sections=major_sections,
        minor_sections=minor_sections
    )

    return Shape3D(torus, 'torus', params, operations)


def create_prism(params: Dict, operations: List = None) -> Shape3D:
    """
    Create a prism (regular polygon extruded)

    Params:
        sides: Number of sides (3=triangle, 4=square, 6=hexagon, etc.)
        radius: Radius of circumscribed circle in mm
        height: Height of extrusion in mm
    """
    sides = params.get('sides', 6)
    radius = params.get('radius', 5)
    height = params.get('height', 10)

    # Create regular polygon
    angles = np.linspace(0, 2*np.pi, sides, endpoint=False)
    vertices_2d = np.column_stack([
        radius * np.cos(angles),
        radius * np.sin(angles)
    ])

    # Create polygon path
    from shapely.geometry import Polygon as ShapelyPolygon
    poly = ShapelyPolygon(vertices_2d)

    # Extrude to create prism
    prism = trimesh.creation.extrude_polygon(poly, height=height)

    return Shape3D(prism, 'prism', params, operations)


def combine_shapes(shape_ids: List[str], operation: str) -> Shape3D:
    """
    Combine multiple shapes with boolean operation

    Args:
        shape_ids: List of shape IDs from registry
        operation: 'union', 'difference', or 'intersection'

    Returns:
        New combined Shape3D
    """
    if len(shape_ids) < 2:
        raise ValueError("Need at least 2 shapes to combine")

    # Get meshes from registry
    meshes = [SHAPE_REGISTRY[sid].geometry for sid in shape_ids]

    # Perform boolean operation
    if operation == 'union':
        result = meshes[0]
        for mesh in meshes[1:]:
            result = result.union(mesh, engine='blender')
    elif operation == 'difference':
        result = meshes[0]
        for mesh in meshes[1:]:
            result = result.difference(mesh, engine='blender')
    elif operation == 'intersection':
        result = meshes[0]
        for mesh in meshes[1:]:
            result = result.intersection(mesh, engine='blender')
    else:
        raise ValueError(f"Unknown operation: {operation}")

    return Shape3D(result, 'combined', {'operation': operation, 'shape_ids': shape_ids}, [])


def apply_threads(shape: Shape3D, thread_type: str, params: Dict) -> Shape3D:
    """
    Apply screw threads to a cylinder
    
    Args:
        shape: Shape3D cylinder to apply threads to
        thread_type: 'male' or 'female'
        params: Thread parameters (diameter, pitch, length)
    """
    # TODO: Implement with build123d thread tools
    # build123d has IsoThread for standard ISO metric threads!
    # from build123d import IsoThread
    #
    # diameter = params.get('diameter', 6)  # M6
    # pitch = params.get('pitch', 1.0)
    # length = params.get('length', 10)
    # external = thread_type == 'male'
    #
    # thread = IsoThread(
    #     major_diameter=diameter,
    #     pitch=pitch,
    #     length=length,
    #     external=external
    # )
    
    pass


def generate_openscad_code(shape_id: str) -> str:
    """
    Generate proper OpenSCAD code for a shape

    Args:
        shape_id: ID of shape in registry

    Returns:
        OpenSCAD script as string
    """
    shape = SHAPE_REGISTRY.get(shape_id)
    if not shape:
        raise ValueError(f"Shape {shape_id} not found in registry")

    code = "// Generated by ZoolZ\n"
    code += f"// Shape Type: {shape.shape_type}\n"
    code += f"// Shape ID: {shape.id}\n\n"

    # Add parameters as comments
    code += "// Parameters:\n"
    for key, value in shape.params.items():
        code += f"//   {key} = {value}\n"
    code += "\n"

    # Generate code based on shape type
    if shape.shape_type == 'box':
        w = shape.params.get('width', 10)
        h = shape.params.get('height', 10)
        d = shape.params.get('depth', 10)
        center = shape.params.get('center', True)
        code += f"cube([{w}, {d}, {h}], center={str(center).lower()});\n"

    elif shape.shape_type == 'cylinder':
        r = shape.params.get('radius', 5)
        h = shape.params.get('height', 10)
        segments = shape.params.get('segments', 32)
        center = shape.params.get('center', True)
        code += f"cylinder(r={r}, h={h}, center={str(center).lower()}, $fn={segments});\n"

    elif shape.shape_type == 'sphere':
        r = shape.params.get('radius', 5)
        subdivisions = shape.params.get('subdivisions', 3)
        # OpenSCAD uses $fn for sphere resolution
        fn = 2 ** (subdivisions + 3)  # Convert subdivision level to $fn
        code += f"sphere(r={r}, $fn={fn});\n"

    elif shape.shape_type == 'cone':
        r = shape.params.get('radius', 5)
        h = shape.params.get('height', 10)
        segments = shape.params.get('segments', 32)
        center = shape.params.get('center', True)
        # OpenSCAD cone is cylinder with r1=radius, r2=0
        code += f"cylinder(r1={r}, r2=0, h={h}, center={str(center).lower()}, $fn={segments});\n"

    elif shape.shape_type == 'torus':
        major_r = shape.params.get('major_radius', 10)
        minor_r = shape.params.get('minor_radius', 3)
        code += "// Torus (using rotate_extrude)\n"
        code += f"rotate_extrude($fn=64)\n"
        code += f"  translate([{major_r}, 0, 0])\n"
        code += f"  circle(r={minor_r}, $fn=32);\n"

    elif shape.shape_type == 'prism':
        sides = shape.params.get('sides', 6)
        radius = shape.params.get('radius', 5)
        height = shape.params.get('height', 10)
        code += f"// Regular {sides}-sided prism\n"
        code += f"linear_extrude(height={height})\n"
        code += f"  circle(r={radius}, $fn={sides});\n"

    elif shape.shape_type == 'combined':
        operation = shape.params.get('operation', 'union')
        shape_ids = shape.params.get('shape_ids', [])
        code += f"// Boolean {operation}\n"
        code += f"{operation}() {{\n"
        for sid in shape_ids:
            if sid in SHAPE_REGISTRY:
                child_shape = SHAPE_REGISTRY[sid]
                code += f"  // Shape: {child_shape.shape_type}\n"
                # Would recursively generate code for each child
        code += "}\n"

    else:
        code += f"// Unknown shape type: {shape.shape_type}\n"

    return code


def render_to_stl(shape_id: str, output_path: str):
    """
    Render shape to STL file
    
    Args:
        shape_id: ID of shape in registry
        output_path: Path to save STL file
    """
    shape = SHAPE_REGISTRY.get(shape_id)
    if not shape:
        raise ValueError(f"Shape {shape_id} not found in registry")
    
    # Convert to trimesh and export
    mesh = shape.to_trimesh()
    mesh.export(output_path)


# Helper functions for common operations

def apply_chamfer(shape: Shape3D, distance: float) -> Shape3D:
    """Apply chamfer to edges"""
    # TODO: Implement with build123d
    pass


def apply_fillet(shape: Shape3D, radius: float) -> Shape3D:
    """Apply fillet to edges"""
    # TODO: Implement with build123d
    pass


def make_hollow(shape: Shape3D, wall_thickness: float, close_ends: bool = True) -> Shape3D:
    """Make shape hollow with optional closed ends"""
    # TODO: Implement
    pass


def add_brim(shape: Shape3D, width: float, height: float, inverse: bool = False) -> Shape3D:
    """Add brim or inverse brim"""
    # TODO: Implement
    pass
