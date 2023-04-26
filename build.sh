# /bin/bash

# Install cwebp
wget -c https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.3.0-linux-x86-64.tar.gz
tar -xvf libwebp-1.3.0-linux-x86-64.tar.gz
export PATH=$PATH:"$(pwd)"/libwebp-1.3.0-linux-x86-64/bin

# Scrape content
python scraper.py

# Build site
hugo -b https://edoardo.fyi/ --minify --gc

# Run torchlight
npx torchlight