# -*- coding: utf-8 -*-
"""
인증 관련 API Views

회원가입, 로그인, 로그아웃, 사용자 정보 조회 등
"""

import logging
import secrets
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import CustomUser

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    회원가입 API
    
    POST /api/auth/register/
    {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "bio": "안녕하세요" (선택)
    }
    """
    try:
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        bio = request.data.get('bio', '')
        
        # 필수 필드 검증
        if not username or not email or not password:
            return Response(
                {'error': '사용자명, 이메일, 비밀번호는 필수입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 사용자명 중복 확인
        if CustomUser.objects.filter(username=username).exists():
            return Response(
                {'error': '이미 사용 중인 사용자명입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 이메일 중복 확인
        if CustomUser.objects.filter(email=email).exists():
            return Response(
                {'error': '이미 사용 중인 이메일입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 비밀번호 유효성 검증
        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {'error': ' '.join(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 사용자 생성
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            bio=bio
        )
        
        # 이메일 인증 토큰 생성
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        user.verification_token_expires_at = timezone.now() + timedelta(days=7)  # 7일 유효
        user.save()
        
        # 이메일 발송 (실제 구현에서는 설정에서 이메일 백엔드 사용)
        try:
            verification_url = f"{request.scheme}://{request.get_host()}/api/auth/verify-email/?token={verification_token}"
            send_mail(
                subject='Loomon AI 이메일 인증',
                message=f'다음 링크를 클릭하여 이메일을 인증해주세요:\n{verification_url}',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@loomon.ai'),
                recipient_list=[email],
                fail_silently=True,  # 이메일 발송 실패해도 회원가입은 성공
            )
            logger.info(f"인증 이메일 발송: {email}")
        except Exception as e:
            logger.warning(f"이메일 발송 실패: {e}")
            # 이메일 발송 실패해도 회원가입은 계속 진행
        
        logger.info(f"새 사용자 등록: {username}")
        
        # 자동 로그인
        login(request, user)
        
        return Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'bio': user.bio,
            'email_verified': user.email_verified,
            'message': '회원가입이 완료되었습니다. 이메일 인증을 완료해주세요.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"회원가입 오류: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    로그인 API
    
    POST /api/auth/login/
    {
        "username": "testuser",
        "password": "securepassword123"
    }
    """
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': '사용자명과 비밀번호를 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 인증
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            return Response(
                {'error': '사용자명 또는 비밀번호가 올바르지 않습니다.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 로그인 처리
        login(request, user)
        
        logger.info(f"사용자 로그인: {username}")
        
        return Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'bio': user.bio,
            'avatar': user.avatar,
            'preferences': user.preferences,
            'email_verified': user.email_verified,
            'message': '로그인 성공'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"로그인 오류: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    로그아웃 API
    
    POST /api/auth/logout/
    """
    try:
        username = request.user.username
        logout(request)
        
        logger.info(f"사용자 로그아웃: {username}")
        
        return Response({
            'message': '로그아웃되었습니다.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"로그아웃 오류: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def current_user_view(request):
    """
    현재 로그인한 사용자 정보 조회 API
    
    GET /api/auth/me/
    
    인증되지 않은 사용자는 null 반환
    """
    try:
        if not request.user.is_authenticated:
            return Response(
                {'message': '인증되지 않은 사용자입니다.'},
                status=status.HTTP_200_OK
            )
        
        user = request.user
        
        return Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'bio': user.bio,
            'avatar': user.avatar,
            'preferences': user.preferences,
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"사용자 정보 조회 오류: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_view(request):
    """
    사용자 정보 업데이트 API
    
    PUT/PATCH /api/auth/me/
    {
        "bio": "새로운 소개",
        "avatar": "https://example.com/avatar.jpg",
        "preferences": {"theme": "dark"}
    }
    """
    try:
        user = request.user
        
        # 업데이트 가능한 필드
        if 'bio' in request.data:
            user.bio = request.data['bio']
        
        if 'avatar' in request.data:
            user.avatar = request.data['avatar']
        
        if 'preferences' in request.data:
            user.preferences.update(request.data['preferences'])
        
        user.save()
        
        logger.info(f"사용자 정보 업데이트: {user.username}")
        
        return Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'bio': user.bio,
            'avatar': user.avatar,
            'preferences': user.preferences,
            'email_verified': user.email_verified,
            'message': '정보가 업데이트되었습니다.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"사용자 정보 업데이트 오류: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email_view(request):
    """
    이메일 인증 API
    
    GET /api/auth/verify-email/?token=VERIFICATION_TOKEN
    """
    try:
        token = request.GET.get('token')
        
        if not token:
            return Response(
                {'error': '인증 토큰이 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CustomUser.objects.get(email_verification_token=token)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': '유효하지 않은 인증 토큰입니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 토큰 만료 확인
        if user.verification_token_expires_at and user.verification_token_expires_at < timezone.now():
            return Response(
                {'error': '인증 토큰이 만료되었습니다. 재발송해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 이미 인증된 경우
        if user.email_verified:
            return Response(
                {'message': '이미 인증된 이메일입니다.'},
                status=status.HTTP_200_OK
            )
        
        # 이메일 인증 완료
        user.email_verified = True
        user.email_verification_token = None
        user.verification_token_expires_at = None
        user.save()
        
        logger.info(f"이메일 인증 완료: {user.email}")
        
        return Response({
            'message': '이메일 인증이 완료되었습니다.',
            'email': user.email
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"이메일 인증 오류: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_verification_view(request):
    """
    인증 이메일 재발송 API
    
    POST /api/auth/resend-verification/
    """
    try:
        user = request.user
        
        # 이미 인증된 경우
        if user.email_verified:
            return Response(
                {'message': '이미 인증된 이메일입니다.'},
                status=status.HTTP_200_OK
            )
        
        # 새 토큰 생성
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        user.verification_token_expires_at = timezone.now() + timedelta(days=7)
        user.save()
        
        # 이메일 발송
        try:
            verification_url = f"{request.scheme}://{request.get_host()}/api/auth/verify-email/?token={verification_token}"
            send_mail(
                subject='Loomon AI 이메일 인증',
                message=f'다음 링크를 클릭하여 이메일을 인증해주세요:\n{verification_url}',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@loomon.ai'),
                recipient_list=[user.email],
                fail_silently=True,
            )
            logger.info(f"인증 이메일 재발송: {user.email}")
        except Exception as e:
            logger.warning(f"이메일 발송 실패: {e}")
            return Response(
                {'error': '이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'message': '인증 이메일이 재발송되었습니다.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"인증 이메일 재발송 오류: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

