from django.contrib.contenttypes.models import ContentType
from django.db.models.query import Q

from calcrule_contribution_legacy.apps import AbsCalculationRule
from calcrule_contribution_legacy.config import CLASS_RULE_PARAM_VALIDATION, \
    DESCRIPTION_CONTRIBUTION_VALUATION, FROM_TO
from calcrule_contribution_legacy.converters import PolicyToInvoiceConverter, PolicyToLineItemConverter, \
    ContractToInvoiceConverter, ContractCpdToLineItemConverter

from core.models import User
from core.signals import *
from core import datetime
from policy.models import Policy


class ContributionPlanCalculationRuleProductModeling(AbsCalculationRule):
    version = 1
    uuid = "2aee6d54-eef4-4ee6-1c47-2793cfa5f9a8"
    calculation_rule_name = "CV: legacy"
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
    def active_for_object(cls, instance, context, type="account_receivable", sub_type="contribution"):
        return instance.__class__.__name__ in ["ContributionPlan", "Policy"] \
               and context in ["submit", "PolicyCreatedInvoice", "ContractCreated"] \
               and cls.check_calculation(instance)

    @classmethod
    def check_calculation(cls, instance):
        class_name = instance.__class__.__name__
        match = False
        if class_name == "ABCMeta":
            match = str(cls.uuid) == str(instance.uuid)
        elif class_name == "ContributionPlan":
            match = str(cls.uuid) == str(instance.calculation)
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
        elif class_name == "Policy":
            match = cls.check_calculation(instance.family)
        # for legacy the calculation is valid for all famillies
        elif class_name == "Family":
            match = True
        return match

    @classmethod
    def calculate(cls, instance, **kwargs):
        context = kwargs.get('context', None)
        user = kwargs.get('user', None)
        if user is None:
            user = User.objects.filter(i_user__id=instance.audit_user_id).first()
        class_name = instance.__class__.__name__
        cls.run_convert(instance=instance, convert_to='Invoice', user=user)
        return f"conversion finished {cls.calculation_rule_name}"

    @classmethod
    def get_linked_class(cls, sender, class_name, **kwargs):
        list_class = []
        if class_name != None:
            model_class = ContentType.objects.filter(model__iexact=class_name).first()
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
    @register_service_signal('convert_to_invoice')
    def convert(cls, instance, convert_to, **kwargs):
        # check from signal before if invoice already exist for instance
        results = {}
        signal = REGISTERED_SERVICE_SIGNALS['convert_to_invoice']
        results_check_invoice_exist = signal.signal_results['before'][0][1]
        if results_check_invoice_exist:
            convert_from = instance.__class__.__name__
            if convert_from == "Policy":
                results = cls._convert_policy(instance)
            if convert_from == "Contract":
                ccpd_list = kwargs.get('ccpd_list', None)
                results = cls._convert_contract(instance, ccpd_list=ccpd_list)
            results['user'] = kwargs.get('user', None)
        # after this method signal is sent to invoice module to save invoice data in db
        return results

    @classmethod
    def convert_batch(cls, **kwargs):
        """ function specific for informal sector """
        # TODO Informal sector / from Policy to Invoice: this function will take the all polices
        #  related to the product (all product if not specified)
        #  that have no invoice and were created in the period specified in the specified location if any
        function_arguments = kwargs.get('data')[1]
        date_from = function_arguments.get('from_date', None)
        date_to = function_arguments.get('to_date', None)
        user = function_arguments.get('user', None)
        product = function_arguments.get('product', None)
        policies_covered = Policy.objects.filter(
            Q(start_date__gte=date_from, start_date__lte=date_to, effective_date__isnull=False),
        ).order_by('start_date')
        if product:
            policies_covered = policies_covered.filter(product__id=product)
        # take all policies that have no invoice
        for policy in policies_covered:
            cls.run_convert(instance=policy, convert_to='Invoice', user=user)

    @classmethod
    def _convert_policy(cls, instance):
        invoice = PolicyToInvoiceConverter.to_invoice_obj(policy=instance)
        invoice_line_item = PolicyToLineItemConverter.to_invoice_line_item_obj(policy=instance)
        return {
            'invoice_data': invoice,
            'invoice_data_line': [invoice_line_item],
            'type_conversion': 'policy-invoice'
        }

    @classmethod
    def _convert_contract(cls, instance, **kwargs):
        invoice = ContractToInvoiceConverter.to_invoice_obj(contract=instance)
        ccpd_list = kwargs.get('ccpd_list', None)
        invoice_line_item = []
        if ccpd_list:
            for ccpd in ccpd_list:
                invoice_line_item.append(
                    ContractCpdToLineItemConverter.to_invoice_line_item_obj(contract_cpd=ccpd)
                )
        return {
            'invoice_data': invoice,
            'invoice_data_line': invoice_line_item,
            'type_conversion': 'contract-invoice'
        }
