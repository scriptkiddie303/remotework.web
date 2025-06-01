import datetime
import mimetypes
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect

from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
import stripe

from .models import Payment, ProgressTracker, Student ,Profile, Teacher, Courses, video

from django.contrib import messages

from django.contrib.auth import logout,authenticate,login 

from django.contrib.auth.models import User

import dns.resolver
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from django.utils import timezone

import random
import datetime
from django.utils import timezone
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib import messages

from django.contrib.auth import update_session_auth_hash
from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename
from django.core.files import File
def has_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return len(records) > 0
    except Exception:
        return False

def home(request):

    return render(request, "index.html")

def about_us(request):
    teachers=Profile.objects.filter(role='teacher')
    return render(request, "about-us.html", {"teachers": teachers,})
def signup(request):
    role = request.GET.get("role") 
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        confirm_password= request.POST.get("confirm_password")
        profile_picture = request.FILES.get("profile_picture")
        if role == "teacher":
            cv = request.FILES.get("cv")
            experience_years = request.POST.get("experience_years")
            linkedin_url = request.POST.get("linkedin_url")
            specializations = request.POST.get("specializations")
            address = request.POST.get("address")
            if not cv or not experience_years  or not specializations or not address or not profile_picture:
                messages.error(request, "All fields are required for teacher registration except linkedin URL.")
                return redirect("/sign-up?role=teacher")
            if cv:
                safe_cv_name = get_valid_filename(cv.name)
                cv_path = default_storage.save(f'temp/cv_{username}_{safe_cv_name}', cv)
        if profile_picture:
          safe_profile_name = get_valid_filename(profile_picture.name)
          profile_pic_path = default_storage.save(f'temp/profile_{username}_{safe_profile_name}', profile_picture)

        if not username or not email or not password or not role:
            messages.error(request, "All fields are required.")
            return redirect("/sign-up")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("/sign-up")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect("/sign-up")
        if Profile.objects.filter(phone=phone).exists():
            messages.error(request,"Phone number already in use.")
            return redirect("/sign-up")
        if not has_mx_record(email.split('@')[1]):
            messages.error(request, "Invalid email domain. Please use a valid email address.")
            return redirect("/sign-up")
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect("/sign-up")
        if not any(char.isdigit() for char in password):
            messages.error(request, "Password must contain at least one digit.")
            return redirect("/sign-up")
        if not any(char.isalpha() for char in password):
            messages.error(request, "Password must contain at least one letter.")
            return redirect("/sign-up")
        if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect("/sign-up")
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("/sign-up")
        otp = str(random.randint(100000, 999999))

# Check profile picture is an image
        if profile_picture:
            profile_type, _ = mimetypes.guess_type(profile_picture.name)
            if not profile_type or not profile_type.startswith('image'):
                messages.error(request, "Profile picture must be an image file.")
                return redirect("/sign-up?role=teacher")
        if role == "teacher":
          if cv:
            cv_type, _ = mimetypes.guess_type(cv.name)
            if cv_type != 'application/pdf':
                messages.error(request, "CV must be a PDF file.")
                return redirect("/sign-up?role=teacher")
        # Check CV is a PDF

       
        if role=="teacher":

             request.session["signup_data"] = {
             "profile_picture":profile_pic_path,
            "username": username,
            "password": password,
            "email": email,
            "phone": phone,
            "role": role,
            "cv":cv_path,
            "experience_years":experience_years,
            "linkedin_url":linkedin_url,
            "specializations":specializations,
            "address":address,
        }
        request.session['otp'] = otp
        request.session['otp_expiry'] = (timezone.now() + datetime.timedelta(minutes=5)).isoformat()
        request.session['otp_attempts'] = 0
        from django.core.mail import send_mail
        send_mail(
            "Your OTP Code",
            f"Your OTP is {otp}",
            "noreply@yourdomain.com",
            [email],
            fail_silently=False
        )
        messages.success(request, f"OTP sent to your {otp} email.")
        return redirect("/verify-otp/")
    if role== "student":
        return render(request, "student/sign_up.html", {"role": role})
    elif role == "teacher":
        return render(request, "teacher/sign_up.html", {"role": role})
    else:
        messages.error(request, "Invalid role selected.")
        # Redirect to a default page or show an error
        return redirect("/chooseRole")
