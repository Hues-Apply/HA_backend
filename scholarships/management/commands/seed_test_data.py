from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from scholarships.models import Scholarship, ScholarshipProfile
from datetime import datetime

class Command(BaseCommand):
    help = 'Seed a user, scholarship profile, and a few scholarships for testing'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # 1. Create test user
        email = "testuser@example.com"
        password = "12345678"
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"User created: {email}"))
        else:
            self.stdout.write(self.style.WARNING(f"User already exists: {email}"))

        # 2. Create Scholarship Profile
        profile, _ = ScholarshipProfile.objects.get_or_create(
            user=user,
            defaults={
                "gpa": 3.5,
                "location": "Ghana",
                "course": "Computer Science",
                "degree_level": "Bachelor",
                "nationality": "Ghanaian",
                "financial_need": 2000.0,
                "eligibility_tags": ["stem", "women"],
            }
        )
        self.stdout.write(self.style.SUCCESS("ScholarshipProfile created."))

        # 3. Create Scholarships
        scholarships = [
            {
                "title": "Women in Tech Scholarship",
                "gpa": "3.5",
                "location": "Ghana",
                "course": "Computer Science",
                "amount": "$3000",
                "deadline": "2025-09-01",
                "degree_level": "Bachelor",
                "nationality": "Ghanaian",
                "application_link": "https://example.com",
                "source": "Test Source",
                "overview": "For women in STEM",
            },
            {
                "title": "Engineering Scholars Fund",
                "gpa": "3.0",
                "location": "USA",
                "course": "Engineering",
                "amount": "$1500",
                "deadline": "2025-11-01",
                "degree_level": "Master",
                "nationality": "Any",
                "application_link": "https://example.org",
                "source": "Another Source",
                "overview": "Open to global applicants",
            }
        ]

        for data in scholarships:
            obj, _ = Scholarship.objects.get_or_create(
                title=data["title"],
                defaults={**data, "scraped_at": datetime.now()}
            )
        self.stdout.write(self.style.SUCCESS("Scholarships created."))

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Done. Login with:\n  Email: {email}\n  Password: {password}"
        ))
