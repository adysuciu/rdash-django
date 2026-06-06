from django.views.generic import TemplateView

from dashboard.data import ACTIVITY_ITEMS, DASHBOARD_STATS, SERVER_ROWS, USER_ROWS


class DashboardView(TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "stats": DASHBOARD_STATS,
                "servers": SERVER_ROWS,
                "users": USER_ROWS,
                "activity_items": ACTIVITY_ITEMS,
            }
        )
        return context