def verify_otp(request):
    if request.method == "POST":
        stored_otp = request.session.get("otp")
        entered_otp = request.POST.get("otp")
        data = request.session.get("signup_data")
        expiry = request.session.get("otp_expiry")
        attempts = request.session.get("otp_attempts", 0)
        if not data or not stored_otp:
            messages.error(request, "Session expired. Please sign up again.")
            return redirect("/sign-up?role=" + data['role'])
        if attempts >= 5:
            messages.error(request, "Too many failed attempts. Try again.")
            return redirect("/sign-up?role=" + data['role'])

        # Check expiry
        if (timezone.now() > datetime.datetime.fromisoformat(expiry)):
            messages.error(request, "OTP expired. Please register again.")
            return redirect("/sign-up?role=" + data['role'])
        if entered_otp == stored_otp:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email']
            )
            user.set_password(data['password'])
            user.save()
            profile_pic_file =default_storage.open(data['profile_picture'], 'rb')
            cv_file = default_storage.open(data['cv'], 'rb')
            profile=Profile.objects.create(user=user, phone=data['phone'],role=data['role'],profile_picture=File(profile_pic_file) if profile_pic_file else None, bio=data.get('bio', ''))
            if data['role'] == "student":
                student = Student.objects.create(profile=profile)
                student.save()
            elif data['role'] == "teacher":
                teacher = Teacher.objects.create(profile=profile,specialization=data['specializations'],cv=File(cv_file),experience_years=data['experience_years'],linkedin_url=data['linkedin_url'] if data.get('linkedin_url') else None,address=data['address'])
                teacher.save()
                admin=User.objects.get(username='admin')
                send_mail(
                    "New Teacher Application",
                    f"New teacher {data['username']} has Applied as teacher in Your site.",
                    from_email="noreply@gmail.com",
                    recipient_list=[admin.email],
                    fail_silently=False,
                )            # Send welcome email
            send_mail(
                "Welcome to our platform",
                "Thank you for signing up!",
                from_email="noreply@yourdomain.com",
                recipient_list=[data['email']],
                fail_silently=False,
                )            # Clear session
            for key in [ 'otp', 'otp_expiry', 'otp_attempts']:
                if key in request.session:
                    del request.session[key]
            del request.session["signup_data"]


            messages.success(request, "Account verified and created!")
            return redirect("/login")

        else:
            request.session['otp_attempts'] = attempts + 1
            messages.error(request, f"Invalid OTP. ")
            return redirect("/verify-otp/")
        # Clear session data


    return render(request, "verify-otp.html")


def resend_otp(request):
    data = request.session.get("signup_data") 
    if not data:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect("/sign-up")

    # Prevent spamming by checking last sent time
    last_sent = request.session.get("otp_last_sent")
    if last_sent:
        last_sent_time = datetime.datetime.fromisoformat(last_sent)
        if (timezone.now() - last_sent_time < datetime.timedelta(seconds=2)):
            messages.error(request, "Please wait before requesting a new OTP.")
            return redirect("/verify-otp")

    # Generate and send new OTP
    new_otp = str(random.randint(100000, 999999))
    request.session["otp"] = new_otp
    request.session["otp_expiry"] = (timezone.now() + datetime.timedelta(minutes=5)).isoformat()
    request.session["otp_last_sent"] = timezone.now().isoformat()
    request.session["otp_attempts"] = 0  # reset attempts

    send_mail(
        subject="Your new OTP",
        message=f"Your new OTP is: {new_otp}",
        from_email="noreply@yourdomain.com",
        recipient_list=[data['email']],

        fail_silently=False,
    )

    messages.success(request, f"A new OTP has been sent to your email."  )
    return redirect("/verify-otp")

