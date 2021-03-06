const colors = require("tailwindcss/colors");

module.exports = {
  mode: "jit",
  content: {
    content: [
      "./templates/**/*.html",
      "./projects/templates/**/*.html",
      "./src/js/projects.js",
    ],
  },
  theme: {
    extend: {
      colors: {
        greeny: colors.green,
        "nina-orange": "#E69D4E",
        "nina-teal": "#82C3C9",
      },
      spacing: {
        160: "40rem",
      },
    },
  },
  variants: {
    extend: {
      backgroundColor: ["active"],
      opacity: ["disabled"],
    },
  },
  plugins: [
    require("@tailwindcss/aspect-ratio"),
    require("@tailwindcss/forms")({
      strategy: "class",
    }),
  ],
};
