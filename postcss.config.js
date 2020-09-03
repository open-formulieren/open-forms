let selectorLintConfig = {
    global: {
        // Simple
        type: true,
        class: true,
        id: false,
        universal: false,
        attribute: false,

        // Pseudo
        pseudo: true,
    },

    local: {
        // Simple
        type: true,
        class: true,
        id: false,
        universal: true,
        attribute: true,

        // Pseudo
        pseudo: true,
    },

    options: {
        excludedFiles: ['admin_overrides.scss'],
    }
};

module.exports = {
    plugins: [
        require('autoprefixer'),
        require('cssnano'),
        require('postcss-selector-lint')(selectorLintConfig)
    ]
};
