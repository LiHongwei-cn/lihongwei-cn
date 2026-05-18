from backend.services.medical import classify_bp, is_emergency, in_target_range


class TestClassifyBP:
    def test_ideal(self):
        assert classify_bp(110, 70) == "理想血压"

    def test_normal(self):
        assert classify_bp(125, 82) == "正常血压"

    def test_high_normal(self):
        assert classify_bp(135, 88) == "正常高值"

    def test_grade1_systolic(self):
        assert classify_bp(145, 85) == "1级高血压（轻度）"

    def test_grade1_diastolic(self):
        assert classify_bp(130, 95) == "1级高血压（轻度）"

    def test_grade2(self):
        assert classify_bp(165, 105) == "2级高血压（中度）"

    def test_grade3(self):
        assert classify_bp(185, 115) == "3级高血压（重度）"

    def test_grade3_diastolic_only(self):
        assert classify_bp(150, 112) == "3级高血压（重度）"

    def test_higher_level_wins(self):
        assert classify_bp(145, 105) == "2级高血压（中度）"


class TestIsEmergency:
    def test_no_emergency_normal(self):
        assert not is_emergency(140, 90)

    def test_emergency_high_with_symptoms(self):
        assert is_emergency(185, 100, "头痛胸闷")

    def test_emergency_low_bp(self):
        assert is_emergency(80, 50)


class TestInTargetRange:
    def test_in_range(self):
        assert in_target_range(135, 85, 140, 90)

    def test_out_of_range_systolic(self):
        assert not in_target_range(145, 85, 140, 90)

    def test_out_of_range_diastolic(self):
        assert not in_target_range(135, 95, 140, 90)
