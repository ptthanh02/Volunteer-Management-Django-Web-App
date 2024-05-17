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
from django.template.loader import render_to_string
from django.db.models import Q
from django.shortcuts import reverse
from .filters import *
from django.db.models import Count, Case, When, IntegerField

@login_required
def join_event(request):
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        event = get_object_or_404(VolunteerEventPost, pk=event_id)

        try:
            user_relation = UserEventRelation.objects.get(
                user=request.user,
                event=event,
                relation_type='attended'
            )
            return JsonResponse({'success': False, 'error': 'Bạn đã tham gia sự kiện này rồi!'})
        except UserEventRelation.DoesNotExist:
            if event.current_participants >= event.max_participants:
                return JsonResponse({'success': False, 'error': 'Sự kiện này đã đủ số người tham gia!'})

            user_relation = UserEventRelation.objects.create(
                user=request.user,
                event=event,
                relation_type='attended'
            )
            event.current_participants += 1
            event.save(update_fields=['current_participants'])

            return JsonResponse({'success': True, 'message': 'Đăng ký tham gia sự kiện thành công!'})
    return JsonResponse({'success': False, 'error': 'Yêu cầu không hợp lệ!'})

@require_POST
@login_required
def like_event_detail(request):
    event_id = request.POST.get('event_id')
    event = VolunteerEventPost.objects.get(id=event_id)
    user = request.user

    relations = UserEventRelation.objects.filter(
        user=user,
        event=event
    )

    liked = False
    if relations.exists():
        relation = relations.first()
        if relation.relation_type == 'liked':
            relation.delete()
            event.likes -= 1
        else:
            relation.relation_type = 'liked'
            relation.save()
            event.likes += 1
            liked = True
    else:
        UserEventRelation.objects.create(
            user=user,
            event=event,
            relation_type='liked'
        )
        event.likes += 1
        liked = True

    event.save()

    return JsonResponse({'success': True, 'likes': event.likes, 'liked': liked})


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(
        VolunteerEventPost.objects.prefetch_related(
            'user_relations',
            'user_relations__user'
        ).annotate(
            likes_count=Count(Case(
                When(user_relations__relation_type='liked', then=1),
                output_field=IntegerField(),
                distinct=True
            )),
            shares_count=Count(Case(
                When(user_relations__relation_type='shared', then=1),
                output_field=IntegerField(),
                distinct=True
            )),
            views_count=Count(Case(
                When(user_relations__relation_type='viewed', then=1),
                output_field=IntegerField(),
                distinct=True
            ))
        ),
        pk=event_id
    )

    if request.user.is_authenticated:
        user_relation, created = UserEventRelation.objects.get_or_create(
            user=request.user,
            event=event,
            relation_type='viewed'
        )

        event.views += 1
        event.save(update_fields=['views'])
        
        try:
            user_relation = event.user_relations.get(
                user=request.user,
                relation_type='liked'
            )
            event.liked = True
        except UserEventRelation.DoesNotExist:
            event.liked = False

        try:
            user_relation = event.user_relations.get(
                user=request.user,
                relation_type='attended'
            )
            event.is_user_attended = True
        except UserEventRelation.DoesNotExist:
            event.is_user_attended = False
    else:
        event.liked = False
        event.is_user_attended = False

    context = {
        'event': event,
    }

    return render(request, 'event_detail.html', context)

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
        # Lọc các sự kiện đã được yêu thích
        liked_event_relations = UserEventRelation.objects.filter(
            user=user, relation_type='liked'
        )
        liked_event_ids = [relation.event.id for relation in liked_event_relations]

        # Lọc các sự kiện đã tham gia
        joined_event_relations = UserEventRelation.objects.filter(
            user=user, relation_type='attended'
        )
        joined_event_ids = [relation.event.id for relation in joined_event_relations]

        # Lọc các sự kiện chưa tham gia
        not_joined_event_ids = list(set(event_posts.values_list('id', flat=True)) - set(joined_event_ids))

        # Đánh dấu các sự kiện đã được yêu thích và đã tham gia
        for event in event_posts:
            event.liked = event.id in liked_event_ids
            event.joined = event.id in joined_event_ids

        # Tạo QuerySet cho các sự kiện đã yêu thích, đã tham gia và chưa tham gia
        liked_events = VolunteerEventPost.objects.filter(id__in=liked_event_ids)
        joined_events = VolunteerEventPost.objects.filter(id__in=joined_event_ids)
        not_joined_events = VolunteerEventPost.objects.filter(id__in=not_joined_event_ids)
    else:
        liked_events = VolunteerEventPost.objects.none()
        joined_events = VolunteerEventPost.objects.none()
        not_joined_events = event_posts

    # Tạo filter cho event_posts
    event_filter = VolunteerEventPostFilter(request.GET, queryset=event_posts)

    context = {
        'event_posts': event_posts,
        'liked_events': liked_events,
        'joined_events': joined_events,
        'not_joined_events': not_joined_events,
        'filter': event_filter,
    }
    return render(request, 'activities.html', context)

