location /private-media/ {
    internal;
    alias {{ _django_app_docker_volumes.results[1].volume.Mountpoint }};
}
