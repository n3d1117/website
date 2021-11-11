const purgecss = require('@fullhuman/postcss-purgecss');
const autoprefixer = require('autoprefixer');
const cssnano = require('cssnano');

module.exports = {
    map: false,
    plugins: [
        purgecss({
            content: ['./**/*.html'],
            fontFace: true,
            keyframes: true,
            variables: true,
            whitelist: ['blockquote', 'inline-note']
        }),
        autoprefixer(),
        cssnano({preset: 'default'})
    ],
}