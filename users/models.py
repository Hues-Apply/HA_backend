from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError

from PIL import Image

import random
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields): 
        if not email:
            raise ValueError('The Email is required.')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    
    username = None
    email = models.EmailField(unique=True, max_length=254)
    is_email_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
        
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    def generate_otp(self):
        otp = f"{random.randint(100000, 999999)}"
        self.otp = otp
        self.save()
        return otp  
    
    # Role management methods
    def add_to_role(self, role_name):
        """Add user to a role (group)"""
        from django.contrib.auth.models import Group
        role, _ = Group.objects.get_or_create(name=role_name)
        self.groups.add(role)
        return self
    
    def remove_from_role(self, role_name):
        """Remove user from a role (group)"""
        from django.contrib.auth.models import Group
        try:
            role = Group.objects.get(name=role_name)
            self.groups.remove(role)
        except Group.DoesNotExist:
            pass
        return self
    
    def set_as_applicant(self):
        """Set user as an applicant"""
        # First remove from other roles
        self.remove_from_role('Employers')
        # Then add to applicant role
        self.add_to_role('Applicants')
        return self
    
    def set_as_employer(self):
        """Set user as an employer"""        # First remove from other roles
        self.remove_from_role('Applicants')
        # Then add to employer role
        self.add_to_role('Employers')
        return self
    
    def is_applicant(self):
        """Check if user is an applicant"""
        return self.groups.filter(name='Applicants').exists()
    
    def is_employer(self):
        """Check if user is an employer"""
        return self.groups.filter(name='Employers').exists()
        
    def get_role(self):
        """Get user's primary role"""
        if self.is_superuser:
            return "Administrator"
        elif self.is_employer():
            return "Employer"
        elif self.is_applicant():
            return "Applicant"
        else:
            return "Unassigned"

def validate_image_size(image):
    file_size = image.file.size
    limit_kb = 500
    if file_size > limit_kb * 1024:
        raise ValidationError(f"Image size should not exceed {limit_kb} KB")
    
def validate_image_format(image):
    try:
        img = Image.open(image)
        if img.format not in ['JPEG', 'PNG']:
            raise ValidationError("Only JPEG and PNG images are allowed.")
    except Exception:
        raise ValidationError("Invalid image format.")

def user_directory_path(instance, filename):
    return f'profile_pictures/user_{instance.user.id}/{filename}'
        
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    profile_picture = models.ImageField(upload_to=user_directory_path, blank=True, default='profile_pictures/default.jpg', validators=[validate_image_size, validate_image_format]) #default image uplaoded from frontend team side
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    goal = models.CharField(max_length=100, blank=True)
    
    # Google OAuth fields
    google_id = models.CharField(max_length=255, blank=True, null=True)
    google_picture = models.URLField(blank=True, null=True)
    google_access_token = models.TextField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True)
    
   
    
class CareerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    industry = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    profile_summary = models.TextField()
    
class EducationProfile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='education_profiles')
    degree = models.CharField(max_length=100)
    school = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_currently_studying = models.BooleanField(default=False)
    extra_curricular = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
class ExperienceProfile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='experience_profiles')
    job_title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_currently_working = models.BooleanField(default=False)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
class ProjectsProfile(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='project_profiles')
    project_title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_currently_working = models.BooleanField(default=False)
    project_link = models.URLField(blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
class OpportunitiesInterest(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    scholarships = models.BooleanField(default=False)
    jobs = models.BooleanField(default=False)
    grants = models.BooleanField(default=False)
    internships = models.BooleanField(default=False)

class RecommendationPriority(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    academic_background = models.BooleanField(default=False)
    work_experience = models.BooleanField(default=False)
    preferred_locations = models.BooleanField(default=False)
    others = models.BooleanField(default=False)
    additional_preferences = models.TextField(blank=True, help_text="Additional preferences for recommendations")

def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'documents/user_{instance.user.id}/{filename}'


def validate_document_format(document):
    """Validate document format"""
    allowed_formats = ['pdf', 'doc', 'docx']
    ext = document.name.split('.')[-1].lower()
    if ext not in allowed_formats:
        raise ValidationError("Only PDF, DOC, and DOCX files are allowed.")


def validate_document_size(document):
    """Validate document size (max 10MB)"""
    try:
        # Handle different file object types
        if hasattr(document, 'size'):
            file_size = document.size
        elif hasattr(document, 'file') and hasattr(document.file, 'size'):
            file_size = document.file.size
        elif hasattr(document, '_file') and hasattr(document._file, 'size'):
            file_size = document._file.size
        else:
            # If we can't determine size, skip validation
            return
        
        limit_mb = 10
        if file_size > limit_mb * 1024 * 1024:
            raise ValidationError(f"File size should not exceed {limit_mb} MB")
    except AttributeError:
        # If we can't access size for any reason, skip validation
        pass


class Document(models.Model):
    """Model for storing uploaded CV/resume documents"""
    DOCUMENT_TYPES = [
        ('cv', 'CV/Resume'),
        ('cover_letter', 'Cover Letter'),
        ('certificate', 'Certificate'),
        ('other', 'Other'),    ]
    
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='cv')
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[validate_document_format, validate_document_size]
    )
    original_filename = models.CharField(max_length=255)
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='pending')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.original_filename}"


