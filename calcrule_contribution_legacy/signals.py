from calculation.services import run_calculation_rules
from core.forms import User
from core.signals import bind_service_signal
from core.service_signals import ServiceSignalBindType
from policy.models import Policy
from calcrule_contribution_legacy.calculation_rule import ContributionPlanCalculationRuleProductModeling


def bind_service_signals():
    bind_service_signal(
        'create_invoice_from_contract',
        adapt_signal_function_to_run_conversion_contract,
        bind_type=ServiceSignalBindType.BEFORE
    )
    bind_service_signal(
        'policy_service.create',
        on_policy_create,
        bind_type=ServiceSignalBindType.AFTER
    )


def on_policy_create(**kwargs):
    policy = kwargs.get('result', None)
    if policy:
        if policy.status in [Policy.STATUS_IDLE, Policy.STATUS_ACTIVE]:
            user = User.objects.filter(i_user__id=policy.audit_user_id).first()
            # run calcrule for Invoice if there is valid rule
            return ContributionPlanCalculationRuleProductModeling.run_calculation_rules(
                sender=policy.__class__.__name__, instance=policy, user=user, context="PolicyCreatedInvoice"
            )


def adapt_signal_function_to_run_conversion_contract(**kwargs):
    # here there is adapter function to adapt signal result
    # to the run_convert function arguments
    passed_argument = kwargs.get('data', None)
    if passed_argument:
        result_conversion = ContributionPlanCalculationRuleProductModeling.run_convert(
            **passed_argument[1]
        )
        return result_conversion
