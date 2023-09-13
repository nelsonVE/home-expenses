from django.utils import timezone


class FilterMixin:
    def get_month(self, request) -> int:
        return int(request.GET.get('month', timezone.now().month))

    def get_year(self, request) -> int:
        return int(request.GET.get('year', timezone.now().year))

    def is_user(self, request) -> bool:
        return bool(request.GET.get('user', False))
