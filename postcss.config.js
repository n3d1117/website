const purgecss = require('@fullhuman/postcss-purgecss')({
    content: ['./hugo_stats.json'],
    defaultExtractor: (content) => {
        let els = JSON.parse(content).htmlElements;
        return els.tags.concat(els.classes, els.ids);
    }
});

const autoprefixer = require("autoprefixer");

module.exports = {
    map: false,
    plugins: [autoprefixer, purgecss]
};