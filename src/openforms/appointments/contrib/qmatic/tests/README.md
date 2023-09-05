# API integration tests

Some of the tests below use VCR with requests and response recorded against a real instance of
Qmatic. For privacy reasons, the real endpoint of this instance is obfuscated. If you need to
re-record the tests, you need access to this or a similar environment. It's probably best to use
`git blame` to find the person having the information.

## Proxy

[mitmproxy](https://github.com/mitmproxy/mitmproxy) was used to obfuscate the recording of the
casettes using the [reverse proxy](https://docs.mitmproxy.org/stable/concepts-modes/#reverse-proxy)
mode:

```bash
mitmdump --mode reverse:$REAL_HOST --ssl-insecure
```

The `--ssl-insecure` option is used when non-public certificate chains are used, as is common with
the Dutch G1 root certificate for private services.
