import sys
import os
import unittest
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent.parent))

from services.ocr.inbody_matcher import ScaleManager, MatchingParameters, ScaledMatchingParameters

class TestMatchingParameters(unittest.TestCase):
    def test_scaling_960px(self):
        """Test scaling for 960px (Ratio 0.4)"""
        # Given
        target_height = 960
        base_height = 2400
        expected_ratio = 0.4
        
        # When
        manager = ScaleManager(target_height, base_height)
        base_params = MatchingParameters()
        scaled = base_params.scale(manager)
        
        # Then (Ratio)
        self.assertEqual(manager.scale_ratio, expected_ratio)
        
        # Then (A. Position Values - Scaled)
        self.assertEqual(scaled.segment_y_min, int(1400 * expected_ratio))  # 560
        self.assertEqual(scaled.segment_y_max, int(1900 * expected_ratio))  # 760
        self.assertEqual(scaled.body_fat_percent_y_min, int(1210 * expected_ratio)) # 484
        
        # Then (B. Distance Values - Scaled)
        self.assertEqual(scaled.keyword_search_y_margin, int(50 * expected_ratio)) # 20
        self.assertEqual(scaled.roi_y_margin, int(50 * expected_ratio)) # 20
        self.assertEqual(scaled.right_dir_x_min, int(-50 * expected_ratio)) # -20
        self.assertEqual(scaled.right_dir_y_max, int(80 * expected_ratio)) # 32
        
        # Then (C. Ratio Values - No Scale)
        self.assertEqual(scaled.similarity_threshold, 0.5)
        self.assertEqual(scaled.large_node_bonus, 20000)
        self.assertEqual(scaled.scale_mark_penalty, 50000)
        
        # Then (Weights - Scaled)
        self.assertEqual(scaled.distance_y_weight, int(300 * expected_ratio)) # 120
        
        # Then (Hough - Scaled with lower bound)
        # minLineLength: 100 * 0.4 = 40. Lower bound is 40.
        self.assertEqual(scaled.hough_min_line_length, 40)
        # maxLineGap: 10 * 0.4 = 4. Lower bound is 5.
        self.assertEqual(scaled.hough_max_line_gap, 5)

    def test_scaling_1200px(self):
        """Test scaling for 1200px (Ratio 0.5)"""
        # Given
        target_height = 1200
        
        # When
        manager = ScaleManager(target_height)
        base_params = MatchingParameters()
        scaled = base_params.scale(manager)
        
        # Then
        self.assertEqual(manager.scale_ratio, 0.5)
        self.assertEqual(scaled.segment_y_min, 700)  # 1400 * 0.5
        self.assertEqual(scaled.roi_y_margin, 25)    # 50 * 0.5
        
        # Hough
        self.assertEqual(scaled.hough_min_line_length, 50) # 100 * 0.5 = 50 (>40)
        self.assertEqual(scaled.hough_max_line_gap, 5)     # 10 * 0.5 = 5 (=5)

    def test_no_scale_ratios(self):
        """Verify ratio/weight values that shouldn't scale don't change"""
        manager = ScaleManager(1200) # 0.5 ratio
        base_params = MatchingParameters()
        scaled = base_params.scale(manager)
        
        self.assertEqual(scaled.similarity_threshold, base_params.similarity_threshold)
        self.assertEqual(scaled.large_node_bonus, base_params.large_node_bonus)
        self.assertEqual(scaled.scale_mark_penalty, base_params.scale_mark_penalty)

if __name__ == '__main__':
    unittest.main()
