find ./ -type f -name '*.jpg' -exec sh -c 'cwebp $1 -o "${1%.jpg}.webp"' _ {} \;
find ./ -type f -name '*.jpeg' -exec sh -c 'cwebp $1 -o "${1%.jpeg}.webp"' _ {} \;
find ./ -type f -name '*.png' -exec sh -c 'cwebp $1 -o "${1%.png}.webp"' _ {} \;