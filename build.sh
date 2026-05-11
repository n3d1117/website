# /bin/bash
set -eu

# Build site
hugo -b https://edoardo.fyi/ --minify --gc

# Run torchlight
npx torchlight
