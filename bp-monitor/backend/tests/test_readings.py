from backend.services.medical import classify_bp, in_target_range


class TestReadingsLogic:
    def test_morning_reading_classification(self):
        """Morning hypertension (morning surge) detection."""
        assert "1级" in classify_bp(145, 92)

    def test_evening_normal_reading(self):
        assert classify_bp(118, 76) == "理想血压"

    def test_target_range_elderly(self):
        """80+ elderly: target < 150/90."""
        assert in_target_range(148, 88, 150, 90)
        assert not in_target_range(155, 88, 150, 90)

    def test_target_range_diabetes(self):
        """Diabetes comorbidity: target < 130/80."""
        assert in_target_range(125, 75, 130, 80)
        assert not in_target_range(135, 78, 130, 80)
