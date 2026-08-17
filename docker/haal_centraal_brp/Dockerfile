# Minimal container to get a git binary for applying the HC data patches.
FROM alpine:3.14
RUN apk add --no-cache git
ENTRYPOINT ["/apply_patches.sh"]
