#!/usr/bin/env python3
"""
Mesh Repair - Fix Common Mesh Problems
Repairs holes, non-manifold edges, inverted normals, and other issues
"""

import trimesh
import numpy as np
from typing import Dict, List, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class MeshRepairer:
    """
    Advanced mesh repair utilities for fixing common 3D model problems.
    """

    def __init__(self, mesh: trimesh.Trimesh):
        """
        Initialize mesh repairer

        Args:
            mesh: Input mesh to repair
        """
        self.mesh = mesh.copy()  # Work on a copy
        self.repair_log = []

    def repair_all(self, aggressive: bool = False) -> trimesh.Trimesh:
        """
        Run all repair operations in optimal order.

        Args:
            aggressive: If True, use more aggressive repair methods that may alter geometry

        Returns:
            Repaired mesh
        """
        logger.info("Starting comprehensive mesh repair")

        # Step 1: Remove degenerate faces (zero area)
        self._remove_degenerate_faces()

        # Step 2: Remove duplicate faces
        self._remove_duplicate_faces()

        # Step 3: Fix normals (consistent winding)
        self._fix_normals()

        # Step 4: Fill holes
        self._fill_holes(aggressive=aggressive)

        # Step 5: Fix non-manifold edges
        self._fix_non_manifold_edges(aggressive=aggressive)

        # Step 6: Remove unreferenced vertices
        self._remove_unreferenced_vertices()

        # Step 7: Merge duplicate vertices
        self._merge_duplicate_vertices()

        logger.info(f"Mesh repair complete. Applied {len(self.repair_log)} fixes")
        return self.mesh

    def _remove_degenerate_faces(self):
        """Remove faces with zero or near-zero area"""
        initial_faces = len(self.mesh.faces)
        self.mesh.remove_degenerate_faces()
        removed = initial_faces - len(self.mesh.faces)

        if removed > 0:
            self.repair_log.append(f"Removed {removed} degenerate faces")
            logger.info(f"Removed {removed} degenerate faces")

    def _remove_duplicate_faces(self):
        """Remove duplicate faces"""
        initial_faces = len(self.mesh.faces)
        self.mesh.remove_duplicate_faces()
        removed = initial_faces - len(self.mesh.faces)

        if removed > 0:
            self.repair_log.append(f"Removed {removed} duplicate faces")
            logger.info(f"Removed {removed} duplicate faces")

    def _fix_normals(self):
        """Fix face normal directions for consistent winding"""
        try:
            self.mesh.fix_normals()
            self.repair_log.append("Fixed face normals")
            logger.info("Fixed face normals")
        except Exception as e:
            logger.warning(f"Could not fix normals: {e}")

    def _fill_holes(self, aggressive: bool = False):
        """
        Fill holes in the mesh.

        Args:
            aggressive: If True, fill larger holes (may create distorted geometry)
        """
        # Trimesh has built-in hole filling
        try:
            # Get boundary loops (holes)
            if hasattr(self.mesh, 'fill_holes'):
                self.mesh.fill_holes()
                self.repair_log.append("Filled holes")
                logger.info("Filled holes in mesh")
        except Exception as e:
            logger.warning(f"Hole filling failed: {e}")

    def _fix_non_manifold_edges(self, aggressive: bool = False):
        """
        Fix non-manifold edges (edges shared by more than 2 faces).

        Non-manifold edges can cause problems in 3D printing and boolean operations.

        Args:
            aggressive: If True, remove problematic faces
        """
        # Detect non-manifold edges
        edges = self.mesh.edges_unique
        edge_face_count = self.mesh.face_adjacency_edges

        # Count how many faces each edge belongs to
        from collections import Counter
        edge_counts = Counter()

        for face in self.mesh.faces:
            # Each face has 3 edges
            for i in range(3):
                edge = tuple(sorted([face[i], face[(i + 1) % 3]]))
                edge_counts[edge] += 1

        # Find non-manifold edges (shared by more than 2 faces)
        non_manifold_edges = [edge for edge, count in edge_counts.items() if count > 2]

        if non_manifold_edges:
            logger.warning(f"Found {len(non_manifold_edges)} non-manifold edges")

            if aggressive:
                # Remove faces that contribute to non-manifold edges
                faces_to_remove = set()

                for face_idx, face in enumerate(self.mesh.faces):
                    for i in range(3):
                        edge = tuple(sorted([face[i], face[(i + 1) % 3]]))
                        if edge in non_manifold_edges:
                            faces_to_remove.add(face_idx)

                if faces_to_remove:
                    faces_to_keep = [i for i in range(len(self.mesh.faces)) if i not in faces_to_remove]
                    self.mesh.update_faces(np.array(faces_to_keep))
                    self.repair_log.append(f"Removed {len(faces_to_remove)} faces to fix non-manifold edges")
                    logger.info(f"Removed {len(faces_to_remove)} faces to fix non-manifold edges")
            else:
                self.repair_log.append(f"Warning: {len(non_manifold_edges)} non-manifold edges detected (use aggressive mode to fix)")

    def _remove_unreferenced_vertices(self):
        """Remove vertices that aren't used by any face"""
        initial_vertices = len(self.mesh.vertices)
        self.mesh.remove_unreferenced_vertices()
        removed = initial_vertices - len(self.mesh.vertices)

        if removed > 0:
            self.repair_log.append(f"Removed {removed} unreferenced vertices")
            logger.info(f"Removed {removed} unreferenced vertices")

    def _merge_duplicate_vertices(self, tolerance: float = 1e-6):
        """
        Merge vertices that are very close together.

        Args:
            tolerance: Distance threshold for considering vertices duplicates (mm)
        """
        initial_vertices = len(self.mesh.vertices)
        self.mesh.merge_vertices(merge_tex=True, merge_norm=True, digits_vertex=6)
        merged = initial_vertices - len(self.mesh.vertices)

        if merged > 0:
            self.repair_log.append(f"Merged {merged} duplicate vertices")
            logger.info(f"Merged {merged} duplicate vertices")

    def get_repair_log(self) -> List[str]:
        """Get log of all repairs performed"""
        return self.repair_log

    def analyze_issues(self) -> Dict:
        """
        Analyze mesh for common issues without repairing.

        Returns:
            Dict with issue counts and descriptions
        """
        issues = {
            'is_watertight': self.mesh.is_watertight,
            'is_winding_consistent': self.mesh.is_winding_consistent,
            'is_volume_consistent': self.mesh.is_volume,
            'degenerate_faces': 0,
            'duplicate_faces': 0,
            'unreferenced_vertices': 0,
            'non_manifold_edges': 0,
            'boundary_edges': len(self.mesh.edges_unique) - len(self.mesh.face_adjacency_edges),
            'total_vertices': len(self.mesh.vertices),
            'total_faces': len(self.mesh.faces)
        }

        # Count degenerate faces
        face_areas = self.mesh.area_faces
        issues['degenerate_faces'] = np.sum(face_areas < 1e-10)

        # Detect unreferenced vertices
        referenced = set()
        for face in self.mesh.faces:
            referenced.update(face)
        issues['unreferenced_vertices'] = len(self.mesh.vertices) - len(referenced)

        return issues


