import dataclasses
from typing import Union


@dataclasses.dataclass()
class OgoneFeedbackParams:
    """
    from docs 'Get transaction feedback':

    https://epayments-support.ingenico.com/en/integration-solutions/integrations/hosted-payment-page#eCommerce-get-transaction-feedback
    """

    # we'll always receive these
    NCERROR: str = ""
    PAYID: str = ""
    ORDERID: str = ""
    STATUS: str = ""

    SHASIGN: str = ""

    @classmethod
    def from_dict(cls, value_dict):
        kws = dict()
        # convoluted but param-names are in-consistently cased
        field_names = set(f.name for f in dataclasses.fields(cls))
        for key, value in value_dict.items():
            key = key.upper()
            if key in field_names:
                kws[key] = value
        return cls(**kws)

    def get_dict(self):
        # clean and filter
        normalized = ((k, str(v).strip()) for k, v in dataclasses.asdict(self).items())
        return {k: v for k, v in normalized if v}


@dataclasses.dataclass()
class OgoneRequestParams:
    """
    stripped from docs example form (might not be complete)

    to reproduce login on the backoffice: https://secure.ogone.com/Ncol/Test/Backoffice/
    navigate to tab: 'Configuration' > 'Technical Information' > 'Test Info' >
    follow 'Create a test payment with Ingenico e-Commerce in UTF-8'
    then copy/strip the form at the end of the page, or add new fields from the list

    """

    # required
    PSPID: str  # fill here your PSPID
    ORDERID: Union[int, str]  # fill here your REF
    AMOUNT: int  # fill here your amount * 100
    CURRENCY: str = "EUR"  # fill here your currency
    LANGUAGE: str = "nl_NL"  # fill here your Client language

    # lay out information
    TITLE: str = ""  # fill here your title
    BGCOLOR: str = ""  # fill here your background color
    TXTCOLOR: str = ""  # fill here your text color
    TBLBGCOLOR: str = ""  # fill here your table background color
    TBLTXTCOLOR: str = ""  # fill here your table text color
    BUTTONBGCOLOR: str = ""  # fill here your background button color
    BUTTONTXTCOLOR: str = ""  # fill here your button text color
    FONTTYPE: str = ""  # fill here your font

    LOGO: str = ""  # fill here your logo file name
    # or dynamic template page
    TP: str = ""  # fill here your template page

    # added for responsive display of payment options
    PMLISTTYPE: int = 2

    # post-payment redirection
    ACCEPTURL: str = ""  #
    DECLINEURL: str = ""  #
    EXCEPTIONURL: str = ""  #
    CANCELURL: str = ""  #
    BACKURL: str = ""  #

    # miscellanous
    HOMEURL: str = ""  #
    CATALOGURL: str = ""  #
    CN: str = ""  # fill here your Client name
    EMAIL: str = ""  # fill here your Client email
    PM: str = ""  #
    BRAND: str = ""  #
    OWNERZIP: str = ""  #
    OWNERADDRESS: str = ""  #
    OWNERADDRESS2: str = ""  #
    OWNERADDRESS3: str = ""  #
    SHASIGN: str = ""  # fill here your signature
    ALIAS: str = ""  #
    ALIASUSAGE: str = ""  #
    ALIASOPERATION: str = ""  #
    COM: str = ""  #
    COMPLUS: str = ""  #
    PARAMPLUS: str = ""  #
    USERID: str = ""  #
    CREDITCODE: str = ""  #

    def get_dict(self):
        # clean and filter
        normalized = (
            (k, str(v).strip()) for k, v in dataclasses.asdict(self).items() if v
        )
        return {k: v for k, v in normalized if v}
