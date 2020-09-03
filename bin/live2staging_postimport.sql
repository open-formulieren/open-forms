UPDATE accounts_user SET email=CONCAT('notify+', REPLACE(email,'@','__at__'), '@maykin.nl'), password='pbkdf2_sha256$12000$pZphUuHkCDke$x8KlvmVInqS1ru9sGZ1tkDStNkMh1xYU1VaG6SHtHMw=';
