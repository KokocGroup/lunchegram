import uuid
from secrets import token_urlsafe

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from djchoices import DjangoChoices, ChoiceItem
from model_utils.models import TimeStampedModel


class CompanyQuerySet(models.QuerySet):
    def privacy_link(self):
        return self.filter(privacy_mode=Company.Privacy.link)


class Company(TimeStampedModel):
    class Privacy(DjangoChoices):
        link = ChoiceItem()

    name = models.CharField(max_length=255)
    privacy_mode = models.CharField(max_length=10, choices=Privacy.choices)
    invite_token = models.CharField(max_length=50, blank=True, null=True, unique=True)
    employees = models.ManyToManyField(settings.AUTH_USER_MODEL, through='core.Employee', related_name='companies')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_companies')

    objects = CompanyQuerySet.as_manager()

    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')

    def __str__(self):
        return self.name

    @staticmethod
    def generate_invite_token():
        return token_urlsafe(nbytes=32)


class Employee(TimeStampedModel):
    class State(DjangoChoices):
        online = ChoiceItem()
        offline = ChoiceItem()

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=State.choices, default=State.online)

    class Meta:
        verbose_name = _('employee')
        verbose_name_plural = _('employees')
        unique_together = [
            ['company', 'user'],
        ]


class LunchSchedule(TimeStampedModel):
    class Day(DjangoChoices):
        monday = ChoiceItem()
        tuesday = ChoiceItem()
        wednesday = ChoiceItem()
        thursday = ChoiceItem()
        friday = ChoiceItem()
        saturday = ChoiceItem()
        sunday = ChoiceItem()

    company = models.ForeignKey('core.Company', on_delete=models.CASCADE, related_name='lunch_schedules')
    day_of_week = models.CharField(max_length=15, choices=Day.choices)
    confirm_delta = models.PositiveSmallIntegerField(
        default=2, validators=[MaxValueValidator(6)],
        help_text='We will send confirmation request specified number of days before lunch. '
                  'We send all messages around 10:00 AM.')
    confirm_timeout = models.PositiveSmallIntegerField(
        default=24, validators=[MaxValueValidator(6*24)],
        help_text='User will have specified amount of hours to confirm request. '
                  'After that time request will be declined automatically.\n'
                  'At least one day should remain before lunch.')

    class Meta:
        verbose_name = 'lunch schedule'
        verbose_name_plural = 'lunch schedules'
        unique_together = [
            ['company', 'day_of_week'],
        ]

    def __str__(self):
        return self.get_day_of_week_display()


class Lunch(TimeStampedModel):
    schedule = models.ForeignKey(LunchSchedule, on_delete=models.CASCADE, related_name='lunches')
    date = models.DateField()
    confirmations_created_at = models.DateTimeField(blank=True, null=True)
    auto_decline_after = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'lunch'
        verbose_name_plural = 'lunches'
        unique_together = [
            ['schedule', 'date'],
        ]


class ConfirmationRequest(TimeStampedModel):
    class Status(DjangoChoices):
        new = ChoiceItem()
        delivered = ChoiceItem()
        confirmed = ChoiceItem()
        declined = ChoiceItem()
        auto_declined = ChoiceItem()

    lunch = models.ForeignKey(Lunch, on_delete=models.CASCADE, related_name='confirmation_requests')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='confirmation_requests')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.new)

    class Meta:
        verbose_name = 'confirmation request'
        verbose_name_plural = 'confirmation requests'
