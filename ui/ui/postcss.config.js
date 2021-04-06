module.exports = (ctx) => ({
  plugins: {
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
