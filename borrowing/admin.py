from django.contrib import admin

from borrowing.models import Borrowing


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = (
        "book",
        "user",
        "expected_return_date",
        "actual_return_date",
    )
    list_filter = ("book", "expected_return_date", "actual_return_date")
    search_fields = ["book__title"]
