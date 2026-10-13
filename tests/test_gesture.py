import math

import pytest

import gesture


def hand(thumb=(100, 100), index=(100, 200), wrist=(0, 0), knuckle=(0, 100)):
    """A minimal landmark list: only the ids the gesture maths needs. Palm size defaults to 100."""
    return [
        [gesture.WRIST, *wrist],
        [gesture.THUMB_TIP, *thumb],
        [gesture.INDEX_MCP, *knuckle],
        [gesture.INDEX_TIP, *index],
    ]


class TestPinchRatio:
    def test_is_distance_divided_by_palm_size(self):
        # thumb-index distance 100, palm size 100
        assert gesture.pinch_ratio(hand()) == pytest.approx(1.0)

    def test_is_independent_of_hand_scale(self):
        near = hand(thumb=(100, 100), index=(100, 160), knuckle=(0, 100))
        far = hand(thumb=(50, 50), index=(50, 80), knuckle=(0, 50))  # same pose, half the size
        assert gesture.pinch_ratio(near) == pytest.approx(gesture.pinch_ratio(far))

    def test_touching_fingertips_give_zero(self):
        assert gesture.pinch_ratio(hand(thumb=(10, 10), index=(10, 10))) == 0

    def test_diagonal_distances(self):
        ratio = gesture.pinch_ratio(hand(thumb=(0, 0), index=(30, 40)))
        assert ratio == pytest.approx(math.hypot(30, 40) / 100)

    def test_returns_none_when_a_landmark_is_missing(self):
        incomplete = [lm for lm in hand() if lm[0] != gesture.THUMB_TIP]
        assert gesture.pinch_ratio(incomplete) is None
        assert gesture.pinch_ratio([]) is None

    def test_returns_none_for_a_degenerate_palm(self):
        assert gesture.pinch_ratio(hand(wrist=(5, 5), knuckle=(5, 5))) is None


class TestRatioToPercent:
    def test_endpoints_and_midpoint(self):
        assert gesture.ratio_to_percent(0.15) == pytest.approx(0)
        assert gesture.ratio_to_percent(1.0) == pytest.approx(100)
        assert gesture.ratio_to_percent(0.575) == pytest.approx(50)

    def test_is_clamped(self):
        assert gesture.ratio_to_percent(-3) == 0
        assert gesture.ratio_to_percent(0.0) == 0
        assert gesture.ratio_to_percent(9) == 100

    def test_custom_range(self):
        assert gesture.ratio_to_percent(0.5, closed=0.0, open_=2.0) == pytest.approx(25)

    def test_rejects_an_empty_range(self):
        with pytest.raises(ValueError):
            gesture.ratio_to_percent(0.5, closed=1.0, open_=1.0)

    def test_is_monotonic(self):
        values = [gesture.ratio_to_percent(r / 20) for r in range(0, 30)]
        assert values == sorted(values)


class TestSmoother:
    def test_first_value_passes_through(self):
        assert gesture.Smoother(alpha=0.3).update(80) == 80

    def test_moves_a_fraction_towards_new_values(self):
        s = gesture.Smoother(alpha=0.5)
        s.update(0)
        assert s.update(100) == pytest.approx(50)
        assert s.update(100) == pytest.approx(75)

    def test_converges_to_a_constant_input(self):
        s = gesture.Smoother(alpha=0.3)
        s.update(0)
        for _ in range(60):
            value = s.update(40)
        assert value == pytest.approx(40, abs=0.01)

    def test_reset_forgets_history(self):
        s = gesture.Smoother()
        s.update(10)
        s.reset()
        assert s.update(90) == 90

    @pytest.mark.parametrize("alpha", [0, -1, 1.5])
    def test_rejects_invalid_alpha(self, alpha):
        with pytest.raises(ValueError):
            gesture.Smoother(alpha=alpha)
