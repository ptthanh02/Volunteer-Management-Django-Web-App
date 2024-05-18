import django_filters
from .models import *

class VolunteerEventPostFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(choices=VolunteerEventPost.CATEGORY_CHOICES)
    status = django_filters.ChoiceFilter(choices=VolunteerEventPost.STATUS_CHOICES)

    class Meta:
        model = VolunteerEventPost
        fields = ['category', 'status']