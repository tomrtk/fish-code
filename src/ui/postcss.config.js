const path = require("path");

const options = [
  // jsTree Images
  {
    filter: "**/+(32px.png|40px.png|throbber.gif)",
    url: "copy",
    assetsPath: "../images",
    basePath: path.resolve("node_modules/jstree/dist/themes/default"),
    useHash: true,
  },
  // Bootstrap Icons
  {
    filter: "**/*.+(woff|woff2)",
    url: "copy",
    assetsPath: "../fonts",
    basePath: path.resolve("node_modules/bootstrap-icons/font"),
    useHash: true,
  },
  // Datatables Images
  {
    url: "copy",
    assetsPath: "../images",
    basePath: path.resolve("node_modules/datatables.net-dt/images"),
    useHash: true,
  },
];

module.exports = (ctx) => ({
  plugins: {
    "postcss-import": {},
    "postcss-url": options,
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
