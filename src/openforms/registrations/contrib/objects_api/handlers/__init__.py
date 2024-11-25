"""
Versioned registration handlers.

The Objects API registration options have multiple possible configuration versions:

* v1 (legacy) - uses Django template strings to produce JSON
* v2 (recommended) - uses explicit mappings of source -> target variables to produce
  structures that can be JSON-serialized

The implementation details vary quite a bit, but they must implement the same top-level
interface called by the plugin, and there are some shared bits of functionality like
handling the file uploads to the Documents API.
"""
