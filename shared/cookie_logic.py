#!/usr/bin/env python3
"""
Cookie Cutter Logic
Adapted from user's COOKIECUTTER.py script
"""

import numpy as np
import cv2
import trimesh
from trimesh import util as tr_util
from trimesh import Scene
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
import shapely.affinity


def make_cookie_cutter_mesh(poly: Polygon,
                            blade_thick: float = 2.0,
                            blade_height: float = 35.0,
                            base_thick: float = 3.0,
                            base_extra: float = 10.0) -> trimesh.Trimesh:
    """
    Create cookie cutter mesh from polygon with smooth ergonomic base

    Args:
        poly: Shapely polygon of the cookie shape
        blade_thick: Thickness of cutting blade (mm)
        blade_height: Height of cutting blade (mm)
        base_thick: Thickness of base plate (mm)
        base_extra: How far base extends beyond blade (mm)

    Returns:
        trimesh.Trimesh of the complete cookie cutter
    """
    # Outer wall ring (blade) - sharp and detailed
    outer = poly.buffer(blade_thick, join_style=2, resolution=64)
    wall_ring = outer.difference(poly)
    wall_parts = wall_ring.geoms if isinstance(wall_ring, MultiPolygon) else [wall_ring]
    walls = [trimesh.creation.extrude_polygon(part, height=blade_height) for part in wall_parts]
    cutter_wall = tr_util.concatenate(walls)

    # Base ring - SMOOTH AND ERGONOMIC
    # First, get the overall shape with extra buffer
    blade_footprint = poly.buffer(blade_thick, join_style=2, resolution=64)

    # Apply smoothing to the blade footprint BEFORE extending for base
    # This creates a smooth, rounded base
    smooth_base_outline = blade_footprint.buffer(
        base_extra,
        join_style=1,  # Round joins for smooth ergonomic curves
        resolution=32   # High resolution for smooth curves
    )

    # Create the base ring (smooth outline - blade footprint)
    base_ring = smooth_base_outline.difference(poly)

    # Handle MultiPolygon case
    base_parts = base_ring.geoms if isinstance(base_ring, MultiPolygon) else [base_ring]
    bases = [trimesh.creation.extrude_polygon(part, height=base_thick) for part in base_parts]
    base_mesh = tr_util.concatenate(bases)

    # Assemble
    cutter_wall.apply_translation([0, 0, base_thick])
    try:
        mesh = base_mesh.union(cutter_wall)
    except Exception:
        mesh = tr_util.concatenate([base_mesh, cutter_wall])

    # Flatten any Scene and repair
    if isinstance(mesh, Scene):
        mesh = tr_util.concatenate(list(mesh.geometry.values()))
    if not mesh.is_watertight:
        mesh = mesh.process(validate=True)

    return mesh


