from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail
from ..models import CustomUser
from rest_framework.permissions import AllowAny
from rest_framework import permissions, viewsets, status
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model()

class SendOTPView(APIView):
    """
    View to send OTP to the user.
    """
    permission_classes = [AllowAny]
    http_method_names = ['post']
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = CustomUser.objects.get(email=email)
            otp = user.generate_otp()
            send_mail(
                'Verify your email',
                f'Your OTP is {otp}',
                'reply@example.com',
                [email],
            )
            return Response({"message": "OTP sent successfully."}, status=200)
            
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=400)    
        
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['post']
    
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        
        if not email or not otp:
            return Response({"error": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
            if user.otp == otp:
                user.is_email_verified = True
                user.is_active = True
                user.otp = ''
                user.save()
                return Response({"message": "Email verified successfully."}, status=200)
            else:
                return Response({"error": "Invalid OTP."}, status=400)
            
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=400)
        
        
class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for managing user accounts.
    
    This viewset provides CRUD operations for the User model, using the
    UserSerializer for serialization. Access is restricted to authenticated
    users via the IsAuthenticated permission class.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]