from django.db import models


class EndpointType(models.TextChoices):
    beantwoord_vraag = "beantwoord_vraag", "BeantwoordVraag"
    vrije_berichten = "vrije_berichten", "VrijeBerichten"
    ontvang_asynchroon = "ontvang_asynchroon", "OntvangAsynchroon"
