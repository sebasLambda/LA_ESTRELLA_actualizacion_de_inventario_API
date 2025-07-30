from django.contrib import admin
from .models import User

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'identification', 'full_name', 'is_staff', 'is_active')
    search_fields = ('identification', 'full_name')
    list_filter = ('is_staff', 'is_active')