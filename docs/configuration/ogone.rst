.. _configuration_ogone:

===========================
Ingenico Ogone configureren
===========================

Open Formulieren ondersteunt de Ingenico Ogone legacy payment backend (met PSPID).

Om deze te kunnen gebruiken moet er een `Ogone merchant` worden aangemaakt in de Open Formulieren beheer module:

Navigeer in de beheer module via het menu `Configuratie > Ogone merchant` en klik `Ogone merchant toevoegen`:

Voor het **Label** vul je een herkenbare naam in.

Voor de **PSPID** vul je de Ingenico Ogone PSPID in.

Open dan in een andere browser-tab de Ogone backoffice om configuratie gegevens in te stellen en over te nemen.

Navigeer in de Ogone backoffice naar `Configuration > Technical Configuration > Global security parameters` en kies deze waardes:

**Hash algorithm**: SHA-512

**Character encoding**: UTF-8

Configureer in de Open Formulieren Ogone merchant het **Hash algorithm** met dezelfde waarde als in de Ogone backoffice.

Navigeer in de Ogone backoffice naar de tab: `Configuration > Technical Configuration > Data and origin verification`.

Kopieer dan `Checks for e-Commerce > SHA-IN pass phrase` naar onze Ogone merchant **SHA-IN passphrase**.

Navigeer in de Ogone backoffice naar de tab: `Configuration > Technical Configuration > Transaction feedback`

Activeer dan onder `eCommerce` de checkbox `"I would like to receive transaction feedback parameters on the redirection URLs."`

Kopieer dan `All transaction submission modes > Security for request parameters > SHA-OUT pass phrase` naar onze Ogone merchant **SHA-OUT passphrase**.

Kies dan een voorgedefineerde **Ogone endpoint** of vul een custom URL van een proxy in.

Sla nu de Ogone merchant op en kopieer daarna de gegenereerde **Feedback url**.

Vind dan in de Ogone backoffice op dezelfde tab `All transaction submission modes > Security for request parameters > HTTP request for status changes`

- Selecteer `"For each offline status change (payment, cancellation, etc.)."`

- Vul de eerder gekopieerde **Feedback url** in bij `"URL on which the merchant wishes to receive a deferred HTTP request, should the status of a transaction change offline."`

Sla dit op en controleer of de waardes goed zijn opgeslagen.


