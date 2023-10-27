from rest_framework import viewsets
from book.models import Book
from book.permissions import IsAdminUserOrReadOnly
from book.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing and editing Book instances."""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminUserOrReadOnly]
