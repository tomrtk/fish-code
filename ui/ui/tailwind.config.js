module.exports = {
  mode: "jit",
  purge: {
    content: ["./templates/**/*.html", "./projects/templates/**/*.html"],
  },
  theme: {
    extend: {
      colors: {
        "nina-orange": "#E69D4E",
        "nina-teal": "#82C3C9",
      },
    },
  },
  variants: {
    extend: {},
  },
  plugins: [
    require("@tailwindcss/aspect-ratio"),
    require("@tailwindcss/forms"),
  ],
};
