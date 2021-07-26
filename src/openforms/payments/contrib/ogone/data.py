import dataclasses
from typing import Union


@dataclasses.dataclass()
class OgoneRequestParams:
    """
    stripped from docs example form (might not be complete)
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
        normalized = ((k, str(v).strip()) for k, v in dataclasses.asdict(self).items())
        return {k: v for k, v in normalized if v}
