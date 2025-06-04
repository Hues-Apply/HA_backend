from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import CustomUser
from opportunities.models import Opportunity

class Command(BaseCommand):
    help = 'Creates default user groups and permissions'

    def handle(self, *args, **kwargs):
        # Create groups
        applicant_group, applicant_created = Group.objects.get_or_create(name='Applicants')
        employer_group, employer_created = Group.objects.get_or_create(name='Employers')
        admin_group, admin_created = Group.objects.get_or_create(name='Administrators')

        # Get content types
        user_content_type = ContentType.objects.get_for_model(CustomUser)
        opportunity_content_type = ContentType.objects.get_for_model(Opportunity)
        
        # Create custom permissions
        view_opportunities, _ = Permission.objects.get_or_create(
            codename='view_all_opportunities',
            name='Can view all opportunities',
            content_type=opportunity_content_type,
        )
        
        apply_opportunity, _ = Permission.objects.get_or_create(
            codename='apply_opportunity',
            name='Can apply to opportunities',
            content_type=opportunity_content_type,
        )
        
        create_opportunity, _ = Permission.objects.get_or_create(
            codename='create_opportunity',
            name='Can create opportunities',
            content_type=opportunity_content_type,
        )
        
        manage_applications, _ = Permission.objects.get_or_create(
            codename='manage_applications',
            name='Can manage applications to opportunities',
            content_type=opportunity_content_type,
        )

        # Assign permissions to groups
        # Applicants can view and apply to opportunities
        applicant_group.permissions.add(view_opportunities)
        applicant_group.permissions.add(apply_opportunity)

        # Employers can create and manage opportunities
        employer_group.permissions.add(view_opportunities)
        employer_group.permissions.add(create_opportunity)
        employer_group.permissions.add(manage_applications)

        # Administrators have all permissions
        # (they already have all permissions by default through is_superuser)

        # Output results
        self.stdout.write(self.style.SUCCESS('Successfully created groups and permissions'))
        
        # Show group counts
        self.stdout.write(f"Applicants group: {applicant_created and 'Created' or 'Already exists'}")
        self.stdout.write(f"Employers group: {employer_created and 'Created' or 'Already exists'}")
        self.stdout.write(f"Administrators group: {admin_created and 'Created' or 'Already exists'}")
