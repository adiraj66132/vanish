import unittest
from types import SimpleNamespace

import numpy as np

from infinity_effect import hand_landmarks_from_result, upside_down_hands_from_result


def landmarks(points):
    return [SimpleNamespace(x=x, y=y) for x, y in points]


def hand(points):
    full = list(points) + [(0.0, 0.0)] * (21 - len(points))
    return landmarks(full)


class HandMappingTests(unittest.TestCase):
    def test_normalized_landmarks_map_to_full_frame(self):
        result = SimpleNamespace(hand_landmarks=[hand([(0.5, 0.25), (1.0, 1.0)])])
        hands = hand_landmarks_from_result(result, 1000, 500)
        self.assertEqual(hands[0][:2].tolist(), [[500.0, 125.0], [1000.0, 500.0]])

    def test_upside_down_mapping_flips_both_axes(self):
        result = SimpleNamespace(hand_landmarks=[hand([(0.25, 0.75), (0.0, 0.0)])])
        hands = upside_down_hands_from_result(result, 1000, 500)
        self.assertEqual(hands[0][:2].tolist(), [[750.0, 125.0], [1000.0, 500.0]])

    def test_degenerate_or_wrong_shape_landmarks_are_dropped(self):
        nan_hand = [(float("nan"), 0.5)] * 21
        short_hand = [(0.1, 0.2)] * 20
        for hand in (nan_hand, short_hand):
            result = SimpleNamespace(hand_landmarks=[landmarks(hand)])
            self.assertEqual(hand_landmarks_from_result(result, 100, 100), [])
            self.assertEqual(upside_down_hands_from_result(result, 100, 100), [])


if __name__ == "__main__":
    unittest.main()
