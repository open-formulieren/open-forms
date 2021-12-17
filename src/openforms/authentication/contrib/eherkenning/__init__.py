"""
Implement the eHerkenning and eIDAS authentication plugins.

eHerkenning enables Dutch companies to authenticate as a company, while eIDAS applies
for both companies and individuals. Technically, eIDAS is implemented almost identical
as eHerkenning, so they are bundled into a single package offering both eherkenning and
eIDAS authentication plugins.

Note that there are also similarities with DigiD
(:mod:`openforms.authentication.contrib.digid`) in the sense that DigiD, eHerkenning
and eIDAS all relay on SAML flows for the authentication.
"""
