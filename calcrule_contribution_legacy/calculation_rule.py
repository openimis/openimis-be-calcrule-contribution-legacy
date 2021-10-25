import json

from .apps import AbsCalculationRule
from .config import CLASS_RULE_PARAM_VALIDATION, \
    DESCRIPTION_CONTRIBUTION_VALUATION, FROM_TO
from core.signals import Signal
from core import datetime
from django.contrib.contenttypes.models import ContentType


class ContributionPlanCalculationRuleProductModeling(AbsCalculationRule):
    version = 1
    uuid = "2aee6d54-eef4-4ee6-1c47-2793cfa5f9a8"
    calculation_rule_name = "payment: fee for service"
    description = DESCRIPTION_CONTRIBUTION_VALUATION
    impacted_class_parameter = CLASS_RULE_PARAM_VALIDATION
    date_valid_from = datetime.datetime(2000, 1, 1)
    date_valid_to = None
    status = "active"
    from_to = FROM_TO

    signal_get_rule_name = Signal(providing_args=[])
    signal_get_rule_details = Signal(providing_args=[])
    signal_get_param = Signal(providing_args=[])
    signal_get_linked_class = Signal(providing_args=[])
    signal_calculate_event = Signal(providing_args=[])
    signal_convert_from_to = Signal(providing_args=[])

    @classmethod
    def ready(cls):
        now = datetime.datetime.now()
        condition_is_valid = (now >= cls.date_valid_from and now <= cls.date_valid_to) \
            if cls.date_valid_to else (now >= cls.date_valid_from and cls.date_valid_to is None)
        if condition_is_valid:
            if cls.status == "active":
                # register signals getParameter to getParameter signal and getLinkedClass ot getLinkedClass signal
                cls.signal_get_rule_name.connect(cls.get_rule_name, dispatch_uid="on_get_rule_name_signal")
                cls.signal_get_rule_details.connect(cls.get_rule_details, dispatch_uid="on_get_rule_details_signal")
                cls.signal_get_param.connect(cls.get_parameters, dispatch_uid="on_get_param_signal")
                cls.signal_get_linked_class.connect(cls.get_linked_class, dispatch_uid="on_get_linked_class_signal")
                cls.signal_calculate_event.connect(cls.run_calculation_rules, dispatch_uid="on_calculate_event_signal")
                cls.signal_convert_from_to.connect(cls.run_convert, dispatch_uid="on_convert_from_to")

    @classmethod
    def active_for_object(cls, instance, context, type='account_receivable', sub_type='contribution'):
        return instance.__class__.__name__ == "ContributionPlan" \
               and context in ["submit"] \
               and cls.check_calculation(instance)

    @classmethod
    def check_calculation(cls, instance):
        pass

    @classmethod
    def calculate(cls, instance, *args):
        pass

    @classmethod
    def get_linked_class(cls, sender, class_name, **kwargs):
        pass

    @classmethod
    def convert(cls, instance, convert_from, convert_to, **kwargs):
        pass
