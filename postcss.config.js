const purgecss = require('@fullhuman/postcss-purgecss')({
    content: ['./hugo_stats.json'],
    defaultExtractor: (content) => {
        let els = JSON.parse(content).htmlElements;
        return els.tags.concat(els.classes, els.ids);
    }
});

const autoprefixer = require("autoprefixer")({
    overrideBrowserslist: ["> 0.5% in US", "Safari > 9"]
})

module.exports = {
    map: false,
    plugins: [purgecss, autoprefixer]
};