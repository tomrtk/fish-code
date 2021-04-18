const path = require("path");

const urlOptions = [
  {
    basePath: path.resolve(__dirname, "node_modules/jstree/src/themes/default"),
    url: "copy",
    assetsPath: path.resolve(__dirname, "static/dist/images"),
    useHast: true,
  },
];

module.exports = (ctx) => ({
  plugins: {
    "postcss-import": {},
    "postcss-url": urlOptions,
    tailwindcss: {},
    autoprefixer: {},
    cssnano:
      ctx.env === "production"
        ? {
            preset: "default",
          }
        : false,
  },
});
