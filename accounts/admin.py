from django.contrib import admin
from django.utils.html import format_html

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ["user", "role", "cv_download", "user_is_active"]
	list_filter = ["role", "user__is_active"]

	@admin.display(description="CV")
	def cv_download(self, obj):
		if not obj.cv_file:
			return "-"
		return format_html('<a href="{}" target="_blank">Download CV</a>', obj.cv_file.url)

	@admin.display(boolean=True, description="Active")
	def user_is_active(self, obj):
		return obj.user.is_active
