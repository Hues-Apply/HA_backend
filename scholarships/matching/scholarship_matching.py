from datetime import date
from .utils import parse_float, parse_date
from scholarships.models import ScholarshipProfile, Scholarship

def score_scholarship(profile: ScholarshipProfile, scholarship: Scholarship) -> int:
    score = 0

    scholarship_gpa = parse_float(scholarship.gpa)
    if scholarship_gpa is not None and abs(profile.gpa - scholarship_gpa) <= 0.3:
        score += 2

    if profile.location.lower() in scholarship.location.lower():
        score += 1

    if profile.course.lower() in scholarship.course.lower():
        score += 2

    if scholarship.degree_level and profile.degree_level.lower() == scholarship.degree_level.lower():
        score += 1

    if scholarship.nationality and profile.nationality.lower() == scholarship.nationality.lower():
        score += 1

    scholarship_amount = parse_float(scholarship.amount)
    if scholarship_amount is not None and profile.financial_need <= scholarship_amount:
        score += 2

    deadline = parse_date(scholarship.deadline)
    if deadline:
        days = (deadline - date.today()).days
        if 0 < days <= 30:
            score += 2
        elif 30 < days <= 60:
            score += 1

    if scholarship.overview:
        matches = sum(1 for tag in profile.eligibility_tags if tag.lower() in scholarship.overview.lower())
        score += matches

    return score
