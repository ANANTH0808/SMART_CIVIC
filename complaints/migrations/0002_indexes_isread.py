from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0001_initial'),
    ]

    operations = [
        # Add is_read field to Notification
        migrations.AddField(
            model_name='notification',
            name='is_read',
            field=models.BooleanField(default=False),
        ),

        # Add default ordering via Meta.ordering (no DB change needed, but
        # we add the indexes which DO require a DB change).

        # Indexes on Complaint
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['user', 'status'], name='complaint_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['status'], name='complaint_status_idx'),
        ),
        migrations.AddIndex(
            model_name='complaint',
            index=models.Index(fields=['-created_at'], name='complaint_created_idx'),
        ),

        # Index on Notification
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='notif_user_isread_idx'),
        ),
    ]
