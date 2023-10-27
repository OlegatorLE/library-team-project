from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """View for creating a new user."""
    serializer_class = UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating the authenticated user's details."""
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """Retrieve the authenticated user."""
        return self.request.user
