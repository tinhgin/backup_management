from django.shortcuts import render
from .models import Backup, BackupInstance, TotalBackup
from django.contrib.auth.decorators import login_required
from .lib import update_total_backups, get_total_pie_chart_data, get_total_line_chart_data, \
    get_total_line_chart_label, get_backup_count, get_storage_type_size, get_backup_list
from django.http import Http404, HttpResponse, FileResponse
from .lib import get_backup_status, get_latest_backup, get_latest_size, get_size_unit, generate_report
from operator import itemgetter
from datetime import date


@login_required
def index(request):
    total_backups, success_backups, missing_backups, warning_backups = get_backup_count()

    update_total_backups()
    line_label = get_total_line_chart_label()
    line_data = get_total_line_chart_data()
    pie_data = get_total_pie_chart_data()
    total_size, size_s3, size_fs = get_storage_type_size()

    total_backups_by_month = TotalBackup.objects.all()
    max_backup = total_backups_by_month[0].total
    min_backup = max_backup
    for i in TotalBackup.objects.all():
        if i.total > max_backup:
            max_backup = i.total
        if i.total < min_backup:
            min_backup = i.total
    max_tick = max_backup - min_backup + 3

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'index.html',
        context={'total_backups': total_backups, 'missing_backups': missing_backups,
                 'success_backups': success_backups, 'warning_backups': warning_backups, 'line_label': line_label,
                 'line_data': line_data, 'pie_data': pie_data, 'size_s3': size_s3, 'size_fs': size_fs,
                 'total_size': total_size, 'max_tick': max_tick},
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
        context={'warning_backups': warning_backups,
                 'backups': get_backup_list("WARNING (size less than yesterday backup size)")},
    )


@login_required
def backup_detail(request, backup_name):
    if Backup.objects.filter(name__exact=backup_name).exists():
        backup_instances = BackupInstance.objects.filter(backup__exact=backup_name)
        latest_backup = get_latest_backup(backup_instances)
        latest_size = get_latest_size(backup_instances, latest_backup)
        backup_status = get_backup_status(backup_instances, latest_backup, latest_size)
        status_color = {}
        if backup_status == "SUCCESS":
            status_color['name'] = "success"
            status_color['code'] = "1cc88a"
        elif backup_status == "MISSING":
            status_color['name'] = "danger"
            status_color['code'] = "e74a3b"
        else:
            status_color['name'] = "warning"
            status_color['code'] = "f6c23e"

        if len(backup_instances) == 0:
            size_unit = "bytes"
            sorted_backup_instances_list = []
            max_size = 2
            max_tick = 2
        else:
            max_size = latest_size
            for i in backup_instances:
                if i.size > max_size:
                    max_size = i.size
            size_unit = get_size_unit(max_size)
            if size_unit == "bytes":
                max_size = float(max_size)
            elif size_unit == "KB":
                max_size = float(max_size / 1000)
            elif size_unit == "MB":
                max_size = float(max_size / 1000000)
            elif size_unit == "GB":
                max_size = float(max_size / 1000000000)
            elif size_unit == "TB":
                max_size = float(max_size / 1000000000000)

            if max_size < 10:
                max_size = (int(max_size % 10)) + 1
                max_tick = max_size + 1
            else:
                max_tick = 12
                if max_size < 100:
                    if max_size % 10 != 0:
                        max_size = (int(max_size / 10)) * 10 + 10
                else:
                    if max_size % 100 != 0:
                        max_size = (int(max_size / 100)) * 100 + 100
            backup_instances_list = []
            for i in backup_instances:
                backup_instances_dict = {}
                backup_instances_dict['date'] = i.date
                if size_unit == "bytes":
                    backup_instances_dict['size'] = float(i.size)
                elif size_unit == "KB":
                    backup_instances_dict['size'] = float(i.size / 1000)
                elif size_unit == "MB":
                    backup_instances_dict['size'] = float(i.size / 1000000)
                elif size_unit == "GB":
                    backup_instances_dict['size'] = float(i.size / 1000000000)
                elif size_unit == "TB":
                    backup_instances_dict['size'] = float(i.size / 1000000000000)

                backup_instances_list.append(backup_instances_dict)
            sorted_backup_instances_list = sorted(backup_instances_list, key=itemgetter('date'))

        return render(
            request,
            'backup_detail.html',
            context={'backup_name': backup_name, 'backup_status': backup_status,
                     'status_color': status_color, 'size_unit': size_unit,
                     'sorted_backup_instances_list': sorted_backup_instances_list,
                     'max_size': max_size, 'max_tick': max_tick},
        )
    else:
        raise Http404


@login_required
def report_webpage(request):
    total_backups, success_backups, missing_backups, warning_backups = get_backup_count()

    update_total_backups()
    line_label = get_total_line_chart_label()
    line_data = get_total_line_chart_data()
    pie_data = get_total_pie_chart_data()
    total_size, size_s3, size_fs = get_storage_type_size()
    today = date.today()

    total_backups_by_month = TotalBackup.objects.all()
    max_backup = total_backups_by_month[0].total
    min_backup = max_backup
    for i in TotalBackup.objects.all():
        if i.total > max_backup:
            max_backup = i.total
        if i.total < min_backup:
            min_backup = i.total
    max_tick = max_backup - min_backup + 3

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'report.html',
        context={'total_backups': total_backups, 'missing_backups': missing_backups,
                 'success_backups': success_backups, 'warning_backups': warning_backups, 'line_label': line_label,
                 'line_data': line_data, 'pie_data': pie_data, 'size_s3': size_s3, 'size_fs': size_fs,
                 'total_size': total_size, 'backups': get_backup_list("total"), 'today': today, 'max_tick': max_tick},
    )


@login_required
def report_pdf(request):
    file_name = generate_report()
    if file_name == None:
        return HttpResponse(status=500)
    else:
        return FileResponse(open(file_name + '.pdf', 'rb'), content_type='application/pdf')

@login_required
def report_png(request):
    file_name = generate_report()
    if file_name == None:
        return HttpResponse(status=500)
    else:
        return FileResponse(open(file_name + '.png', 'rb'), content_type='image/png')
