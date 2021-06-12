from django.shortcuts import render
from .models import Backup
from django.contrib.auth.decorators import login_required
from .lib import show_error, update_total_backups, get_total_pie_chart_data, get_total_line_chart_data, \
    get_total_line_chart_label, get_backup_count, get_storage_type_size, get_backup_list


@login_required
def index(request):
    total_backups, success_backups, missing_backups, warning_backups = get_backup_count()

    update_total_backups()
    line_label = get_total_line_chart_label()
    line_data = get_total_line_chart_data()
    pie_data = get_total_pie_chart_data()
    total_size, size_s3, size_fs = get_storage_type_size()

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'index.html',
        context={'total_backups': total_backups, 'missing_backups': missing_backups,
                 'success_backups': success_backups, 'warning_backups': warning_backups, 'line_label': line_label,
                 'line_data': line_data, 'pie_data': pie_data, 'size_s3': size_s3, 'size_fs': size_fs, 'total_size': total_size},
    )


@login_required
def total_backups(request):
    total_backups = Backup.objects.all().count()

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'total_backups.html',
        context={'total_backups': total_backups, 'backups': get_backup_list("total")},
    )

@login_required
def success_backups(request):
    success_backups = get_backup_count()[1]

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'success_backups.html',
        context={'success_backups': success_backups, 'backups': get_backup_list("SUCCESS")},
    )

@login_required
def missing_backups(request):
    missing_backups = get_backup_count()[2]

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'missing_backups.html',
        context={'missing_backups': missing_backups, 'backups': get_backup_list("MISSING")},
    )

@login_required
def warning_backups(request):
    warning_backups = get_backup_count()[3]

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'warning_backups.html',
        context={'warning_backups': warning_backups, 'backups': get_backup_list("WARNING (size less than yesterday backup size)")},
    )

@login_required
def test(request):
    warning_backups = get_backup_count()[3]

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'backup_instances.html',
        context={'warning_backups': warning_backups, 'backups': get_backup_list("WARNING (size less than yesterday backup size)")},
    )