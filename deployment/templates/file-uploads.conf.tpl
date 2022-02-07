location = /api/v1/submissions/files/upload {
    client_max_body_size {{ of_max_upload_size|mandatory }};

    # we have to repeat all the proxy directives here from the `location /` block.
    proxy_pass_header Server;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $server_name;
    proxy_set_header X-Scheme $scheme;
    proxy_connect_timeout 300s;
    proxy_read_timeout 300s;

    proxy_set_header Host $http_host;
    proxy_redirect off;
    proxy_pass_request_headers on;
    proxy_pass http://{{ django_app_nginx_prefix }};
}