def update_profile(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        if profile.role == "teacher":
            teacher = Teacher.objects.get(profile=profile)
        if request.method == "POST":
            # Update bio if provided
            bio = request.POST.get("bio")
            if bio:
                profile.bio = bio
            
            # Update phone if provided
            phone = request.POST.get("phone")
            if phone:
                profile.phone = phone
            
            # Update profile picture if provided
            profile_picture = request.FILES.get("profile_picture")
            if profile_picture:
                profile.profile_picture = profile_picture
            
            # Update other fields if provided
            specialization = request.POST.get("specialization")
            if specialization:
                teacher.specialization = specialization
            
            experience_years = request.POST.get("experience_years")
            if experience_years:
                teacher.experience_years = experience_years
            
            linkedin_url = request.POST.get("linkedin_url")
            if linkedin_url:
                teacher.linkedin_url = linkedin_url
            
            address = request.POST.get("address")
            if address:
                teacher.address = address
            
            # Save the updated profile
            if profile.role == "teacher":
                            teacher.save()
            profile.save()
            messages.success(request, ("Profile updated successfully!"))
            return redirect("/student-dashboard" if profile.role == "student" else "/teacher-dashboard")
        
        return render(request, "update_profile.html", {"profile": profile})
    else:
        messages.error(request, ("You need to log in first."))
        return redirect("/login")


def change_password(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # Authenticate the user with the old password
        user = authenticate(username=request.user.username, password=old_password)

        if user is not None:
            # Check if new passwords match
            if new_password == confirm_password:
                # Update the user's password
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, "Your password has been changed successfully!")
                profile= Profile.objects.get(user=request.user)
                return redirect("/student-dashboard" if profile.role == "student" else "/teacher-dashboard")
            else:
                messages.error(request, "New passwords do not match.")
        else:
            messages.error(request, "Old password is incorrect.")

    return render(request, "change_password.html")

def request_password_reset(request):
    if request.method == "POST":
        email = request.POST.get("email")
        request.session['reset_email'] = email
        try:
            user = User.objects.get(email=email)
            # Generate a unique token for the password reset link
            token = str(random.randint(100000, 999999))
            request.session['reset_token'] = token
            request.session['reset_email'] = email
            request.session['reset_token_expiry'] = (timezone.now() + datetime.timedelta(minutes=15)).isoformat()
            # Send email with the reset link
            send_mail(
                "Password Reset Request",
                f"Your password reset token is: {token}. It is valid for 15 minutes.",
                "noreply@yourdomain.com",
                [email],
                fail_silently=False,
            )
            messages.success(request, "A password reset token has been sent to your email.")
            return redirect("/verify-reset-token")
        except User.DoesNotExist:
            messages.error(request, "No user found with this email address.")
            return redirect("/request-password-reset")
    return render(request, "request_password_reset.html")
def verify_reset_token(request):
    if request.method == "POST":
        entered_token = request.POST.get("token")
        stored_token = request.session.get("reset_token")
        expiry = request.session.get("reset_token_expiry")

        if not stored_token or not expiry:
            messages.error(request, "Session expired. Please request a password reset again.")
            return redirect("/request-password-reset")

        # Check if the token is valid and not expired
        if (timezone.now() > datetime.datetime.fromisoformat(expiry)):
            messages.error(request, "Token expired. Please request a new password reset.")
            return redirect("/request-password-reset")

        if entered_token == stored_token:
            return redirect("/reset-password")
        else:
            messages.error(request, "Invalid token. Please try again.")
            return redirect("/verify-reset-token")

    return render(request, "verify_reset_token.html")
def reset_password(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        email = request.session.get("reset_email")

        if not email:
            messages.error(request, "Session expired. Please request a password reset again.")
            return redirect("/request-password-reset")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("/reset-password")

        # Validate password strength
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect("/reset-password")
        if not any(char.isdigit() for char in new_password):
            messages.error(request, "Password must contain at least one digit.")
            return redirect("/reset-password")
        if not any(char.isalpha() for char in new_password):
            messages.error(request, "Password must contain at least one letter.")
            return redirect("/reset-password")
        if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in new_password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect("/reset-password")

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            # Clear session data
            for key in ['reset_token', 'reset_email', 'reset_token_expiry']:
                if key in request.session:
                    del request.session[key]
            messages.success(request, "Password reset successfully! You can now log in with your new password.")
            return redirect("/login")
        except User.DoesNotExist:
            messages.error(request, "No user found with this email address.")
            return redirect("/request-password-reset")

    return render(request, "reset_password.html")

def login_veiw(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.profile.role == "student":
                login(request, user)
                messages.success(request,"done")
                return HttpResponseRedirect("/student-dashboard")
            elif user.profile.role == "teacher":
                # Check if the teacher is verified
                if not user.profile.teacher.is_verified:
                    messages.error(request, "Your account is not verified yet.")
                    return HttpResponseRedirect("/login")
                login(request, user)
                return HttpResponseRedirect("/teacher-dashboard")

        else:
            messages.error(request,f"Invalid username or password!")

            return HttpResponseRedirect("/login")
    return render(request, "login.html")
def logout_view(request):
    # Perform logout logic here
    logout(request)
    return HttpResponseRedirect("/")





def choose_role(request):
    return render(request, "chooseRole.html")
def contact_us(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        if not name or not email or not message:
            messages.error(request, "All fields are required!")
            return redirect("/contact-us")
        else:
            messages.success(request, "Message sent successfully!")
            return redirect("/")
    return render(request, "contact-us.html")

def teacher_dashboard(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        courses = Courses.objects.filter(teacher__profile=profile)

        if profile.role == "teacher":
            courses = Courses.objects.filter(teacher__profile=profile)
            return render(request, "teacher/dashboard.html", {"courses": courses,
                                                              "total_course":courses.count(),
                                                              "total_students": sum(course.students.count() for course in courses),})
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def teacher_courses(request):
    if request.user.is_authenticated:
        teacher = request.user.profile.teacher
        profile = Profile.objects.get(user=request.user)
        if profile.role == "teacher":
            courses = Courses.objects.filter(teacher=teacher)
            return render(request, "teachercourses.html", {"courses": courses})
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def t_course_detail(request, course_id):    
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        
        if profile.role == "teacher":
            course = Courses.objects.get(id=course_id)
            videos = video.objects.filter(course=course)
            return render(request, "t_course_detail.html", {"course": course, "videos": videos})
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def student_dashboard(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        
        if profile.role == "student":
            courses = Courses.objects.filter(students__profile=profile)
            return render(request, "student/dashboard.html", {"courses": courses,
                                                              "enrolled_courses":courses.count(),})
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def student_courses(request):
    if request.user.is_authenticated:
        student = request.user.profile.student
        profile = Profile.objects.get(user=request.user)
        if profile.role == "student":
            courses = Courses.objects.filter(students=student)
            return render(request, "studentcourses.html", {"courses": courses})
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def courses(request):
    if request.user.is_authenticated:
     if request.user.username == 'admin':
        
        courses = Courses.objects.all()

        return render(request, "courses.html", {
    "courses": courses,
    "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY
})
     else:
        profile = Profile.objects.get(user=request.user)
        if profile.role == "student":
            student = Student.objects.get(profile=profile) 
            enrolled_courses = student.courses.all()
            courses = Courses.objects.exclude(id__in=enrolled_courses.values_list('id', flat=True))
            return render(request, "courses.html", {
    "courses": courses,
    "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY
})
        elif profile.role == "teacher":
            return redirect("/teacher-dashboard/courses")
        else:
                  courses = Courses.objects.all()

        return render(request, "courses.html", {
    "courses": courses,
    "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY
})

    return render(request, "courses.html", {
    "courses": courses,
    "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY
    })
def create_course(request):
    if request.user.is_authenticated:
        teacher = request.user.profile.teacher
        profile = Profile.objects.get(user=request.user)
        if profile.role == "teacher":
            if request.method == "POST":
                name = request.POST.get("name")
                description = request.POST.get("description")
                price = request.POST.get("price")
                thumbnail = request.FILES.get("thumbnail")
                course = Courses.objects.create(name=name, description=description, price=price, teacher=teacher, thumbnail=thumbnail)
                course.save()
                messages.success(request, "Course added successfully!")
                return redirect("/teacher-dashboard")
            return render(request, "create_course.html")
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def update_course(request, course_id):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        if profile.role == "teacher":
            course = Courses.objects.get(id=course_id)
            if request.method == "POST":
                name = request.POST.get("name")
                description = request.POST.get("description")
                price = request.POST.get("price")
                thumbnail = request.FILES.get("thumbnail")
                course.name = name
                course.description = description
                course.price = price
                if thumbnail:
                    course.thumbnail = thumbnail
                course.save()
                messages.success(request, "Course updated successfully!")
                return redirect("/teacher-dashboard")
            return render(request, "update_course.html", {"course": course})
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def add_video(request, course_id):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        if profile.role == "teacher":
            course = Courses.objects.get(id=course_id)
            if request.method == "POST":
                title = request.POST.get("title")
                description = request.POST.get("description")
                file=request.FILES.get("file")
                url = request.POST.get("url")
                video_obj = video.objects.create(title=title, description=description, course=course)
                if file and url:
                    return messages.error(request, "You can only upload either a file or a URL, not both.")
                elif url:
                    video_obj.url = url
                elif file and not url:
                    video_obj.url = None
                    video_obj.file = file
                elif url and not file:
                    video_obj.file = None
                    video_obj.url = url
                video_obj.save()
                messages.success(request, "Video added successfully!")
                return redirect("/teacher-dashboard/course/" + str(course_id)+"/")
            return render(request, "upload_video.html", {"course": course})
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
    # return render(request, "upload_video.html")

def course_details(request, course_id):  
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        
        if profile.role == "student":
            course = Courses.objects.get(id=course_id)
            videos = video.objects.filter(course=course)
            return render(request, "courseDetails.html", {"course": course, "videos": videos})
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def enroll_course(request, course_id):   
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        
        if profile.role == "student":
            course = Courses.objects.get(id=course_id)
            if course.students.filter(profile=profile).exists():
                messages.error(request, "You are already enrolled in this course!")
                return redirect("/student-dashboard")
            course.students.add(profile.student)
            course.save()
            # Send confirmation email
            send_mail(
                "Course Enrollment Confirmation",
                f"You have been successfully enrolled in {course.name}.",
                from_email=" noreply@gmail.com   ",
                recipient_list=[request.user.email],
                fail_silently=False,
            )
            # Send Email to teacher
            send_mail(
                "New Student Enrollment",
                f"{profile.user.username} has enrolled in your course {course.name}.",
                from_email="noreply@gmail.com",
                recipient_list=[course.teacher.profile.user.email],
                fail_silently=False,
            )
            messages.success(request, "Enrolled in course successfully!")
            return redirect("/student-dashboard")
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def delete_course(request, course_id):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        
        if profile.role == "teacher":
            course = Courses.objects.get(id=course_id)
            course.delete()
            messages.success(request, "Course deleted successfully!")
            return redirect("/teacher-dashboard/courses")
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def delete_video(request, video_id,course_id): 
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        
        if profile.role == "teacher":
            video_obj = video.objects.get(id=video_id)
            video_obj.delete()
            messages.success(request, "Video deleted successfully!")
            return redirect("/teacher-dashboard/course/<int:course_id>/")
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
 
def update_video(request, video_id,course_id):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        
        if profile.role == "teacher":
            video_obj = video.objects.get(id=video_id)
            if request.method == "POST":
                title = request.POST.get("title")
                description = request.POST.get("description")
                file=request.FILES.get("file")
                url = request.POST.get("url")
                video_obj.title = title
                video_obj.description = description
                if file and url:
                    return messages.error(request, "You can only upload either a file or a URL, not both.")
                elif url:
                    video_obj.url = url
                elif file and not url:
                    video_obj.url = None
                    video_obj.file = file
                elif url and not file:
                    video_obj.file = None
                    video_obj.url = url
                video_obj.save()
                messages.success(request, "Video updated successfully!")
                return redirect("/teacher-dashboard/courses")
            return render(request, "update_video.html", {"video": video_obj})
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")
def student_course_detail(request, course_id,video_id=None):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        
        if profile.role == "student":
            course = Courses.objects.get(id=course_id)
            videos = video.objects.filter(course=course)
            student = Student.objects.get(profile=profile)

            tracker, created = ProgressTracker.objects.get_or_create(student=student, course=course)

            # Decide which video to play:
            if video_id:
                current_video = get_object_or_404(video, id=video_id, course=course)
            elif tracker.last_video:
                current_video = tracker.last_video
            else:
                current_video = videos.first()

          
            return render(request, "s_course_detail.html", {
                'course': course,
                'videos': videos,
                'first_video': current_video,
                'progress_tracker': tracker, })
        else:
            messages.error(request, "You are not authorized to access this page.")
            return redirect("/")
    else:
        messages.error(request, "You need to log in first.")
        return redirect("/login")


def play_video(request,course_id, video_id):
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in first.")
        return redirect("/login")

    profile = get_object_or_404(Profile, user=request.user)
    
    if profile.role != "student":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/")

    student = get_object_or_404(Student, profile=profile)
    video_obj = get_object_or_404(video, id=video_id)

    tracker, created = ProgressTracker.objects.get_or_create(
        student=student,
        course=video_obj.course  
    )

    tracker.last_video = video_obj
    tracker.watched_videos.add(video_obj)
    total_videos = video.objects.filter(course=video_obj.course).count()
    watched_count = tracker.watched_videos.count()
    tracker.progress = round((watched_count / total_videos) * 100, 2) if total_videos else 0

    tracker.save()
    return redirect('s_course_detail_video', course_id=video_obj.course.id, video_id=video_obj.id)




stripe.api_key = settings.STRIPE_SECRET_KEY
@csrf_exempt
def course_checkout(request, course_id):
    if not request.user.is_authenticated:
        messages=messages.error(request, "You need to log in first.")
        login_url = reverse('login') + f"?next=/checkout/{course_id}/"
        return redirect(login_url, messages=messages)
    course = get_object_or_404(Courses, id=course_id)
    student = get_object_or_404(Student, profile__user=request.user)
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': course.name},
                'unit_amount': int(course.price * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        metadata={
            'course_id': str(course.id),
            'student_id': str(student.id),
        },
        success_url=f"{settings.DOMAIN}/payment-success/?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.DOMAIN}/payment-cancel/",
    )
    return redirect(session.url)  

def payment_success(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    session_id = request.GET.get('session_id')
    if not session_id:
        # handle error or redirect
        return redirect('/')

    session = stripe.checkout.Session.retrieve(session_id, expand=['payment_intent'])
    payment_intent = session.payment_intent

    # Get your metadata to find student and course
    course_id = session.metadata.get('course_id')
    student_id = session.metadata.get('student_id')

    course = get_object_or_404(Courses, id=course_id)
    student = get_object_or_404(Student, id=student_id)

    # Check if payment already exists to avoid duplicates
    payment, created = Payment.objects.get_or_create(
        stripe_payment_intent=payment_intent.id,
        defaults={
            'student': student,
            'course': course,
            'amount': course.price,
            'paid': True,
        }
    )

    if not created:
        payment.paid = True
        payment.save()

    # You can enroll the student in the course here or trigger other logic
    # For example:
    if not course.students.filter(id=student.id).exists():
        course.students.add(student)

    # Render a success template or redirect
    return render(request, 'payment/success.html', {'session': session, 'course': course})

def payment_cancel(request):
    return render(request, 'payment/cancel.html')
