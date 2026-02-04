import sys
import os
import unittest
import cv2
import tempfile
import numpy as np
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Add backend/services/ocr directory to path to avoid 'services' package init
backend_dir = Path(__file__).parent.parent
ocr_dir = backend_dir / "services" / "ocr"
sys.path.append(str(ocr_dir))

# Import directly from the module, not via services package
from inbody_matcher import InBodyMatcher

class TestInBodyMatcherResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Locate sample image
        cls.sample_image_path = "/home/user/ExplainMyBody-1/src/OCR/444.jpg"
        if not os.path.exists(cls.sample_image_path):
            print(f"Sample image not found at {cls.sample_image_path}. Integration tests will be skipped.")
            cls.sample_image = None
        else:
            cls.sample_image = cv2.imread(cls.sample_image_path)

    def setUp(self):
        if self.sample_image is None:
            self.skipTest("Sample image not found")

    def _resize_and_save(self, height: int) -> str:
        """Resize sample image to target height and save to temp file"""
        ratio = height / self.sample_image.shape[0]
        resized = cv2.resize(
            self.sample_image,
            (int(self.sample_image.shape[1] * ratio), height),
            interpolation=cv2.INTER_LANCZOS4
        )
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        cv2.imwrite(tf.name, resized)
        return tf.name

    def test_2400px_baseline(self):
        """Baseline test: 2400px should work perfectly (>=90%)"""
        # Create a "virtual" 2400px image from the source (which might be different)
        # Or just use source if we assume source is good. 
        # Let's explicitly resize to 2400 to be sure we are testing that resolution.
        temp_path = self._resize_and_save(2400)
        
        try:
            matcher = InBodyMatcher(target_height=2400, auto_perspective=True)
            result = matcher.extract_and_match(temp_path)
            
            non_null_count = sum(1 for v in result.values() if v is not None and v != "미검출")
            total_items = len(result)
            match_rate = non_null_count / total_items
            
            print(f"\n[2400px] Matched {non_null_count}/{total_items} ({match_rate:.2%})")
            
            # Baseline expectation: 90%
            self.assertGreaterEqual(match_rate, 0.90, "Match rate at 2400px should be >= 90%")
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_1200px_scaled(self):
        """Scaled test: 1200px (>=85%)"""
        temp_path = self._resize_and_save(1200)
        
        try:
            # Initialize with target_height=1200
            matcher = InBodyMatcher(target_height=1200, auto_perspective=True)
            result = matcher.extract_and_match(temp_path)
            
            non_null_count = sum(1 for v in result.values() if v is not None and v != "미검출")
            total_items = len(result)
            match_rate = non_null_count / total_items
            
            print(f"\n[1200px] Matched {non_null_count}/{total_items} ({match_rate:.2%})")
            
            # Expectation: 85%
            self.assertGreaterEqual(match_rate, 0.85, "Match rate at 1200px should be >= 85%")
            
            # Scaling verification
            self.assertIsNotNone(matcher.params)
            self.assertEqual(matcher.scale_manager.scale_ratio, 0.5)
            self.assertEqual(matcher.params.keyword_search_y_margin, 25) # 50 * 0.5
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_960px_scaled(self):
        """Scaled test: 960px (>=77%)"""
        temp_path = self._resize_and_save(960)
        
        try:
            matcher = InBodyMatcher(target_height=960, auto_perspective=True)
            result = matcher.extract_and_match(temp_path)
            
            non_null_count = sum(1 for v in result.values() if v is not None and v != "미검출")
            total_items = len(result)
            match_rate = non_null_count / total_items
            
            print(f"\n[960px] Matched {non_null_count}/{total_items} ({match_rate:.2%})")
            
            # Expectation: 77% (Lower due to lower OCR quality)
            self.assertGreaterEqual(match_rate, 0.77, "Match rate at 960px should be >= 77%")

            # Scaling verification
            self.assertIsNotNone(matcher.params)
            self.assertEqual(matcher.scale_manager.scale_ratio, 0.4)
            self.assertEqual(matcher.params.keyword_search_y_margin, 20) # 50 * 0.4
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()
