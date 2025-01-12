import logging

import celery
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as __
from telebot.apihelper import ApiException

from accounts.models import User
from core.models import Company, Employee, LunchGroup, Lunch, LunchGroupMember
from core.pair_matcher import MaximumWeightGraphMatcher
from lunchegram import celery_app, bot
from core.utils import kokoc_users_sync


@celery_app.task
def run_everything():
    kokoc_users_sync()
    create_lunch_groups.delay()


@celery_app.task
def create_lunch_groups():
    for company in Company.objects.lunches_enabled():
        employees = Employee.objects.filter(company=company, state=Employee.State.online)
        check_employee_tasks = [check_employee_in_telegram.si(pk) for pk in employees.values_list('pk', flat=True)]
        job = celery.group(check_employee_tasks) | create_lunch_groups_for_company.si(company.pk)
        job.apply_async()


@celery_app.task
def check_employee_in_telegram(employee_id):
    employee = Employee.objects.select_related('user').get(pk=employee_id)
    if employee.user.telegram_account is None:
        employee.state = Employee.State.offline
        employee.save()
        return
    try:
        bot.send_message(
            employee.user.telegram_account.uid,
            __("We have started to look for a perfect lunch partner for you! "
               "Soon you will get link to your partner's account.\n\n"
               "_You received this message because we make sure all participants still available._"),
            parse_mode='Markdown',
        )
    except ApiException as e:
        if e.result.status_code == 403 and b'bot was blocked by the user' in e.result.content:
            employee.state = Employee.State.offline
            employee.save()
            logging.info(f'User `{employee.user}` as employee of company `{employee.company} was switched offline`')
        else:
            logging.error(f'{e}')


@celery_app.task
def create_lunch_groups_for_company(company_id):
    tasks = []

    with transaction.atomic():
        company = Company.objects.get(pk=company_id)
        lunch = Lunch.objects.create(company=company, date=timezone.localdate())
        employees = Employee.objects.filter(company=company, state=Employee.State.online)
        matcher = MaximumWeightGraphMatcher()
        groups = matcher.match(company, employees)
        for group in groups:
            lunch_group = LunchGroup.objects.create(lunch=lunch)
            for employee in group:
                member = LunchGroupMember.objects.create(lunch_group=lunch_group, employee=employee)
                tasks.append(notify_lunch_group_member.s(member.pk))

    job = celery.group(tasks)
    job.apply_async()


@celery_app.task
def notify_lunch_group_member(pk):
    member = LunchGroupMember.objects.select_related('employee__user').get(pk=pk)
    if member.is_notified:
        return
    user = member.employee.user
    if user.telegram_account:
        lunch_group = member.lunch_group
        partners = list(LunchGroupMember.objects.filter(lunch_group=lunch_group).exclude(pk=pk))
        if len(partners) == 1:
            partner_employee = partners[0].employee
            # partner_user = partners[0].employee.user
            # message = __('Hello! Your next random lunch partner is here: [{}](tg://user?id={})').format(
            #     partner_user.get_full_name(), partner_user.telegram_account.uid)
            message_html = __('Hello! Your next random lunch partner is here: <a href="tg://user?id={}">{}</a> (@{} - <a href="{}">открыть на портале</a>)').format(
                partner_employee.user.telegram_account.uid, partner_employee.get_full_name(), partner_employee.user.username, partner_employee.get_external_link())
        else:
            partner_employees = (p.employee for p in partners)
            # partner_users = (p.employee.user for p in partners)
            # partner_links = (f'[{u.get_full_name() or u.telegram_account.uid}](tg://user?id={u.telegram_account.uid})' for u in partner_users)
            # message = __('Hello! Your next random lunch partners are here: {}').format(', '.join(partner_links))
            partner_links_html = (
            f'<a href="tg://user?id={e.user.telegram_account.uid}">{e.get_full_name()}</a> (@{e.user.username} - <a href="{e.get_external_link()}">открыть на портале</a>)'
            for e in partner_employees)
            message_html = __('Hello! Your next random lunch partners are here: {}').format(', '.join(partner_links_html))
        (
            send_telegram_message.s(user.pk, message_html, parse_mode='HTML') |
            mark_lunch_group_member_as_notified.s(pk)
        ).apply_async()


@celery_app.task
def mark_lunch_group_member_as_notified(message_id, pk):
    member = LunchGroupMember.objects.get(pk=pk)
    if member.is_notified:
        return
    member.notified_at = timezone.now()
    member.notification_message_id = message_id
    member.save()


@celery_app.task
def send_telegram_message(user_id: int, message: str, parse_mode: str = None) -> int:
    user = User.objects.get(pk=user_id)
    message = bot.send_message(user.telegram_account.uid, message, parse_mode=parse_mode)
    return message.message_id