def load_events(request):
    filter_type = request.GET.get('filter')
    user = request.user

    # Tạo queryset ban đầu
    event_posts = VolunteerEventPost.objects.all()

    # Áp dụng django-filter
    event_filter = VolunteerEventPostFilter(request.GET, queryset=event_posts)

    # Lọc sự kiện theo filter từ navigation bar
    if filter_type == 'not-joined':
        attended_event_ids = UserEventRelation.objects.filter(
            user=user,
            relation_type='attended'
        ).values_list('event__id', flat=True)
        event_posts = event_filter.qs.exclude(id__in=attended_event_ids)
    elif filter_type == 'joined':
        attended_event_ids = UserEventRelation.objects.filter(
            user=user,
            relation_type='attended'
        ).values_list('event__id', flat=True)
        event_posts = event_filter.qs.filter(id__in=attended_event_ids)
    elif filter_type == 'liked':
        liked_event_ids = UserEventRelation.objects.filter(
            user=user,
            relation_type='liked'
        ).values_list('event__id', flat=True)
        event_posts = event_filter.qs.filter(id__in=liked_event_ids)
    else:
        event_posts = event_filter.qs

    # Đánh dấu sự kiện đã được yêu thích cho người dùng đã đăng nhập
    if user.is_authenticated:
        liked_event_ids = UserEventRelation.objects.filter(
            user=user,
            relation_type='liked'
        ).values_list('event__id', flat=True)
        for event in event_posts:
            event.liked = event.id in liked_event_ids

    html = render_to_string('activities_includes/event_list.html', {'event_posts': event_posts})
    return JsonResponse({'html': html})

def filter_events(request):
    search_query = request.GET.get('search_query', '').strip()
    user = request.user

    if search_query:
        event_posts = VolunteerEventPost.objects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    else:
        event_posts = VolunteerEventPost.objects.all()

    if user.is_authenticated:
        liked_event_relations = UserEventRelation.objects.filter(
            user=user,
            relation_type='liked'
        )
        liked_event_ids = [relation.event.id for relation in liked_event_relations]
        for event in event_posts:
            event.liked = event.id in liked_event_ids

    html = render_to_string('activities_includes/event_list.html', {'event_posts': event_posts})
    return JsonResponse({'html': html})

@require_POST
@login_required
def like_event(request):
    event_id = request.POST.get('event_id')
    event = VolunteerEventPost.objects.get(id=event_id)
    user = request.user

    relations = UserEventRelation.objects.filter(
        user=user,
        event=event
    )
    if relations.exists():
        relation = relations.first()
        if relation.relation_type == 'liked':
            relation.delete()
            event.likes -= 1
            if event.likes < 0:
                event.likes = 0
            liked = False
        else:
            relation.relation_type = 'liked'
            event.likes += 1
            liked = True
    else:
        UserEventRelation.objects.create(
            user=user,
            event=event,
            relation_type='liked'
        )
        event.likes += 1
        if event.likes < 0:
            event.likes = 0
        liked = True

    event.save()

    return JsonResponse({'likes': event.likes, 'liked': liked})

@require_POST
def share_event(request):
    event_id = request.POST.get('event_id')
    share_platform = request.POST.get('share_platform')

    try:
        event = VolunteerEventPost.objects.get(id=event_id)
    except VolunteerEventPost.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)

    event.shares += 1
    event.save()

    share_url = request.build_absolute_uri(reverse('activities')) + f'?event_id={event_id}'

    return JsonResponse({'shares': event.shares, 'share_url': share_url})

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
        
def reset_events_filter(request):
    return redirect('activities')
        
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
    
    