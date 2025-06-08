from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError

from PIL import Image

import random

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
        """Set user as an employer"""
        # First remove from other roles
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

    
class UserProfile(models.Model):
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
        
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    profile_picture = models.ImageField(upload_to=user_directory_path, blank=True, default='profile_pictures/default.jpg', validators=[validate_image_size, validate_image_format]) #default image uplaoded from frontend team side
    phone_number = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    goal = models.CharField(max_length=100, blank=True)
    
   
    
class CareerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    industry = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    profile_summary = models.TextField()
    
class EducationProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    degree = models.CharField(max_length=100)
    school = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    extra_curricular = models.TextField(blank=True)
    
class ExperienceProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    
class ProjectsProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    project_title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    project_link = models.URLField(blank=True)
    description = models.TextField()
    
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
    
    