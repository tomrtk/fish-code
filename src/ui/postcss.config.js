const path = require("path");

module.exports = (ctx) => ({
  plugins: {
    "postcss-import": {},
    "postcss-url": [
      {
        url: function (asset, dir) {
          return "../images/jstree/" + asset.url;
        },
      },
    ],
    tailwindcss: {},
    "postcss-nesting": {},
    autoprefixer: {},
    cssnano:
      ctx.env === "production"
        ? {
            preset: "default",
          }
        : false,
  },
});
