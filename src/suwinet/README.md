# Why?

WSDLs are here because the endpoints don't serve them and they reference so lots of separate XSDs,
that fetching them from the network is prohibitively slow. In fact, parsing all the WSDLs at once
from the file system proved too slow already.

# Updating them

## The gist

Unpack the new version, and fix the paths in `constants.py`. That should be enough to start using
the new definitions.

## Integrity

Ensuring no forms exist that were using the old definitions is a different thing. Having access to a
test environment that actually serves test data would make this a lot easier. But until that
happens, diff utilities geared towards XML may be an option to study the differences and see if any
operations have different parameter or return types.
