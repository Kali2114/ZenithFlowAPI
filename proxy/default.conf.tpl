server {
    listen ${LISTEN_PORT};

    location /static {
        alias /vol/static;
    }

    location / {
        uwsgi_pass           ${APP_HOST}:${APP_PORT};
        include              /etc/nginx/uwsgi_params;
        client_max_body_size 10M;

        uwsgi_buffer_size 64k;
        uwsgi_buffers 4 64k;
        uwsgi_busy_buffers_size 128k;
        uwsgi_max_temp_file_size 0;
    }
}