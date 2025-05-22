from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete
from django.dispatch import receiver
# Create your models here.

class Profile(models.Model):   
    roles = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=roles)
    bio = models.TextField(blank=True ,null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")  
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)  # validators should be a list
   
    def delete(self):
        if self.profile_picture:
            self.profile_picture.delete()
        super().delete()
class Student(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.profile.user.username    

class Teacher(models.Model):
    profile= models.OneToOneField(Profile, on_delete=models.CASCADE)
    cv = models.FileField(upload_to='cvs/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    experience_years = models.IntegerField(default=0)
    linkedin_url = models.URLField(blank=True, null=True)
    specializations = models.CharField(max_length=200, blank=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    def clean(self):
        if not self.cv:
            raise ValidationError('CV is required for teacher profile.')
        if self.experience_years < 0:

            raise ValidationError('Experience years cannot be negative.')
        if not self.linkedin_url.startswith('https://www.linkedin.com/'):
            raise ValidationError('Invalid LinkedIn URL. It should start with "https://www.linkedin.com/".')
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        if self.cv:
            self.cv.delete(save=False)
        super().delete(*args, **kwargs)
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('teacher_detail', args=[str(self.id)])
    def get_profile_picture(self):
        if self.profile and self.profile.profile_picture:
            return self.profile.profile_picture.url
        return None


class Courses(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    students = models.ManyToManyField(Student, related_name='courses')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    def __str__(self):
        return self.name

class video(models.Model):
    file=models.FileField(upload_to='videos/', null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    @receiver(post_delete, sender=file)
    def delete_video_file(sender, instance, **kwargs):
     if instance.file:
        instance.file.delete(False)
    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)