from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, identification, full_name, password=None, **extra_fields):
        if not identification:
            raise ValueError("La identificación es obligatoria")
        if not full_name:
            raise ValueError("El nombre completo es obligatorio")

        user = self.model(
            identification=identification,
            full_name=full_name,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, identification, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(identification, full_name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    identification = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'identification'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.identification})"
