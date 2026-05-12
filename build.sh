# /bin/bash
set -eu

# Build site
hugo -b https://edoardo.fyi/ --minify --gc --timeout 180s

# Run torchlight
npx torchlight
