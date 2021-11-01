const purgecss = require('@fullhuman/postcss-purgecss');
const autoprefixer = require('autoprefixer');

module.exports = {
    map: false,
    plugins: [
        purgecss({
            content: ['./**/*.html'],
            fontFace: true,
            keyframes: true,
            variables: true,
        }),
        autoprefixer()
    ],
}