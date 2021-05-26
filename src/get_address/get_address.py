from get_address.stuf_bg.models import StufBGConfig


def get_person_address(bsn: str):
    return StufBGConfig.get_solo().get_address(bsn)