def repair_mesh(mesh: trimesh.Trimesh, aggressive: bool = False) -> Dict:
    """
    High-level function to repair a mesh.

    Args:
        mesh: Input mesh to repair
        aggressive: Use aggressive repair methods

    Returns:
        Dict containing:
            - mesh: Repaired mesh
            - repair_log: List of repairs performed
            - before: Issues before repair
            - after: Issues after repair
    """
    repairer = MeshRepairer(mesh)

    # Analyze before
    before_issues = repairer.analyze_issues()

    # Repair
    repaired_mesh = repairer.repair_all(aggressive=aggressive)

    # Analyze after
    repairer_after = MeshRepairer(repaired_mesh)
    after_issues = repairer_after.analyze_issues()

    return {
        'mesh': repaired_mesh,
        'repair_log': repairer.get_repair_log(),
        'before': before_issues,
        'after': after_issues,
        'improvements': {
            'watertight': after_issues['is_watertight'] and not before_issues['is_watertight'],
            'faces_cleaned': before_issues['total_faces'] - after_issues['total_faces'],
            'vertices_cleaned': before_issues['total_vertices'] - after_issues['total_vertices']
        }
    }


def quick_fix(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Quick mesh fix - just the essentials.

    Args:
        mesh: Input mesh

    Returns:
        Fixed mesh
    """
    mesh = mesh.copy()
    mesh.remove_degenerate_faces()
    mesh.remove_duplicate_faces()
    mesh.fix_normals()
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()

    return mesh


def make_watertight(mesh: trimesh.Trimesh, aggressive: bool = True) -> trimesh.Trimesh:
    """
    Attempt to make mesh watertight (suitable for 3D printing).

    Args:
        mesh: Input mesh
        aggressive: Use aggressive methods

    Returns:
        Watertight mesh (if successful)
    """
    repairer = MeshRepairer(mesh)
    repaired = repairer.repair_all(aggressive=aggressive)

    if not repaired.is_watertight:
        logger.warning("Mesh is still not watertight after repair")

        # Try convex hull as last resort (will change geometry significantly)
        if aggressive:
            logger.info("Attempting convex hull as fallback")
            repaired = mesh.convex_hull

    return repaired
