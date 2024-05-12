from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import VolunteerEventPost, UserEventRelation
from datetime import datetime
from django.utils import timezone

User = get_user_model()

class UserEventRelationTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        event_data = {
            'name': 'Sự kiện tình nguyện mẫu',
            'start_date': timezone.now() + timezone.timedelta(days=2),
            'end_date': timezone.now() + timezone.timedelta(days=5),
            'location': 'Hà Nội',
            'description': 'Đây là mô tả sự kiện tình nguyện mẫu.',
            'hours': 5,
            'max_participants': 20,
            'organizer': self.user,
            'category': 'community',
        }

        self.event = VolunteerEventPost.objects.create(**event_data)

    def test_user_viewed_event(self):
        # Tạo mối quan hệ "viewed" cho người dùng và sự kiện
        relation = UserEventRelation.objects.create(
            user=self.user,
            event=self.event,
            relation_type='viewed'
        )

        # Kiểm tra xem mối quan hệ đã được tạo thành công
        self.assertTrue(UserEventRelation.objects.filter(
            user=self.user,
            event=self.event,
            relation_type='viewed'
        ).exists())

        # Kiểm tra chi tiết của mối quan hệ
        self.assertEqual(relation.user, self.user)
        self.assertEqual(relation.event, self.event)
        self.assertEqual(relation.relation_type, 'viewed')