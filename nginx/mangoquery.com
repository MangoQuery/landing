# Redirect www to non-www
server {
    listen 80;
    listen 443 ssl;
    server_name www.mangoquery.com;

    ssl_certificate /etc/letsencrypt/live/mangoquery.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mangoquery.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    return 301 https://mangoquery.com$request_uri;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name mangoquery.com;
    return 301 https://mangoquery.com$request_uri;
}

# Main site
server {
    listen 443 ssl;
    server_name mangoquery.com;

    root /var/www/mangoquery.com;
    index index.html;

    ssl_certificate /etc/letsencrypt/live/mangoquery.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mangoquery.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Root URL - serve the language detector page
    location = / {
        try_files /index.html =404;
    }

    # Language-prefixed pages (clean URLs)
    location ~ ^/(en|es|fr|pt|de|nl|zh|ja|ko|ar|he)(/.*)?$ {
        try_files $uri $uri/ $uri/index.html =404;
    }

    # Backward compat: redirect old /docs.html to /en/docs
    location = /docs.html {
        return 301 /en/docs;
    }

    # Backward compat: redirect bare /docs to /en/docs
    location = /docs {
        return 301 /en/docs;
    }

    # Cache static assets
    location ~* \.(png|svg|ico|css|js|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Serve exe as download
    location /downloads/ {
        add_header Content-Disposition "attachment";
        add_header Cache-Control "public, max-age=3600";
    }
}
