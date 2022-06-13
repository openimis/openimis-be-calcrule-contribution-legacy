from django.contrib.contenttypes.models import ContentType
from invoice.apps import InvoiceConfig
from invoice.models import Invoice


class PolicyToInvoiceConverter(object):

    @classmethod
    def to_invoice_obj(cls, policy):
        invoice = {}
        cls.build_subject(policy, invoice)
        cls.build_thirdparty(policy, invoice)
        cls.build_code(policy, invoice)
        cls.build_date_datas(policy, invoice)
        #cls.build_tax_analysis(invoice)
        cls.build_currency(invoice)
        cls.build_status(invoice)
        return invoice

    @classmethod
    def build_subject(cls, policy, invoice):
        invoice["subject_id"] = policy.family.id
        invoice['subject_type'] = ContentType.objects.get_for_model(policy.family)

    @classmethod
    def build_thirdparty(cls, policy, invoice):
        invoice["thirdparty_id"] = policy.family.head_insuree.id
        invoice['thirdparty_type'] = ContentType.objects.get_for_model(policy.family.head_insuree)

    @classmethod
    def build_code(cls, policy, invoice):
        invoice["code"] = f"" \
            f"IV-{policy.product.code}" \
            f"-{policy.family.head_insuree.chf_id}" \
            f"-{policy.start_date.strftime('%Y-%m')}"

    @classmethod
    def build_date_datas(cls, policy, invoice):
        invoice["date_due"] = policy.effective_date if policy.effective_date else policy.enroll_date
        invoice["date_invoice"] = policy.enroll_date
        invoice["date_valid_from"] = policy.effective_date if policy.effective_date else policy.enroll_date
        invoice["date_valid_to"] = policy.expiry_date

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

    @classmethod
    def build_amounts(cls, line_item, invoice_update):
        invoice_update["amount_net"] = line_item["amount_net"]
        invoice_update["amount_total"] = line_item["amount_total"]
        invoice_update["amount_discount"] = 0 if line_item["discount"] else line_item["discount"]
