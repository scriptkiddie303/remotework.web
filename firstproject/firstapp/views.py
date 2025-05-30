import datetime
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect

from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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

def has_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return len(records) > 0
    except Exception:
        return False

def home(request):

    return render(request, "index.html")

def about_us(request):
    return render(request, "about-us.html")
def signup(request):
    role = request.GET.get("role")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        request.session["signup_data"] = {
            "username": username,
            "password": password,
            "email": email,
            "phone": phone,
            "role": role,
        }
        # Simple validation
        if not username or not email or not password or not role:
            messages.error(request, "All fields are required.")
            return redirect("/sign-up")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("/sign-up")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect("/sign-up")

        import random
        otp = str(random.randint(100000, 999999))

        request.session["signup_data"] = {
            "username": username,
            "password": password,
            "email": email,
            "phone": phone,
            "role": role,
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
        return redirect("/verify-otp")
    return render(request, "sign-up.html",)
def verify_otp(request):
    if request.method == "POST":
        stored_otp = request.session.get("otp")
        entered_otp = request.POST.get("otp")
        data = request.session.get("signup_data")
        expiry = request.session.get("otp_expiry")
        attempts = request.session.get("otp_attempts", 0)
        if not data or not stored_otp:
            messages.error(request, "Session expired. Please sign up again.")
            return redirect("/sign-up")
        if attempts >= 5:
            messages.error(request, "Too many failed attempts. Try again.")
            return redirect("/sign-up")

        # Check expiry
        if (timezone.now() > datetime.datetime.fromisoformat(expiry)):
            messages.error(request, "OTP expired. Please register again.")
            return redirect("/sign-up")
        if entered_otp == stored_otp:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email']
            )
            user.set_password(data['password'])
            user.save()

            profile=Profile.objects.create(user=user, phone=data['phone'],role=data['role'])
            if data['role'] == "student":
                student = Student.objects.create(profile=profile)
                student.save()
            elif data['role'] == "teacher":
                teacher = Teacher.objects.create(profile=profile)
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
        
        if profile.role == "teacher":
            courses = Courses.objects.filter(teacher__profile=profile)
            return render(request, "teacherDash.html", {"courses": courses})
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
            return render(request, "studentDash.html", {"courses": courses})
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
        messages.error(request, "You need to log in first.")
        return redirect("/login")
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
        return JsonResponse({'error': 'Login required'}, status=401)

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

    # Return the session id for frontend to redirect to Stripe checkout
    return JsonResponse({'id': session.id})

def payment_success(request):
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
