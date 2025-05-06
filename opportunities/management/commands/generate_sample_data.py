import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from faker import Faker
from opportunities.models import Opportunity, Category, Tag

class Command(BaseCommand):
    help = 'Generates sample opportunity data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10000,
            help='Number of sample opportunities to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        fake = Faker()
        
        self.stdout.write(self.style.SUCCESS(f'Creating {count} sample opportunities...'))
        
        # Create categories
        categories = []
        for category_name in ['Technology', 'Healthcare', 'Education', 'Engineering', 'Business', 
                              'Arts', 'Science', 'Finance', 'Marketing', 'Design']:
            category, created = Category.objects.get_or_create(
                name=category_name,
                slug=category_name.lower()
            )
            categories.append(category)
        
        # Create tags
        tags = []
        for tag_name in ['Python', 'JavaScript', 'React', 'Node.js', 'Django', 'Machine Learning',
                        'Data Science', 'UI/UX', 'Graphic Design', 'Marketing', 'Sales', 
                        'Human Resources', 'Finance', 'Leadership', 'Communication']:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                slug=tag_name.lower().replace(' ', '-').replace('/', '-')
            )
            tags.append(tag)
        
        # Generate opportunities
        opportunity_types = ['job', 'scholarship', 'grant', 'internship', 'fellowship']
        locations = ['Lagos, Nigeria', 'Nairobi, Kenya', 'Accra, Ghana', 'Johannesburg, South Africa', 
                    'Cairo, Egypt', 'Remote', 'New York, USA', 'London, UK', 'Berlin, Germany', 'Paris, France']
        
        batch_size = 500
        opportunities = []
        
        for i in range(count):
            if i > 0 and i % batch_size == 0:
                # Create in batches for better performance
                Opportunity.objects.bulk_create(opportunities)
                self.stdout.write(f'Created {i} opportunities...')
                opportunities = []
            
            opportunity_type = random.choice(opportunity_types)
            category = random.choice(categories)
            location = random.choice(locations)
            is_remote = location == 'Remote' or random.random() < 0.3
            
            # Generate random skills
            skills_count = random.randint(1, 5)
            all_skills = ['Python', 'JavaScript', 'React', 'Node.js', 'Django', 'Machine Learning',
                        'Leadership', 'Communication', 'Teamwork', 'Project Management',
                        'Data Analysis', 'Research', 'Writing', 'Public Speaking', 'Design',
                        'Marketing', 'Sales', 'Customer Service', 'Finance', 'Accounting']
            skills = random.sample(all_skills, skills_count)
            
            # Generate random eligibility criteria
            education_levels = ['high_school', 'bachelors', 'masters', 'phd']
            eligibility_criteria = {
                'education_level': random.choice(education_levels),
                'min_age': random.randint(18, 30),
                'max_age': random.randint(30, 60),
            }
            
            # Add nationality requirements for some opportunities
            if random.random() < 0.3:
                countries = ['Nigerian', 'Kenyan', 'Ghanaian', 'South African', 'Egyptian', 
                           'American', 'British', 'German', 'French']
                eligibility_criteria['nationalities'] = random.sample(countries, random.randint(1, 5))
            
            # Create the opportunity
            title_prefix = ""
            if opportunity_type == 'job':
                title_prefix = random.choice(['Junior ', 'Senior ', 'Lead ', '']) + random.choice([
                    'Software Developer', 'Data Scientist', 'Product Manager', 'UX Designer',
                    'Marketing Specialist', 'Sales Representative', 'HR Manager', 'Financial Analyst'
                ])
            elif opportunity_type == 'scholarship':
                title_prefix = random.choice([
                    'Full Tuition', 'Partial', 'Merit-based', 'Need-based', 'Research'
                ]) + ' Scholarship for ' + random.choice([
                    'Undergraduate Studies', 'Graduate Program', 'PhD Research', 'MBA Program'
                ])
            elif opportunity_type == 'grant':
                title_prefix = random.choice([
                    'Research Grant for', 'Development Grant in', 'Innovation Fund for', 
                    'Project Funding for'
                ]) + ' ' + category.name
            elif opportunity_type == 'internship':
                title_prefix = random.choice([
                    'Summer Internship:', 'Winter Internship:', 'Paid Internship:', '3-Month Internship:'
                ]) + ' ' + random.choice([
                    'Marketing Assistant', 'Engineering Intern', 'Research Assistant', 'Business Analyst'
                ])
            else:  # fellowship
                title_prefix = random.choice([
                    'Research Fellowship in', 'Academic Fellowship for', 'Professional Fellowship in',
                    'Leadership Fellowship:'
                ]) + ' ' + category.name
                
            title = f"{title_prefix} at {fake.company()}"
            
            # Create deadline between 1 week and 3 months in the future
            deadline_days = random.randint(7, 90)
            deadline = timezone.now().date() + timedelta(days=deadline_days)
            
            opportunity = Opportunity(
                title=title,
                type=opportunity_type,
                organization=fake.company(),
                category=category,
                location=location,
                is_remote=is_remote,
                description=fake.text(max_nb_chars=1000),
                eligibility_criteria=eligibility_criteria,
                skills_required=skills,
                deadline=deadline,
                is_verified=random.random() < 0.8,  # 80% are verified
                is_featured=random.random() < 0.1,  # 10% are featured
                application_url=fake.url() if random.random() < 0.7 else '',
                application_process=fake.text(max_nb_chars=300) if random.random() < 0.5 else ''
            )
            
            opportunities.append(opportunity)
        
        # Create any remaining opportunities
        if opportunities:
            Opportunity.objects.bulk_create(opportunities)
            
        # Add tags (needs to be done after creation due to M2M relationship)
        all_opportunities = Opportunity.objects.all()
        for opportunity in all_opportunities:
            # Add 1-3 tags
            opportunity_tags = random.sample(tags, random.randint(1, 3))
            opportunity.tags.add(*opportunity_tags)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} sample opportunities!'))