def build_mask_from_image(img_path: str) -> np.ndarray:
    """
    Build binary mask from input image

    Automatically detects foreground using multiple strategies:
    1. Alpha channel (for transparent PNGs/WebP)
    2. GrabCut algorithm (robust for any foreground on background)
    3. Otsu's thresholding (fallback)

    Args:
        img_path: Path to input image

    Returns:
        Binary mask as numpy array
    """
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Cannot read image '{img_path}'")

    # Handle images with alpha channel (transparency)
    if img.shape[-1] == 4:
        # Use alpha channel as mask if available
        alpha = img[:, :, 3]
        mask = cv2.threshold(alpha, 128, 255, cv2.THRESH_BINARY)[1]
        print(f"🪙 using alpha channel: {cv2.countNonZero(mask)} pixels")
    else:
        # Convert to BGR if needed
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # NEW: Edge-based detection for black outlines around white areas (SpongeBob fix!)
        # Apply Canny edge detection to find all edges including black outlines
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Dilate edges to create connected regions
        kernel_edge = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges_dilated = cv2.dilate(edges, kernel_edge, iterations=1)

        # Find contours from edges
        edge_contours, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        edge_mask_success = False
        if edge_contours:
            # Get largest edge contour (the main outline)
            main_contour = max(edge_contours, key=cv2.contourArea)

            # Create mask from filled contour
            edge_mask = np.zeros_like(gray)
            cv2.drawContours(edge_mask, [main_contour], -1, 255, thickness=cv2.FILLED)

            # Check if edge-based mask is reasonable
            total_pixels = gray.shape[0] * gray.shape[1]
            edge_fg_ratio = cv2.countNonZero(edge_mask) / total_pixels

            if 0.05 < edge_fg_ratio < 0.95:
                print(f"🪙 using edge detection: {edge_fg_ratio:.1%} foreground (fixes white areas!)")
                mask = edge_mask
                edge_mask_success = True

        if not edge_mask_success:
            # Strategy 1: Try Otsu's thresholding first
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Check if we got reasonable foreground (between 5% and 95% of image)
        total_pixels = gray.shape[0] * gray.shape[1]
        fg_pixels = cv2.countNonZero(mask)
        fg_ratio = fg_pixels / total_pixels

        if not (0.05 < fg_ratio < 0.95):
            # Otsu didn't work well, try GrabCut
            print(f"🪙 Otsu gave {fg_ratio:.1%} foreground, trying GrabCut...")

            # Initialize mask for GrabCut
            h, w = gray.shape
            mask_gc = np.zeros((h, w), np.uint8)

            # Define a rectangle with margins (assume subject is in center)
            margin_h = int(h * 0.05)
            margin_w = int(w * 0.05)
            rect = (margin_w, margin_h, w - 2*margin_w, h - 2*margin_h)

            # GrabCut models
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)

            # Run GrabCut
            try:
                cv2.grabCut(img, mask_gc, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
                # Create binary mask (foreground and probable foreground)
                mask = np.where((mask_gc == 2) | (mask_gc == 0), 0, 1).astype('uint8') * 255
            except:
                # If GrabCut fails, fall back to simple thresholding
                print(f"🪙 GrabCut failed, using simple threshold")
                _, mask = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)

        print(f"🪙 initial mask nonzero: {cv2.countNonZero(mask)}")

    # Morphological operations to clean up
    kernel_size = max(5, min(img.shape[:2]) // 150) * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

    # Close small gaps
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Remove small noise
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Find largest contour and fill it
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cnt = max(contours, key=cv2.contourArea)
        filled = np.zeros_like(mask)
        cv2.drawContours(filled, [cnt], -1, 255, thickness=cv2.FILLED)
        mask = filled

    print(f"🪙 filled mask nonzero: {cv2.countNonZero(mask)}")
    return mask


def chaikin_smooth(points: np.ndarray, iterations: int = 2, ratio: float = 0.25) -> np.ndarray:
    """
    Apply Chaikin's corner cutting algorithm for smooth curves

    This creates rounded curves instead of sharp corners by subdividing
    line segments and moving points.

    Args:
        points: Numpy array of points (N, 2)
        iterations: Number of smoothing iterations
        ratio: Corner cutting ratio (0.25 is standard)

    Returns:
        Smoothed numpy array of points
    """
    pts = points.copy()

    for _ in range(iterations):
        new_pts = []
        n = len(pts)

        for i in range(n):
            p1 = pts[i]
            p2 = pts[(i + 1) % n]  # Wrap around for closed curve

            # Cut the corner: create two new points along the edge
            q = p1 + ratio * (p2 - p1)
            r = p1 + (1 - ratio) * (p2 - p1)

            new_pts.append(q)
            new_pts.append(r)

        pts = np.array(new_pts)

    return pts


def find_and_smooth_contour(mask: np.ndarray, mode: str = "outer",
                            epsilon_factor: float = 0.005, apply_curve_smoothing: bool = False) -> np.ndarray:
    """
    Extract and smooth contour from binary mask

    Strategy:
    1. Get perfect outside perimeter (no approximation)
    2. Apply controlled smoothing with Douglas-Peucker
    3. Optionally apply Chaikin curve smoothing for rounded edges
    4. Ensure closed contour with proper orientation

    Args:
        mask: Binary mask
        mode: "outer" for external contour only
        epsilon_factor: Smoothing factor for Douglas-Peucker (smaller = more detail)
        apply_curve_smoothing: If True, apply Chaikin smoothing for rounded curves

    Returns:
        Numpy array of contour points (N, 2)
    """
    # Get contours with NO approximation (CHAIN_APPROX_NONE = perfect perimeter)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise ValueError("No contours found in mask")

    # Get largest contour (perfect outside perimeter)
    cnt = max(contours, key=cv2.contourArea)

    print(f"🪙 original contour points: {len(cnt)}")

    # Now apply controlled smoothing with Douglas-Peucker
    perimeter = cv2.arcLength(cnt, True)
    epsilon = epsilon_factor * perimeter
    smoothed = cv2.approxPolyDP(cnt, epsilon, True)

    print(f"🪙 smoothed contour points: {len(smoothed)} (epsilon: {epsilon:.2f})")

    # Convert to (N, 2) array
    points = smoothed.squeeze()
    if points.ndim == 1:  # Single point edge case
        points = points.reshape(1, -1)

    # Apply Chaikin curve smoothing if requested (for rounded curves)
    if apply_curve_smoothing:
        # Apply more iterations for lower detail (more smoothing)
        iterations = 2 if epsilon_factor > 0.005 else 1
        points = chaikin_smooth(points, iterations=iterations)
        print(f"🪙 curve smoothed points: {len(points)}")

    return points


def generate_cookie_cutter(image_path: str, params: dict) -> trimesh.Trimesh:
    """
    Main function to generate cookie cutter from image

    Args:
        image_path: Path to input image
        params: Dictionary with keys:
            - blade_thick (float): Blade thickness in mm
            - blade_height (float): Blade height in mm
            - base_thick (float): Base thickness in mm
            - base_extra (float): Base extension beyond blade in mm
            - max_dim (float): Maximum dimension to scale to in mm
            - no_base (bool): Omit base plate if True
            - detail_level (float): Detail level 0.0-1.0 (0=smooth, 1=detailed)

    Returns:
        trimesh.Trimesh of the cookie cutter
    """
    # Extract parameters
    blade_thick = params.get('blade_thick', 2.0)
    blade_height = params.get('blade_height', 20.0)
    base_thick = params.get('base_thick', 3.0) if not params.get('no_base') else 0.0
    base_extra = params.get('base_extra', 10.0)
    max_dim = params.get('max_dim', 90.0)
    detail_level = params.get('detail_level', 0.5)

    # Map detail_level (0-1) to epsilon_factor
    # detail_level 0.0 = smooth (epsilon ~0.01)
    # detail_level 0.5 = medium (epsilon ~0.005)
    # detail_level 1.0 = very detailed (epsilon ~0.001)
    epsilon_factor = 0.01 - (detail_level * 0.009)  # 0.01 to 0.001

    # Build mask from image
    mask = build_mask_from_image(image_path)

    # Extract contour and create polygon with controlled smoothing
    # Apply curve smoothing for lower detail levels to get rounded edges instead of sharp corners
    apply_curve_smooth = detail_level < 0.6
    pts = find_and_smooth_contour(mask, mode="outer", epsilon_factor=epsilon_factor,
                                   apply_curve_smoothing=apply_curve_smooth)
    poly = Polygon(pts)
    
    # Validate and fix polygon
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty or poly.area < 1e-3:
        raise ValueError("Invalid polygon from contour")
    poly = orient(poly, sign=1.0)
    
    # Scale to fit max dimension
    minx, miny, maxx, maxy = poly.bounds
    scale = max_dim / max(maxx - minx, maxy - miny)
    poly = shapely.affinity.scale(poly, xfact=scale, yfact=scale, origin='center')
    
    # Build mesh
    mesh = make_cookie_cutter_mesh(
        poly,
        blade_thick=blade_thick,
        blade_height=blade_height,
        base_thick=base_thick,
        base_extra=base_extra
    )

    # Orient correctly for viewing:
    # The 2D image becomes a thin 3D extrusion (like a coin standing on edge)
    # Goal: Front of image faces camera, back lays flat on build plate
    # Trimesh creates mesh with Z-axis as height, XY as the image plane
    # We need: Back flat on XY plane (z=0), front facing +Y direction
    from trimesh.transformations import rotation_matrix

    # Rotate 90° around X axis to lay it down
    # This puts the back on the XY plane
    mesh.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))

    return mesh


