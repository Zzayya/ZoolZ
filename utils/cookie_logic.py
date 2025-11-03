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
