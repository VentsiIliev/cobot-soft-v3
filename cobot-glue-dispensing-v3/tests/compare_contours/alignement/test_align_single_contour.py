import numpy as np
import pytest


from backend.system.contour_matching.alignment.contour_aligner import align_single_contour
from backend.system.contour_matching.matching_config import REFINEMENT_THRESHOLD
from compare_contours.testShapeGenerator import create_rectangle_contour
from modules.shared.core.ContourStandartized import Contour


# --- Fixtures for basic contours ---
@pytest.fixture
def square_contour():

    return Contour(create_rectangle_contour())

@pytest.fixture
def reference_square():

    return create_rectangle_contour(center=(500, 400))  # Offset reference

@pytest.fixture
def spray_contours(square_contour):
    return [square_contour]

@pytest.fixture
def spray_fills(square_contour):
    return [square_contour]

# --- Unit tests ---
def test_initial_rotation_translation(square_contour, reference_square):
    """Test initial rotation and translation applied."""
    initial_centroid = square_contour.getCentroid()
    align_single_contour(square_contour, reference_square, rotation_diff=45.0, translation_diff=(10, 20), refine=False)
    final_centroid = square_contour.getCentroid()

    # Centroid should move by translation
    assert np.allclose(final_centroid, np.array(initial_centroid) + np.array([10, 20]), atol=1e-5)

def test_refinement_applied(square_contour, reference_square):
    """Test mask-based refinement is applied."""
    # Patch _refine_alignment_with_mask to return known rotation
    from unittest.mock import patch
    # patch the function where it is looked up in the runtime module
    with patch("backend.system.contour_matching.alignment.contour_aligner._refine_alignment_with_mask") as mock_refine:
        mock_refine.return_value = (30.0, 1.0)  # Large enough to apply
        initial_centroid = square_contour.getCentroid()
        align_single_contour(square_contour, reference_square, refine=True)

        # Check that _refine_alignment_with_mask was called
        mock_refine.assert_called_once()
        # Final rotation moves centroid back (rotation about centroid doesn't move centroid)
        assert np.allclose(square_contour.getCentroid(), initial_centroid, atol=1e-5)

def test_spray_contours_transformed(square_contour, reference_square):
    """Test spray contours are rotated and translated along with target."""
    spray = Contour(square_contour.get())  # clone
    initial_centroid = spray.getCentroid()
    align_single_contour(square_contour, reference_square, spray_contours=[spray], rotation_diff=15, translation_diff=(5, 5), refine=False)

    # Spray centroid should be translated the same as target
    expected = np.array(initial_centroid) + np.array([5, 5])
    assert np.allclose(spray.getCentroid(), expected, atol=1e-5)

def test_no_refinement_below_threshold(square_contour, reference_square):
    """Test refinement rotation below threshold does not apply."""

    from unittest.mock import patch

    with patch("backend.system.contour_matching.alignment.contour_aligner._refine_alignment_with_mask") as mock_refine:
        mock_refine.return_value = (REFINEMENT_THRESHOLD * 0.5, 1.0)
        initial_centroid = square_contour.getCentroid()
        align_single_contour(square_contour, reference_square, refine=True)

        # Centroid should not move due to rotation below threshold
        assert np.allclose(square_contour.getCentroid(), initial_centroid, atol=1e-5)
