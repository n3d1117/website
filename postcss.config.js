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
            safelist: ['blockquote', 'chroma']
        }),
        autoprefixer(),
        cssnano({preset: 'default'})
    ],
}