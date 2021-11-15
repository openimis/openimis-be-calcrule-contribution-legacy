from django.contrib.contenttypes.models import ContentType
from invoice.apps import InvoiceConfig
from invoice.models import Invoice


class ContractToInvoiceConverter(object):

    @classmethod
    def to_invoice_obj(cls, contract):
        invoice = {}
        cls.build_subject(contract, invoice)
        cls.build_thirdparty(contract, invoice)
        cls.build_code(contract, invoice)
        cls.build_date_datas(contract, invoice)
        #cls.build_tax_analysis(invoice)
        cls.build_currency(invoice)
        cls.build_status(invoice)
        return invoice

    @classmethod
    def build_subject(cls, contract, invoice):
        invoice["subject_id"] = contract.id
        invoice['subject_type'] = ContentType.objects.get_for_model(contract)

    @classmethod
    def build_thirdparty(cls, contract, invoice):
        invoice["thirdparty_id"] = contract.policy_holder.id
        invoice['thirdparty_type'] = ContentType.objects.get_for_model(contract.policy_holder)

    @classmethod
    def build_code(cls, contract, invoice):
        invoice["code"] = f"IV-{contract.code}"

    @classmethod
    def build_date_datas(cls, contract, invoice):
        invoice["date_due"] = contract.date_payment_due
        invoice["date_invoice"] = contract.date_approved
        invoice["date_valid_from"] = contract.date_valid_from
        invoice["date_valid_to"] = contract.date_valid_to

    @classmethod
    def build_tax_analysis(cls, invoice):
        invoice["tax_analysis"] = None

    @classmethod
    def build_currency(cls, invoice):
        invoice["currency_tp_code"] = InvoiceConfig.default_currency_code
        invoice["currency_code"] = InvoiceConfig.default_currency_code

    @classmethod
    def build_status(cls, invoice):
        invoice["status"] = Invoice.Status.VALIDATED
