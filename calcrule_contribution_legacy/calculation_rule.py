import json

from .apps import AbsCalculationRule
from .config import CLASS_RULE_PARAM_VALIDATION, \
    DESCRIPTION_CONTRIBUTION_VALUATION, FROM_TO
from .converters.policy_to_invoice import PolicyToInvoiceConverter
from core.signals import Signal
from core import datetime
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import Q
from policy.models import Policy
from policy.values import policy_values


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
    type = "account_receivable"
    sub_type = "contribution"

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
    def active_for_object(cls, instance, context, type, sub_type):
        return instance.__class__.__name__ == "ContributionPlan" \
               and context in ["submit"] \
               and cls.check_calculation(instance)

    @classmethod
    def check_calculation(cls, instance):
        class_name = instance.__class__.__name__
        match = False
        if class_name == "ContributionPlan":
            match = cls.uuid == instance.calculation
        elif class_name == "PolicyHolderInsuree":
            match = cls.check_calculation(instance.cpb)
        elif class_name == "ContractDetails":
            match = cls.check_calculation(instance.cpb)
        elif class_name == "ContractContributionPlanDetails":
            match = cls.check_calculation(instance.cp)
        elif class_name == "ContributionPlanBundle":
            for cp in instance.cp:
                if cls.check_calculation(cp):
                    match = True
                    break
        # for legacy the calculation is valid for all famillies
        elif class_name == "Family":
            match = True
        return match

    @classmethod
    def calculate(cls, instance, *args):
        pass

    @classmethod
    def get_linked_class(cls, sender, class_name, **kwargs):
        list_class = []
        if class_name != None:
            model_class = ContentType.objects.filter(model=class_name).first()
            if model_class:
                model_class = model_class.model_class()
                list_class = list_class + \
                             [f.remote_field.model.__name__ for f in model_class._meta.fields
                              if f.get_internal_type() == 'ForeignKey' and f.remote_field.model.__name__ != "User"]
        else:
            list_class.append("Calculation")
        # because we have calculation in ContributionPlan
        #  as uuid - we have to consider this case
        if class_name == "ContributionPlan":
            list_class.append("Calculation")
        # because we have no direct relation in ContributionPlanBundle
        #  to ContributionPlan we have to consider this case
        if class_name == "ContributionPlanBundle":
            list_class.append("ContributionPlan")
        return list_class

    @classmethod
    def convert(cls, instance, convert_from, convert_to, **kwargs):
        if convert_from == "Policy":
            cls._convert_policy(instance, convert_from, convert_to, **kwargs)
        if convert_from == "Contract":
            cls._convert_contract(instance, convert_from, convert_to, **kwargs)

    @classmethod
    def _convert_policy(cls, instance, convert_from, convert_to, **kwargs):
        pass

    @classmethod
    def _convert_contract(cls, instance, convert_from, convert_to, **kwargs):
        pass
