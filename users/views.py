# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from .models import User
from django.contrib.auth.hashers import check_password

class LoginView(APIView):
    def post(self, request):
        identification = request.data.get('identification')
        password = request.data.get('password')

        if not identification or not password:
            return Response({"detail": "Identificación y contraseña son requeridos."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(identification=identification, password=password)

        if user is not None:
            return Response({
                "message": "Login exitoso. Continúa con Twilio.",
                "user_id": user.id,
                "full_name": user.full_name,
                "is_sttaff": "si" if user.is_staff else "no",
            })
        
        return Response({"detail": "Identificación o contraseña incorrectos."}, status=status.HTTP_401_UNAUTHORIZED)

class CreateUserView(APIView):
    def post(self, request):
        data = request.data
        try:
            user = User.objects.create_user(
                identification=data["identification"],
                full_name=data["full_name"],
                password=data["password"],
                is_staff=True if data.get("is_staff") == "si" else False,
            )
            return Response({"message": "Usuario creado", "user_id": user.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ToggleUserStatusView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({"error": "El campo 'user_id' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(identification=user_id)
            user.is_active = not user.is_active
            user.save()
            return Response({"message": f"Usuario {'activado' if user.is_active else 'inactivado'}"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

class UpdateUserFieldView(APIView):
    def post(self, request):
        identification = request.data.get('identification')
        field = request.data.get('field')
        value = request.data.get('value')

        if not identification or not field or value is None:
            return Response({"detail": "Faltan datos obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(identification=identification)
        except User.DoesNotExist:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Verifica que el campo exista en el modelo
        if not hasattr(user, field):
            return Response({"detail": f"El campo '{field}' no existe en el modelo User."}, status=status.HTTP_400_BAD_REQUEST)

        # Si el campo es la contraseña, se debe manejar de manera especial
        if field == 'password':
            # Validar que el valor de la nueva contraseña no esté vacío
            if len(value) < 8:
                return Response({"detail": "La contraseña debe tener al menos 8 caracteres."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Establecer la nueva contraseña de manera segura
            user.set_password(value)
        elif field == 'is_staff':
            value = True if value.lower() == 'si' else False
            setattr(user, field, value)
        else:
            # Actualizar otros campos como antes
            setattr(user, field, value)

        # Guardar los cambios
        user.save()

        return Response({"detail": f"Campo '{field}' actualizado correctamente."}, status=status.HTTP_200_OK)

    
class GetUserByIdentificationView(APIView):
    def post(self, request):
        identification = request.data.get('identification')

        if not identification:
            return Response({"detail": "La identificación es obligatoria."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(identification=identification)
        except User.DoesNotExist:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        user_data = {
            "identification": user.identification,
            "full_name": user.full_name,
            "is_active": "Activo" if user.is_active else "Inactivo",
            "is_staff": user.is_staff,
        }

        return Response(user_data, status=status.HTTP_200_OK)