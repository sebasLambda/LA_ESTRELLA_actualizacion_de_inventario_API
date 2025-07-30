from django.urls import path
from .views import *

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("create/", CreateUserView.as_view(), name="create_user"),
    path("toggle-status/", ToggleUserStatusView.as_view(), name="toggle_user_status"),
    path("get-user/", GetUserByIdentificationView.as_view(), name="get_user_by_identification"),
    path("update-user/", UpdateUserFieldView.as_view(), name="update_users"),
]