def extract_outline_data(image_path: str, detail_level: float = 0.5) -> dict:
    """
    Extract outline data as JSON-serializable dict for preview/editing

    Args:
        image_path: Path to input image
        detail_level: Detail level 0.0-1.0 (0=smooth, 1=detailed)

    Returns:
        Dictionary with outline points and image dimensions
    """
    # Build mask from image
    mask = build_mask_from_image(image_path)

    # Map detail_level to epsilon_factor
    epsilon_factor = 0.01 - (detail_level * 0.009)

    # Extract contour
    apply_curve_smooth = detail_level < 0.6
    pts = find_and_smooth_contour(mask, mode="outer", epsilon_factor=epsilon_factor,
                                   apply_curve_smoothing=apply_curve_smooth)

    # Get image dimensions
    img = cv2.imread(image_path)
    height, width = img.shape[:2]

    return {
        'outline': pts.tolist(),  # Convert numpy array to list for JSON
        'width': int(width),
        'height': int(height),
        'point_count': len(pts),
        'type': 'outer'
    }


def extract_inner_details(image_path: str, precision: float = 0.5) -> dict:
    """
    Extract inner detail contours (eyes, clothing lines, etc.) for stamp generation

    Args:
        image_path: Path to input image
        precision: Precision level 0.0-1.0 (0=only large features, 1=all details)

    Returns:
        Dictionary with array of inner contour data
    """
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Cannot read image '{image_path}'")

    # Convert to grayscale
    if len(img.shape) == 3 and img.shape[-1] == 4:
        gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
    elif len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # Apply adaptive thresholding to find edges
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 11, 2)

    # Find ALL contours (including inner details)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return {'details': [], 'width': gray.shape[1], 'height': gray.shape[0]}

    # Calculate minimum area threshold based on precision (EXPONENTIAL SCALE)
    # precision 0.0 = only large features (>5% of image)
    # precision 1.0 = even tiny features (>0.01% of image)
    # Using exponential scale for better control across the slider range
    import math
    total_area = gray.shape[0] * gray.shape[1]
    min_area_ratio = 0.05 * math.pow(0.02, precision)  # Exponential: 0.05 to 0.0001
    min_area = total_area * min_area_ratio

    # Filter contours by area and hierarchy (only inner contours, not the main outline)
    # Store contours with their area for sorting
    detail_contours_with_area = []
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        # Check if it's an inner contour (has a parent)
        if hierarchy[0][i][3] != -1 and area > min_area:
            # Simplify contour
            perimeter = cv2.arcLength(cnt, True)
            epsilon = 0.005 * perimeter
            simplified = cv2.approxPolyDP(cnt, epsilon, True)

            if len(simplified) >= 3:  # Valid polygon
                detail_contours_with_area.append((area, simplified.squeeze().tolist()))

    # Sort by area (largest first) and limit to top 50
    detail_contours_with_area.sort(key=lambda x: x[0], reverse=True)
    MAX_CONTOURS = 50
    detail_contours = [contour for area, contour in detail_contours_with_area[:MAX_CONTOURS]]

    print(f"🪙 found {len(detail_contours)} inner details (precision: {precision:.2f}, total found: {len(detail_contours_with_area)}, showing top {min(len(detail_contours_with_area), MAX_CONTOURS)})")

    return {
        'details': detail_contours,
        'width': int(gray.shape[1]),
        'height': int(gray.shape[0]),
        'detail_count': len(detail_contours),
        'type': 'inner'
    }


