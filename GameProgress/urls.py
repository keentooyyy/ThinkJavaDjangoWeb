from django.urls import path

from GameProgress.views import get_game_progress, update_game_progress, dummy_login_and_test

urlpatterns = [
    path('progress/<int:student_id>/', get_game_progress, name='get_game_progress'),
    path('progress/update/<int:student_id>/', update_game_progress, name='update_game_progress'),
    path('test-dummy/', dummy_login_and_test, name='dummy_login'),
]
