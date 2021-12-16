"""
Implement the eHerkenning and EIDAS authentication plugins.

eHerkenning enabled Dutch companies to authenticate as a company, while EIDAS applies
for both companies and individuals. Technically, EIDAS is implemented almost identical
as eHerkenning, so they are bundled into a single package offering both eherkenning and
eidas authentication plugins.

Note that there are also similarities with DigiD
(:mod:`openforms.authentication.contrib.digid`) in the sense that DigiD, eHerkenning
and EIDAS all relay on SAML flows for the authentication.
"""
