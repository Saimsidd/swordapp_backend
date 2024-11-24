# blog_api/views.py
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import UserSerializer, BlogSerializer
from .models import Blog

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
   try:
       # Extract data from request
       username = request.data.get('email')  # Using email as username
       email = request.data.get('email')
       password = request.data.get('password')
       name = request.data.get('name')

       # Validate data
       if not username or not email or not password:
           return Response(
               {'error': 'Please provide all required fields'},
               status=status.HTTP_400_BAD_REQUEST
           )

       # Check if user already exists
       if User.objects.filter(username=username).exists():
           return Response(
               {'error': 'User with this email already exists'},
               status=status.HTTP_400_BAD_REQUEST
           )

       # Create user
       user = User.objects.create_user(
           username=username,
           email=email,
           password=password
       )
       
       # Set first name if provided
       if name:
           user.first_name = name
           user.save()

       # Serialize and return user data
       serializer = UserSerializer(user)
       return Response({
           'success': True,
           'message': 'User registered successfully',
           'user': serializer.data
       }, status=status.HTTP_201_CREATED)

   except Exception as e:
       return Response(
           {'error': str(e)},
           status=status.HTTP_500_INTERNAL_SERVER_ERROR
       )

class BlogViewSet(viewsets.ModelViewSet):
   serializer_class = BlogSerializer
   permission_classes = [IsAuthenticated]

   def get_queryset(self):
       return Blog.objects.filter(author=self.request.user).order_by('-created_at')

   def create(self, request, *args, **kwargs):
       try:
           serializer = self.get_serializer(
               data={'title': request.data.get('title'), 'content': request.data.get('content')},
               context={'request': request}
           )
           serializer.is_valid(raise_exception=True)
           blog = serializer.save()

           return Response({
               'success': True,
               'message': 'Blog created successfully',
               'blog': self.get_serializer(blog).data
           }, status=status.HTTP_201_CREATED)
       except Exception as e:
           print(f"Error creating blog: {str(e)}")  # Debug print
           return Response({
               'success': False,
               'error': str(e)
           }, status=status.HTTP_400_BAD_REQUEST)

   def list(self, request, *args, **kwargs):
       try:
           queryset = self.get_queryset()
           serializer = self.get_serializer(queryset, many=True)
           return Response({
               'success': True,
               'blogs': serializer.data
           })
       except Exception as e:
           return Response({
               'success': False,
               'error': str(e)
           }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   def update(self, request, *args, **kwargs):
       try:
           instance = self.get_object()
           
           if instance.author != request.user:
               return Response({
                   'success': False,
                   'error': 'You do not have permission to edit this blog'
               }, status=status.HTTP_403_FORBIDDEN)

           serializer = self.get_serializer(
               instance,
               data={'title': request.data.get('title'), 'content': request.data.get('content')},
               partial=True,
               context={'request': request}
           )
           serializer.is_valid(raise_exception=True)
           blog = serializer.save()

           return Response({
               'success': True,
               'message': 'Blog updated successfully',
               'blog': self.get_serializer(blog).data
           })
       except Exception as e:
           return Response({
               'success': False,
               'error': str(e)
           }, status=status.HTTP_400_BAD_REQUEST)

   def destroy(self, request, *args, **kwargs):
       try:
           instance = self.get_object()
           
           if instance.author != request.user:
               return Response({
                   'success': False,
                   'error': 'You do not have permission to delete this blog'
               }, status=status.HTTP_403_FORBIDDEN)

           instance.delete()
           return Response({
               'success': True,
               'message': 'Blog deleted successfully'
           }, status=status.HTTP_200_OK)
       except Exception as e:
           return Response({
               'success': False,
               'error': str(e)
           }, status=status.HTTP_400_BAD_REQUEST)

   @action(detail=True, methods=['GET'])
   def detail(self, request, pk=None):
       try:
           instance = self.get_object()
           serializer = self.get_serializer(instance)
           return Response({
               'success': True,
               'blog': serializer.data
           })
       except Exception as e:
           return Response({
               'success': False,
               'error': str(e)
           }, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
   serializer_class = UserSerializer
   permission_classes = [IsAuthenticated]
   
   def get_queryset(self):
       return User.objects.filter(id=self.request.user.id)

   @action(detail=False, methods=['GET'])
   def me(self, request):
       try:
           serializer = self.get_serializer(request.user)
           return Response({
               'success': True,
               'user': serializer.data
           })
       except Exception as e:
           return Response({
               'success': False,
               'error': str(e)
           }, status=status.HTTP_400_BAD_REQUEST)

   @action(detail=False, methods=['PUT'])
   def update_profile(self, request):
       try:
           user = request.user
           serializer = self.get_serializer(user, data=request.data, partial=True)
           serializer.is_valid(raise_exception=True)
           serializer.save()
           
           return Response({
               'success': True,
               'message': 'Profile updated successfully',
               'user': serializer.data
           })
       except Exception as e:
           return Response({
               'success': False,
               'error': str(e)
           }, status=status.HTTP_400_BAD_REQUEST)