class UserGoal(models.Model):
    """Model for storing user's selected goals"""
    GOAL_CHOICES = [
        ('job_opportunities', 'Get Job Opportunities'),
        ('cv_assistance', 'CV & Cover Letter Assistance'),
        ('scholarship_opportunities', 'Get Scholarship Opportunities'),
        ('grant_opportunities', 'Get Grant Opportunities'),
        ('internship_opportunities', 'Get Internship Opportunities'),
        ('career_guidance', 'Career Guidance'),
        ('skill_development', 'Skill Development'),
        ('networking', 'Networking Opportunities'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='goals')
    goal = models.CharField(max_length=50, choices=GOAL_CHOICES)
    priority = models.PositiveIntegerField(default=1)  # 1 = highest priority
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'goal']
        ordering = ['priority', 'created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_goal_display()}"


class ParsedProfile(models.Model):
    """Model for storing parsed CV/resume data"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='parsed_profile')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Personal Information
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    linkedin = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    
    # Professional Summary
    summary = models.TextField(blank=True)
    
    # Structured data stored as JSON
    education = models.JSONField(default=list, blank=True)  # List of education entries
    experience = models.JSONField(default=list, blank=True)  # List of work experience
    skills = models.JSONField(default=list, blank=True)  # List of skills
    certifications = models.JSONField(default=list, blank=True)  # List of certifications
    languages = models.JSONField(default=list, blank=True)  # List of languages with proficiency
    projects = models.JSONField(default=list, blank=True)  # List of projects
    
    # Metadata
    confidence_score = models.FloatField(null=True, blank=True)  # Overall parsing confidence (0-1)
    parsed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - Parsed Profile"
    
    @property
    def completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 12  # Number of main sections
        completed_fields = 0
        
        # Personal info fields
        if self.first_name: completed_fields += 1
        if self.last_name: completed_fields += 1
        if self.email: completed_fields += 1
        if self.phone: completed_fields += 1
        if self.address: completed_fields += 1
        if self.linkedin: completed_fields += 1
        if self.portfolio: completed_fields += 1
        
        # Content fields
        if self.summary: completed_fields += 1
        if self.education: completed_fields += 1
        if self.experience: completed_fields += 1
        if self.skills: completed_fields += 1
        if self.certifications or self.languages or self.projects: completed_fields += 1
        
        return round((completed_fields / total_fields) * 100)
    
    @property
    def missing_sections(self):
        """Get list of missing profile sections"""
        missing = []
        
        if not self.first_name or not self.last_name:
            missing.append('personal_info')
        if not self.summary:
            missing.append('summary')
        if not self.education:
            missing.append('education')
        if not self.experience:
            missing.append('experience')
        if not self.skills:
            missing.append('skills')
        if not self.certifications:
            missing.append('certifications')
        if not self.languages:
            missing.append('languages')
        if not self.projects:
            missing.append('projects')
            
        return missing
    
    @property
    def completed_sections(self):
        """Get list of completed profile sections"""
        completed = []
        
        if self.first_name and self.last_name:
            completed.append('personal_info')
        if self.summary:
            completed.append('summary')
        if self.education:
            completed.append('education')
        if self.experience:
            completed.append('experience')
        if self.skills:
            completed.append('skills')
        if self.certifications:
            completed.append('certifications')
        if self.languages:
            completed.append('languages')
        if self.projects:
            completed.append('projects')
            
        return completed

