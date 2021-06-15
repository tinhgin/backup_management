import logging
import sys
import os
import telegram
from .models import Backup, BackupInstance, FSPath, S3Path, TotalBackup
from django.db import connection
from backup_management import env
from operator import itemgetter
import time
import uuid
import fitz


def show_error(e):
    chat_id = env.TELEGRAM_CHAT_ID
    try:
        if env().str('PROXY') == '':
            bot = telegram.Bot(token=env.TELEGRAM_BOT_TOKEN)
        else:
            pp = telegram.utils.request.Request(proxy_url=env.PROXY)
            bot = telegram.Bot(token=env.TELEGRAM_BOT_TOKEN, request=pp)
    except:
        bot = telegram.Bot(token=env.TELEGRAM_BOT_TOKEN)

    logger = logging.getLogger('BACKUP-MANAGEMENT')
    logging.basicConfig(stream=sys.stdout, level=logging.ERROR)

    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    error = str(e) + " - " + str(fname) + " - line: " + str(exc_tb.tb_lineno)
    logger.error(error)
    try:
        bot.sendMessage(chat_id=chat_id, text=error, parse_mode="Markdown")
    except Exception as e:
        logger.error(e)


def get_previous_backup_size(backup_instances, latest_backup):
    try:
        backup_instances_count = backup_instances.count()
        if backup_instances_count <= 1:
            return 0
        date_list = []
        for backup_instance in backup_instances:
            if backup_instance.date != latest_backup:
                date_list.append(backup_instance.date)
        if len(date_list) == 0:
            return 0
        sorted_list = sorted(date_list, reverse=True)
        previous_backup_date = sorted_list[0]
        return backup_instances.filter(date__exact=previous_backup_date)[0].size
    except Exception as e:
        show_error(e)


def get_backup_status(backup_instances, latest_backup, latest_size):
    try:
        if latest_backup == None or latest_size == None:
            return "MISSING"
        from datetime import datetime, timedelta
        previous_backup_size = get_previous_backup_size(backup_instances, latest_backup)
        now = datetime.now().date()
        latest_backup = latest_backup + timedelta(hours=7)
        if latest_backup.date() >= now:
            if latest_size < previous_backup_size and latest_size * 100 / previous_backup_size <= 99:
                return "WARNING (size less than yesterday backup size)"
            return "SUCCESS"
        else:
            return "MISSING"
    except Exception as e:
        show_error(e)


def get_latest_size(backup_instances, latest_backup):
    try:
        if latest_backup == None:
            return None
        else:
            backup_instances_count = backup_instances.count()
            if backup_instances_count == 1:
                return backup_instances.filter(date__exact=latest_backup)[0].size
            else:
                latest_size = backup_instances.filter(date__exact=latest_backup)[0].size
                for backup_instance in backup_instances:
                    if backup_instance.date > backup_instances[0].date:
                        latest_size = backup_instance.size
                return latest_size
    except Exception as e:
        show_error(e)


def get_latest_backup(backup_instances):
    try:
        backup_instances_count = backup_instances.count()
        if backup_instances_count == 0:
            return None
        elif backup_instances_count == 1:
            return backup_instances[0].date
        else:
            latest_backup = backup_instances[0].date
            for backup_instance in backup_instances:
                if backup_instance.date > backup_instances[0].date:
                    latest_backup = backup_instance.date
            return latest_backup
    except Exception as e:
        show_error(e)


def get_backup_count():
    try:
        total_backups = Backup.objects.all().count()
        backups = Backup.objects.all()
        missing_backups = 0
        success_backups = 0
        warning_backups = 0
        for backup in backups:
            backup_instances = BackupInstance.objects.filter(backup__exact=backup.name)
            latest_backup = get_latest_backup(backup_instances)
            latest_size = get_latest_size(backup_instances, latest_backup)
            backup_status = get_backup_status(backup_instances, latest_backup, latest_size)
            if backup_status == "SUCCESS":
                success_backups += 1
            elif backup_status == "MISSING":
                missing_backups += 1
            else:
                warning_backups += 1
        return total_backups, success_backups, missing_backups, warning_backups
    except Exception as e:
        show_error(e)
    connection.close()


