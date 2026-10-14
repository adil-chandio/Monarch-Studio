from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from conform_reference_audio import validate_picture_metrics


class ReferenceConformTests(unittest.TestCase):
    def test_full_portrait_picture_can_reach_audio_check(self):
        validate_picture_metrics(1332,30,720,1280,'test-fixture')
        validate_picture_metrics(1332,30,1080,1920,'test-fixture')

    def test_outro_is_not_accepted_as_full_film(self):
        with self.assertRaisesRegex(ValueError,'Full picture required'):
            validate_picture_metrics(108,30,1080,1920,'test-fixture')

    def test_other_chat_21_second_length_is_not_main_reference(self):
        with self.assertRaises(ValueError):validate_picture_metrics(632,30,1080,1920,'test-fixture')

    def test_wrong_frame_rate_or_shape_is_rejected(self):
        with self.assertRaises(ValueError):validate_picture_metrics(1332,24,1080,1920,'test-fixture')
        with self.assertRaises(ValueError):validate_picture_metrics(1332,30,1280,720,'test-fixture')

    def test_wrong_picture_duration_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Picture duration'):
            validate_picture_metrics(1332,30,720,1280,'test-fixture',duration=45.)

    def test_known_wrong_picture_files_are_not_relabelled(self):
        for md5 in ['42e52d770f6b53338639d2d1a01e2e48','bd9ac138749b658175c26873320a4a3c']:
            with self.assertRaisesRegex(ValueError,'Not a new picture edit'):
                validate_picture_metrics(1332,30,720,1280,md5)


if __name__=='__main__':unittest.main()
