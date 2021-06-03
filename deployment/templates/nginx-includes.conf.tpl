location /_flower {
    proxy_pass http://localhost:13555;
}

location /private-media/ {
    internal;
    alias {{ _django_app_docker_volumes.results[1].volume.Mountpoint }};
}
