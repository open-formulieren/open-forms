.. _mutual_tls:

Dubbelzijdig TLS
================

Het is mogelijk om dubbelzijdig TLS (mutual TLS) te gebruiken om verzoeken naar externe systemen te maken.

Om een service te configureren zodat dubbelzijdig TLS wordt gebruikt, moet de service gekoppeld zijn aan
een client certificaat en een server certificaat.

Certificaten
------------

Certificaten moeten in de Admin geüpload worden:

* Onder **Configuratie** click op **Certificaten**
* Click op **Certificaat toevoegen**:

   * Vul het **label** in
   * Indien u ook een private key wil toevoegen, kies voor **Key-pair** als type, anders **Certificate only**
   * Upload het certificaat en optioneel de bijhorende private key

* Klik op **Opslaan**

Service
-------

Om een certificaat aan een service te koppelen, ga naar **Configuratie** > **Services**.
Klik dan op de service die gekoppeld moet worden aan uw certificaten.

U vindt twee velden:

* **Server certificate**:

   Hiermee verifiëert Open Formulieren het servercertificaat. Als dit veld leeg blijft,
   dan wordt de server-configuratie gebruikt om de lijst van vertrouwde certificaten op
   te halen. Dit wordt ingesteld tijdens de installatie van Open Formulieren door de
   dienstverlener.

* **Client certificate**:

   Het cliëntcertificaat wordt naar de server opgestuurd zodat die de identiteit van
   Open Formulieren kan verifiëren. Als dit veld leeg blijft, dan is dubbelzijdig TLS
   niet geactiveerd.
