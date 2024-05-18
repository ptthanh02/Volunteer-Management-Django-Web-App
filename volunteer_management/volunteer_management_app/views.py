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

# hệ thống khuyến nghị dựa trên nội dung (Content-based Recommendation System).
def get_recommended_events(user):
    user_liked_events = UserEventRelation.objects.filter(
        user=user,
        relation_type='liked'
    ).values_list('event__id', flat=True)

    event_scores = VolunteerEventPost.objects.annotate(
        likes_count=Count('user_relations', filter=Q(user_relations__relation_type='liked')),
        shares_count=Count('user_relations', filter=Q(user_relations__relation_type='shared')),
        views_count=Count('user_relations', filter=Q(user_relations__relation_type='viewed'))
    ).exclude(id__in=user_liked_events)

    # Tính điểm cho mỗi sự kiện dựa trên số lượng lượt yêu thích, chia sẻ, xem
    for event in event_scores:
        event.score = event.likes_count * 0.5 + event.shares_count * 0.3 + event.views_count * 0.2

    # Sắp xếp các sự kiện theo điểm giảm dần
    sorted_events = sorted(event_scores, key=lambda x: x.score, reverse=True)

    return sorted_events

@login_required
def dashboard(request):
    # Lấy số lượng sự kiện theo trạng thái
    event_status_counts = []
    for status, status_label in VolunteerEventPost.STATUS_CHOICES:
        count = VolunteerEventPost.objects.filter(status=status).count()
        event_status_counts.append({
            'status': status,
            'status_display': status_label,
            'count': count
        })
    
    # Lấy số lượng người dùng theo quản trị viên và  người dùng thông thường
    user_status_counts = CustomUser.objects.values('is_superuser').annotate(count=Count('is_superuser'))
    
    # Thêm label cho chart
    user_status_counts = [
        {
            'status': 'Quản trị viên' if item['is_superuser'] else 'Người dùng',
            'count': item['count']
        }
        for item in user_status_counts
    ]
    
    # Lấy số lượng báo cáo sự kiện theo tháng
    report_counts_by_month = EventReport.objects.values('report_date__month').annotate(count=Count('id'))
    report_counts_by_month = [
        {
            'month': item['report_date__month'],
            'count': item['count']
        }
        for item in report_counts_by_month
    ]

    context = {
        'event_status_counts': event_status_counts,
        'user_status_counts': user_status_counts,
        'report_counts_by_month': report_counts_by_month,
    }
    
    return render(request, 'base_includes/dashboard.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            return JsonResponse({'success': True, 'message': 'Mật khẩu đã được đổi thành công.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = PasswordChangeForm(request.user)
    return JsonResponse({'form_html': form.as_p()})

@login_required
def update_profile(request):
    user = request.user

    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Thông tin cá nhân đã được cập nhật thành công.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    form = UpdateProfileForm(instance=user)
    return JsonResponse({'form_html': form.as_p()})


@login_required
def admin_eventreport_change(request, report_id):
    admin_url = reverse('admin:volunteer_management_app_eventreport_change', args=[report_id])
    return redirect(admin_url)

@login_required
def activity_report_detail(request, event_id):
    event = get_object_or_404(VolunteerEventPost, pk=event_id)
    event_reports = EventReport.objects.filter(event=event)
    if event_reports.exists():
        report = event_reports.first()  # Lấy báo cáo đầu tiên
    else:
        report = None
    context = {
        'event': event,
        'report': report  # Thêm report vào context
    }
    return render(request, 'activity_report_detail.html', context)

@login_required
def activity_reports(request):
    if  request.user.is_superuser:
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
    else:
        return redirect('homepage')

def donation(request):
    return render(request, 'donation.html')

@login_required
def join_event(request):
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        event = get_object_or_404(VolunteerEventPost, pk=event_id)
        if event.status != 'planned':
            return JsonResponse({'success': False, 'error': 'Sự kiện không còn mở đăng ký!'})
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
def like_event(request):
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
    liked_count = UserEventRelation.objects.filter(user=user, relation_type='liked').count()
    joined_count = UserEventRelation.objects.filter(user=user, relation_type='attended').count()
    not_joined_count = VolunteerEventPost.objects.exclude(
        id__in=UserEventRelation.objects.filter(user=user, relation_type='attended').values_list('event__id', flat=True)
    ).count()

    return JsonResponse({
        'success': True,
        'likes': event.likes,
        'liked': liked,
        'liked_count': liked_count,
        'joined_count': joined_count,
        'not_joined_count': not_joined_count
    })


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
        
        recommended_events = get_recommended_events(user)
    else:
        liked_events = VolunteerEventPost.objects.none()
        joined_events = VolunteerEventPost.objects.none()
        not_joined_events = event_posts
        recommended_events = []

    # Tạo filter cho event_posts
    event_filter = VolunteerEventPostFilter(request.GET, queryset=event_posts)

    context = {
        'event_posts': event_posts,
        'liked_events': liked_events,
        'joined_events': joined_events,
        'not_joined_events': not_joined_events,
        'filter': event_filter,
        'recommended_events': recommended_events,
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
    
    elif filter_type == 'recommended':    
        if user.is_authenticated:
            event_posts = get_recommended_events(user)
        else:
            event_posts = VolunteerEventPost.objects.none()
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

    # html = render_to_string('activities_includes/event_list.html', {'event_posts': event_posts})
    user_data = {
        'username': request.user.username,
        'is_superuser': request.user.is_superuser,
        # Thêm các thông tin khác về người dùng nếu cần
    } 
    event_reports = EventReport.objects.all()
    if request.user.is_superuser:
        html = render_to_string('activities_includes/event_report_list.html', {'event_posts': event_posts, 'user': user_data, 'event_reports': event_reports})
    else:
        html = render_to_string('activities_includes/event_list.html', {'event_posts': event_posts})
    return JsonResponse({'html': html, 'event_reports': list(event_reports.values())})

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
    
    