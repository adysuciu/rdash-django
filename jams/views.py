from django.views.generic import TemplateView

from jams.models import JamStorageSyncState
from jams.services import (
    JamStorageSyncError,
    filter_options,
    filtered_jam_jars,
    jam_storage_is_stale,
    sync_jam_storage,
)


class JamStorageView(TemplateView):
    template_name = "jams/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        error = ""

        if jam_storage_is_stale():
            try:
                sync_jam_storage()
            except JamStorageSyncError as exc:
                error = str(exc)

        filters = self._filters()
        jars = filtered_jam_jars(filters)
        state = JamStorageSyncState.current()

        context.update(
            {
                "jars": jars,
                "filters": filters,
                "options": filter_options(),
                "total_visible": jars.count(),
                "sync_state": state,
                "sync_error": error or state.last_error,
            }
        )
        return context

    def _filters(self) -> dict[str, str]:
        return {
            "type": self.request.GET.get("type", "").strip(),
            "fruit": self.request.GET.get("fruit", "").strip(),
            "year": self.request.GET.get("year", "").strip(),
            "origin": self.request.GET.get("origin", "").strip(),
            "big": self.request.GET.get("big", "").strip(),
            "status": self.request.GET.get("status", "").strip(),
            "date": self.request.GET.get("date", "").strip(),
        }