def get_backup_list(status):
    try:
        backups = Backup.objects.all()
        backup_list = []
        for backup in backups:
            backup_instances = BackupInstance.objects.filter(backup__exact=backup.name)
            latest_backup = get_latest_backup(backup_instances)
            latest_size = get_latest_size(backup_instances, latest_backup)
            backup_status = get_backup_status(backup_instances, latest_backup, latest_size)
            if backup_status == status or status == "total":
                backup_dict = {}
                backup_dict['name'] = backup.name
                backup_dict['project'] = str(backup.project)
                backup_dict['storage_type'] = backup.storage_type
                backup_dict['latest_backup'] = latest_backup
                backup_dict['latest_size'] = latest_size
                backup_dict['status'] = backup_status
                if backup.storage_type == "fs":
                    fspath = FSPath.objects.filter(fs_path=backup.fs_storage)
                    if fspath.count() == 0:
                        server_ip = None
                    else:
                        server_ip = fspath[0].server_ip
                    backup_dict['serverip_s3bucket'] = server_ip
                    backup_dict['storage_path'] = backup.fs_storage
                if backup.storage_type == "s3":
                    s3path = S3Path.objects.filter(s3_path=backup.s3_storage)
                    if s3path.count() == 0:
                        s3bucket = None
                    else:
                        s3bucket = s3path[0].s3_bucket
                    backup_dict['serverip_s3bucket'] = s3bucket
                    backup_dict['storage_path'] = backup.s3_storage
                backup_list.append(backup_dict)
        sorted_backup_list = sorted(backup_list, key=itemgetter('project'))
        return sorted_backup_list
    except Exception as e:
        show_error(e)
    connection.close()


def get_total_line_chart_label():
    try:
        line_label = {}
        from datetime import datetime
        currentMonth = datetime.today().month
        currentYear = datetime.today().year
        if currentMonth == 12:
            for index in range(1, 12):
                line_label[index] = str(index) + "/" + str(currentYear)
        else:
            month = currentMonth
            for index in range(1, 12):
                if month == 12:
                    month = 1
                else:
                    month += 1
                if month > currentMonth:
                    line_label[index] = str(month) + "/" + str(currentYear - 1)
                else:
                    line_label[index] = str(month) + "/" + str(currentYear)
        line_label[12] = str(currentMonth) + "/" + str(currentYear)
        return line_label
    except Exception as e:
        show_error(e)


def get_total_line_chart_data():
    try:
        line_data = {}

        line_label = get_total_line_chart_label()
        for i in line_label:
            line_label_value_split = line_label[i].split("/")
            month = line_label_value_split[0]
            year = line_label_value_split[1]
            total_backups_month_objects = TotalBackup.objects.filter(date__month=month, date__year=year)
            if total_backups_month_objects.count() > 0:
                date_tmp = total_backups_month_objects[0].date
                line_data[i] = total_backups_month_objects[0].total
                for j in total_backups_month_objects:
                    if j.date > date_tmp:
                        line_data[i] = j.total
                        date_tmp = j.date
        return line_data
    except Exception as e:
        show_error(e)
    connection.close()


def update_total_backups():
    try:
        current_total = get_backup_count()[0]
        from datetime import datetime
        TotalBackup.objects.update_or_create(date=datetime.now().date(), defaults={'total': current_total})
    except Exception as e:
        show_error(e)
    connection.close()


def get_total_pie_chart_data():
    try:
        pie_data = {}
        pie_data['s3'] = 0
        pie_data['fs'] = 0
        backup_list = get_backup_list("total")
        for i in backup_list:
            if i['storage_type'] == 's3':
                pie_data['s3'] += 1
            else:
                pie_data['fs'] += 1
        return pie_data
    except Exception as e:
        show_error(e)


