module.exports = (ctx) => ({
  plugins: {
    "postcss-import": {},
    "postcss-url": { url: "inline" },
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