def generate_cookie_cutter_from_outline(outline_data: dict, params: dict) -> trimesh.Trimesh:
    """
    Generate cookie cutter from pre-extracted outline data (for edited outlines)

    Args:
        outline_data: Dictionary with 'outline' key containing points array
        params: Same parameters as generate_cookie_cutter()

    Returns:
        trimesh.Trimesh of the cookie cutter
    """
    # Extract parameters
    blade_thick = params.get('blade_thick', 2.0)
    blade_height = params.get('blade_height', 20.0)
    base_thick = params.get('base_thick', 3.0) if not params.get('no_base') else 0.0
    base_extra = params.get('base_extra', 10.0)
    max_dim = params.get('max_dim', 90.0)

    # Get outline points
    pts = np.array(outline_data['outline'])

    # Create polygon
    poly = Polygon(pts)

    # Validate and fix polygon
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty or poly.area < 1e-3:
        raise ValueError("Invalid polygon from outline")
    poly = orient(poly, sign=1.0)

    # Scale to fit max dimension
    minx, miny, maxx, maxy = poly.bounds
    scale = max_dim / max(maxx - minx, maxy - miny)
    poly = shapely.affinity.scale(poly, xfact=scale, yfact=scale, origin='center')

    # Build mesh
    mesh = make_cookie_cutter_mesh(
        poly,
        blade_thick=blade_thick,
        blade_height=blade_height,
        base_thick=base_thick,
        base_extra=base_extra
    )

    # Orient correctly
    from trimesh.transformations import rotation_matrix
    mesh.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))

    return mesh


def generate_detail_stamp_from_outlines(detail_data: dict, params: dict) -> trimesh.Trimesh:
    """
    Generate detail stamp from inner outline data

    Args:
        detail_data: Dictionary with 'details' array of contour points
        params: Parameters including stamp_depth, stamp_height

    Returns:
        trimesh.Trimesh of the detail stamp
    """
    stamp_depth = params.get('stamp_depth', 2.0)
    stamp_height = params.get('stamp_height', 3.0)
    max_dim = params.get('max_dim', 90.0)

    # Create meshes for each detail contour
    detail_meshes = []

    for contour_points in detail_data['details']:
        pts = np.array(contour_points)
        if len(pts) < 3:
            continue

        try:
            # Create polygon
            poly = Polygon(pts)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty or poly.area < 1e-3:
                continue

            # Extrude to create raised detail
            detail_mesh = trimesh.creation.extrude_polygon(poly, height=stamp_depth)
            detail_meshes.append(detail_mesh)
        except:
            continue

    if not detail_meshes:
        raise ValueError("No valid detail contours found")

    # Combine all details
    combined = tr_util.concatenate(detail_meshes)

    # Scale to match cookie cutter dimensions
    bounds = combined.bounds
    current_size = max(bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1])
    scale_factor = max_dim / current_size
    combined.apply_scale(scale_factor)

    # Orient correctly
    from trimesh.transformations import rotation_matrix
    combined.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))

    return combined
