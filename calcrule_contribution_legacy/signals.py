from core.signals import bind_service_signal
from core.service_signals import ServiceSignalBindType
from calcrule_contribution_legacy.calculation_rule import ContributionPlanCalculationRuleProductModeling


def bind_service_signals():
    bind_service_signal(
        'create_invoice_from_contract',
        adapt_signal_function_to_run_conversion_contract,
        bind_type=ServiceSignalBindType.BEFORE
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
