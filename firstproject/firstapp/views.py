
from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect

from .models import Student

from django.contrib import messages

from django.contrib.auth import logout,authenticate,login 

from django.contrib.auth.models import User
# Create your views here.
def home(request):
    return render(request, "index.html")
def practice(request):
    data={
        "title":"Practice Page",
        'students':[
            {"name":"John","age":20},
            {"name":"Jane","age":22},
            {"name":"Doe","age":23}
        ],
    }
    return render(request, "practice.html",data)
def aboutUs(request):
    return render(request, "about-us.html")
def signup(request):
    string=''
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        students = User.objects.all()
        print(students)
        for student in students:
            if student.email == email:
                messages.error(request,"Account already exists! Please login.")
                return HttpResponseRedirect("/login")
            if student.name==name:
                messages.error(request,"Username already exists! please try a different one.")
                return HttpResponseRedirect("/sign-up")
        if(confirm_password != password):
            messages.error(request,"Password and Confirm Password do not match!")
            return HttpResponseRedirect("/sign-up")
        # if len(password) < 8:
        #     messages.error(request,"Password must be at least 8 characters long!")
        #     return HttpResponseRedirect("/sign-up")
        # if len(name) < 3:
        #     messages.error(request,"Name must be at least 3 characters long!")
        #     return HttpResponseRedirect("/sign-up")
        # if len(name) > 20:
        #     messages.error(request,"Name must be at most 20 characters long!")
        #     return HttpResponseRedirect("/sign-up")
        # if len(password) > 20:
        #     messages.error(request,"Password must be at most 20 characters long!")
        #     return HttpResponseRedirect("/sign-up")
        # if len(email) < 5:
        #     messages.error(request,"Email must be at least 5 characters long!")
        #     return HttpResponseRedirect("/sign-up")
        # if len(email) > 50:   
        #     messages.error(request,"Email must be at most 50 characters long!")
        #     return HttpResponseRedirect("/sign-up")
        # if len(name) > 20:
        #     messages.error(request,"Name must be at most 20 characters long!")
        #     return HttpResponseRedirect("/sign-up")
        # if len(password) > 20:
        #     messages.error(request,"Password must be at most 20 characters long!")
        #     return HttpResponseRedirect("/sign-up")
        student = User(username=name, email=email, password=password)
        student.save()
        return HttpResponseRedirect("/login")

    return render(request, "sign-up.html",)
def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
         user=User.objects.get(email=email)
         print(user)
         print(3)

        # for student in students:
        #     if student.email == email and student.password == password:
         user=Student.authenticate(request, email=user.email, password=password)
        except User.DoesNotExist:
            user = None
        if user is not None:

            messages.success(request,"Login successful!")
            login(request,user)
            return HttpResponseRedirect("/")
        else:
            messages.error(request,"Invalid credentials! Please try again.")
            return HttpResponseRedirect("/login")
    return render(request, "login.html")
def logout_view(request):
    # Perform logout logic here
    logout(request)
    return HttpResponseRedirect("/")