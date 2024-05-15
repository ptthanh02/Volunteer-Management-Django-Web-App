from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import *
from .forms import *
from django.contrib import messages
from datetime import datetime
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
import re
from django.views.decorators.http import require_POST

def homepage(request):
    upcoming_events = VolunteerEventPost.objects.filter(
        status='planned',
        start_date__gte=timezone.now()
    ).order_by('start_date')[:3]

    for event in upcoming_events:
        event.status_display = event.get_status_display()

    context = {
        'upcoming_events': upcoming_events
    }

    return render(request, 'homepage.html', context)

def activities(request):
    event_posts = VolunteerEventPost.objects.all()
    user = request.user

    if user.is_authenticated:
        user_event_relations = UserEventRelation.objects.filter(user=user, relation_type='liked')
        liked_event_ids = [relation.event.id for relation in user_event_relations]

        for event in event_posts:
            event.liked = event.id in liked_event_ids

    return render(request, 'activities.html', {'event_posts': event_posts})

@require_POST
@login_required
def like_event(request):
    event_id = request.POST.get('event_id')
    event = VolunteerEventPost.objects.get(id=event_id)
    user = request.user

    relation, created = UserEventRelation.objects.get_or_create(
        user=user,
        event=event,
        defaults={'relation_type': 'liked'}
    )

    if created:
        event.likes += 1
        liked = True
    else:
        relation.delete()
        event.likes -= 1
        liked = False

    event.save()

    return JsonResponse({'likes': event.likes, 'liked': liked})

def user_login(request):
    show_login_form = True # to show login form 
    if request.method != 'POST':
        messages.error(request,"Vui lòng đăng nhập hoặc đăng ký để xem thông tin!")
        return render(request, 'homepage.html', {'show_login_form': show_login_form})
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('rememberMe')
        
        if remember_me == 'on':
            request.session.set_expiry(1209600) # remember user account for 14 days
        
        if not username or not password:
            messages.error(request, "Vui lòng nhập tên tài khoản và mật khẩu!")
            return render(request, 'homepage.html', {'show_login_form': show_login_form})
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser == True:
                return redirect('/admin/')
            return activities(request) # redirect to activities page
        else:
            messages.error(request, "Tên tài khoản hoặc mật khẩu không đúng!")
            return render(request, 'homepage.html', {'show_login_form': show_login_form})
        
def user_logout(request):
    logout(request)
    return homepage(request)

def user_register(request):
    show_register_form = True # to show register form
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        name = request.POST.get('name')
        age = request.POST.get('age')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        if not username or not password1 or not name or not age or not email or not phone:
            messages.error(request, "Vui lòng điền đầy đủ thông tin!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
                
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Tên đăng nhập đã tồn tại! Vui lòng chọn tên đăng nhập khác!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        if re.search(r'\d', name):
            messages.error(request, "Tên không hợp lệ!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        age = int(age)
        if age < 0 or age > 100:
            messages.error(request, "Tuổi không hợp lệ!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        if len(password1) < 8:
            messages.error(request, "Mật khẩu phải chứa ít nhất 8 ký tự!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        if not re.search(r'[A-Z]', password1):
            messages.error(request, "Mật khẩu phải chứa ít nhất 1 ký tự viết hoa!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        if not re.search(r'[a-z]', password1):
            messages.error(request, "Mật khẩu phải chứa ít nhất 1 ký tự viết thường!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        if not re.search(r'\d', password1):
            messages.error(request, "Mật khẩu phải chứa ít nhất 1 ký tự số!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        if password1 != password2:
            messages.error(request, "Mật khẩu không trùng khớp!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email đã tồn tại! Vui lòng chọn email khác!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        if not re.match(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', email):
            messages.error(request, "Email không hợp lệ!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        if not re.match(r'^\d{10}$', phone):
            messages.error(request, "Số điện thoại không hợp lệ!")
            return render(request, 'homepage.html', {'show_register_form': show_register_form})
        
        user = CustomUser.objects.create_user(username=username, password=password1, name=name, age=age, email=email, phone=phone)
        user.save()
        register_sucess = True # to show register success message
        show_register_form = False
        messages.success(request, "Đăng ký tài khoản thành công!")
        return render(request, 'homepage.html', {'register_sucess': register_sucess, 'show_register_form': show_register_form})
    else:
        return render(request, 'homepage.html', {'show_register_form': show_register_form})

# for ckeditor-5 image upload
def custom_upload_function(request):
    if request.method == 'POST' and request.FILES['upload']:
        upload_file = request.FILES['upload']
        file_name = default_storage.save(upload_file.name, upload_file)
        file_url = default_storage.url(file_name)
        return JsonResponse({
            'uploaded': True,
            'url': settings.MEDIA_URL + file_name
        })
    return JsonResponse({
        'uploaded': False,
        'error': {
            'message': 'Error message'
        }
    })
    
    