from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

# Create your views here.

def homepage(request):
    return render(request, 'homepage.html')

def activities(request):
    return render(request, 'activities.html')

# @login_required
# def add_comment(request, event_id):
#     event = get_object_or_404(VolunteerEvent, id=event_id)
#     if request.method == 'POST':
#         content = request.POST.get('content')
#         Comment.objects.create(event=event, user=request.user, content=content)
#     return redirect('event_detail', event_id=event.id)

# @login_required
# def register_event(request, event_id):
#     event = get_object_or_404(VolunteerEvent, id=event_id)
#     event.register_attendee(request.user)
#     return redirect('event_detail', event_id=event.id)

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
    
    