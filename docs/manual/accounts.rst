.. _manual_accounts:

==================
Gebruikers beheren
==================

.. note::

   Om gebruikers te kunnen beheren moet je tot de **Functioneel beheerders**
   groep behoren of equivalente permissies hebben. Zie
   :ref:`manual_users_groups` voor groepenbeheer.

.. _manual_users_groups:

Groepen
=======

Een gebruiker kan tot meerdere groepen behoren - de permissies vullen elkaar
dan aan, d.w.z. dat je de gecombineerde set van permissies krijgt van elke
groep.

Een standaard Open Formulieren installatie komt met een aantal standaardgroepen:

**Beheerders**
    Leden van deze groep kunnen de globale configuratie beheren.

**Functioneel beheerders**
    Leden van deze groep kunnen gebruikers beheren.

**Redacteurs**
    Leden van deze groep kunnen alleen formulieren beheren.


.. note::

    **Technische achtergrond**

    Een *groep* is een set van permissies. Een permissie laat een gebruiker toe
    om iets te doen met een object, waarbij een object van alles kan zijn: Een
    formulier, inzending, configuratie, etc. Typisch zijn er vier soorten
    permissies voor elk soort object:

    * objecten lezen
    * objecten aanmaken
    * objecten aanpassen
    * objecten verwijderen

.. _manual_users_add:

Nieuwe gebruiker aanmaken
=========================

.. note::

    U maakt hier een lokaal account aan. Als u gebruik maakt van organisatie
    accounts dan kunt u beter geen lokaal account aanmaken. Deze wordt
    automatisch aangemaakt zodra een gebruiker inlogt met een organisatie
    account, mits dit is :ref:`geconfigureerd <configuration_authentication_oidc>`.


1. Navigeer naar **Accounts** > **Gebruikers**.
2. Klik rechtsboven op **Gebruiker toevoegen**.
3. Vul een **gebruikersnaam** en een **wachtwoord** in.
4. Klik op **Opslaan en opnieuw bewerken** om verdere gegevens in te vullen.
5. U kunt verdere gegevens zelf invullen maar let alstublieft op:

   * **Actief** dient aangevinkt te zijn. Als dit niet is aangevinkt, kan de
     gebruiker niet inloggen.
   * **Stafstatus** dient aangevinkt te zijn. Als dit niet is aangevinkt, kan de
     gebruiker niet inloggen.
   * Selecteer 1 of meerdere **Groepen** en zorg dat de gewenste groepen
     in de rechterkolom worden geplaatst.

6. Klik rechtsonder op **Opslaan** om de gebruiker aan te maken.


.. _manual_restore_2fa:

Tweestapsauthenticatie herstellen
---------------------------------

Als beheerder kunt u de tweestapsauthenticatie van een andere gebruiker opnieuw 
instellen.

1. Navigeer naar **Accounts** > **TOTP devices**.
2. Vink het checkbox aan in de lijst van het betreffende account.
3. Kies bij **Actie** de optie **Verwijder geselecteerde TOTP devices** en klik op de knop **Uitvoeren**.
4. Op de bevestigingspagina klikt u op **Ja, ik weet het zeker**.

De gebruiker van het betreffende account krijgt nu bij inloggen de mogelijkheid
om opnieuw de QR code te scannen.


Gebruikers verwijderen
======================

.. note::

    Het deactiveren van gebruikers schakelt ook het account uit indien het een
    organisatie account betreft.

1. Navigeer naar **Accounts** > **Gebruikers**.
2. Klik op de gewenste gebruiker om te verwijderen.
3. Vink de optie **Actief** uit.
4. Klik rechtsonder op **Opslaan** om de gebruiker te deactiveren.


Definitief verwijderen
----------------------

.. warning::

    U verwijdert met deze stappen een lokaal account. Om historie te behouden
    kunt u het account beter anonimiseren en inactief maken zoals hierboven
    omschreven.

    Het verwijderen van organisatie accounts heeft alleen zin als de gebruiker
    ook geen organsiatie account meer heeft.

    Organisatie accounts zijn te herkennen aan de gebruikersnaam die bestaat
    uit een reeks willekeurige karakters.

1. Navigeer naar **Accounts** > **Gebruikers**.
2. Klik op de gewenste gebruiker om te verwijderen.
3. Klik linksonder op de knop **Verwijderen**.
4. U wordt gevraagd om de actie te bevestingen en ziet ook een overzicht van
   alle gerelateerde objecten die worden mee verwijderd.
5. Klik op **Ja, ik weet het zeker** om de actie te bevestigen.
