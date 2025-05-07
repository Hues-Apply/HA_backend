from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail
from .models import CustomUser

class SendOTPView(APIView):
    """
    View to send OTP to the user.
    """
    def post(self, request):
        email = request.data.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            otp = user.generate_otp()
            send_mail(
                'Verify your email',
                f'Your OTP is {otp}'
                'reply@example.com',
                [email],
            )
            return Response({"message": "OTP sent successfully."}, status=200)
            
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=400)    
        
class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        
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