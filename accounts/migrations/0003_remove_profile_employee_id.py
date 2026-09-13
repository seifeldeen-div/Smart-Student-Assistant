from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_profile_instructor_details"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="profile",
            name="employee_id",
        ),
    ]