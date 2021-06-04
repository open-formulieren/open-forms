location /sdk {
    proxy_pass http://127.0.0.1:{{ sdk_port }}/;
}

location /_flower {
    proxy_pass http://localhost:13555;
}

location /private-media/ {
    internal;
    alias {{ _django_app_docker_volumes.results[1].volume.Mountpoint }};
}
