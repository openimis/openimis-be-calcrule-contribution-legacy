from django.contrib.contenttypes.models import ContentType
from policy.models import Policy


class PolicyToLineItemConverter(object):

    @classmethod
    def to_invoice_line_item_obj(cls, policy):
        invoice_line_item = {}
        cls.build_line_fk(invoice_line_item, policy)
        cls.build_dates(invoice_line_item, policy)
        cls.build_code(invoice_line_item, policy)
        cls.build_description(invoice_line_item, policy)
        cls.build_details(invoice_line_item, policy)
        cls.build_ledger_account(invoice_line_item, policy)
        cls.build_quantity(invoice_line_item)
        cls.build_unit_price(invoice_line_item, policy)
        cls.build_discount(invoice_line_item, policy)
        #cls.build_tax(invoice_line_item)
        cls.build_amounts(invoice_line_item, policy)
        return invoice_line_item

    @classmethod
    def build_line_fk(cls, invoice_line_item, policy):
        invoice_line_item["line_id"] = policy.id
        invoice_line_item['line_type'] = ContentType.objects.get_for_model(policy)

    @classmethod
    def build_dates(cls, invoice_line_item, policy):
        invoice_line_item["date_valid_from"] = policy.effective_date if policy.effective_date else policy.enroll_date
        invoice_line_item["date_valid_to"] = policy.expiry_date

    @classmethod
    def build_code(cls, invoice_line_item, policy):
        invoice_line_item["code"] = policy.product.code

    @classmethod
    def build_description(cls, invoice_line_item, policy):
        invoice_line_item["description"] = policy.product.name

    @classmethod
    def build_details(cls, invoice_line_item, policy):
        details = {"otherName": policy.family.head_insuree.other_names, "name": policy.family.head_insuree.last_name,
                   "gender": policy.family.head_insuree.gender.gender, "dob": f'{policy.family.head_insuree.dob}'}
        invoice_line_item["details"] = details

    @classmethod
    def build_ledger_account(cls, invoice_line_item, policy):
        invoice_line_item["ledger_account"] = policy.product.acc_code_premiums

    @classmethod
    def build_quantity(cls, invoice_line_item):
        invoice_line_item["quantity"] = 1

    @classmethod
    def build_unit_price(cls, invoice_line_item, policy):
        invoice_line_item["unit_price"] = policy.value

    @classmethod
    def build_discount(cls, invoice_line_item, policy):
        if policy.stage == Policy.STAGE_RENEWED:
            invoice_line_item["discount"] = policy.product.renewal_discount_perc \
                if policy.product.renewal_discount_perc else 0

    @classmethod
    def build_tax(cls, invoice_line_item):
        invoice_line_item["tax_rate"] = None
        invoice_line_item["tax_analysis"] = None

    @classmethod
    def build_amounts(cls, invoice_line_item, policy):
        invoice_line_item["amount_net"] = invoice_line_item["quantity"] * invoice_line_item["unit_price"]
        if "discount" in invoice_line_item:
            if invoice_line_item["discount"] > 0:
                invoice_discount = invoice_line_item["amount_net"] * invoice_line_item["discount"]
                invoice_line_item["amount_net"] = invoice_line_item["amount_net"] - invoice_discount
        invoice_line_item["amount_total"] = invoice_line_item["amount_net"]
