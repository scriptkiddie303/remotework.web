from django.conf import settings
from django.conf.urls.static import static
"""firstproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from firstapp import views

urlpatterns = [
    path('admin-panel/', admin.site.urls),
    path('', views.home ,name='home'), 
    path('about-us/', views.about_us ,name='about-us'),
    path('sign-up/', views.signup ,name='sign-up'),
    path('verify-otp/', views.verify_otp, name='verify-otp'),
    path('resend-otp/', views.resend_otp, name='resend-otp'),
    path('login/', views.login_veiw ,name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('courses/', views.courses ,name='courses'),
    path('chooseRole/', views.choose_role ,name='chooseRole'),
    path('student-dashboard/', views.student_dashboard ,name='student-dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard ,name='teacher-dashboard'),
    path('teacher-dashboard/create-course/', views.create_course ,name='create-course'),
    path('teacher-dashboard/courses/<int:course_id>/delete/', views.delete_course, name='delete-course'),
    path('teacher-dashboard/courses/<int:course_id>/edit/', views.update_course, name='edit-course'),
    path('teacher-dashboard/courses/', views.teacher_courses ,name='teacher-courses'),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll-course'),
    # path('unenroll/<int:course_id>/', views.unenrollCourse, name='unenroll-course'),    
    path('teacher-dashboard/course/<int:course_id>/', views.t_course_detail, name='course-detail'),
    path('teacher-dashboard/course/<int:course_id>/add-video/', views.add_video, name='add-video'),
    path('teacher-dashboard/course/<int:course_id>/deletevideo/<int:video_id>', views.delete_video, name='delete-video'),
    path('teacher-dashboard/course/<int:course_id>/editvideo/<int:video_id>', views.update_video, name='edit-video'),
    path('student-dashboard/courses/', views.student_courses ,name='student-courses'),
    path('student-dashboard/courses/<int:course_id>/', views.student_course_detail, name='s_course_detail')
    # path('student-dashboard/course/<int:course_id>/', views.s_course_detail, name='s-course-detail'),
]


if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)