def get_storage_type_size():
    try:
        size_s3 = {}
        size_fs = {}
        size_s3['size'] = 0
        size_fs['size'] = 0

        backups = Backup.objects.all()
        for i in backups:
            backup_instances = BackupInstance.objects.filter(backup__exact=i.name)
            for j in backup_instances:
                if j.size != None:
                    if i.storage_type == "fs":
                        size_fs['size'] += j.size
                    if i.storage_type == "s3":
                        size_s3['size'] += j.size

        total_size = size_s3['size'] + size_fs['size']
        if total_size == 0:
            size_s3['percent'] = 0
            size_fs['percent'] = 0
        else:
            size_s3['percent'] = size_s3['size'] * 100 / total_size
            size_fs['percent'] = size_fs['size'] * 100 / total_size
        return total_size, size_s3, size_fs
    except Exception as e:
        show_error(e)
    connection.close()


def get_size_unit(size):
    if size < 1000:
        return "bytes"
    elif size < 1000000:
        return "KB"
    elif size < 1000000000:
        return "MB"
    elif size < 1000000000000:
        return "GB"
    else:
        return "TB"


def send_mail():
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import get_template
    from datetime import date

    htmly = get_template('email.html')
    color = {}
    color['total'] = "#0d6efd"
    color['success'] = "#198754"
    color['missing'] = "#dc3545"
    color['warning'] = "#ffc107"
    viewer_pw = env.VIEWER_PASS
    backup_list = get_backup_list("total")

    total_backups, success_backups, missing_backups, warning_backups = get_backup_count()
    d = {'color': color, 'total_backups': total_backups, 'missing_backups': missing_backups,
         'success_backups': success_backups, 'warning_backups': warning_backups,
         'backups': backup_list, 'viewer_pw': viewer_pw}

    try:
        subject = "Backup Report - " + str(date.today())
        from_email = env.DEFAULT_FROM_EMAIL
        to = env.MAIL_TO
        html_content = htmly.render(d)
        msg = EmailMultiAlternatives(subject=subject, from_email=from_email, to=to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        show_error(e)


def generate_report():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        d = webdriver.Chrome('chromedriver', chrome_options=chrome_options)

        file_name = "reports/" + str(uuid.uuid4())

        d.get('http://127.0.0.1:8000/accounts/login/?next=/backup/report/webpage')
        WebDriverWait(d, 10).until(EC.element_to_be_clickable((By.NAME, 'submit')))

        username = d.find_element_by_id("exampleInputEmail")
        password = d.find_element_by_id("exampleInputPassword")

        username.send_keys("viewer")
        password.send_keys(env.VIEWER_PASS)

        d.find_element_by_name("submit").click()

        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="container-fluid"]')))

        # the element with longest height on page
        ele = d.find_element("xpath", '//div[@class="container-fluid"]')
        total_height = ele.size["height"] + 0

        d.set_window_size(1500, total_height)  # the trick
        time.sleep(1)
        d.save_screenshot(file_name + ".png")
        # d.execute_script('window.print();')

        doc = fitz.open()  # PDF with the pictures
        img = fitz.open(file_name + ".png")  # open pic as document
        rect = img[0].rect  # pic dimension
        pdfbytes = img.convertToPDF()  # make a PDF stream
        img.close()  # no longer needed
        imgPDF = fitz.open("pdf", pdfbytes)  # open stream as PDF
        page = doc.newPage(width=rect.width,  # new page with ...
                           height=rect.height)  # pic dimension
        page.showPDFpage(rect, imgPDF, 0)
        # image fills the page
        doc.save(file_name + ".pdf")
        d.close()

        return file_name
    except Exception as e:
        show_error(e)
        return None
