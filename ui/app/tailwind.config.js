module.exports = {
  purge: [],
  darkMode: false,
  theme: {
    extend: {
      colors: {
        "nina-orange": "#E69D4E",
        "nina-teal": "#82C3C9",
      },
    },
  },
  variants: {
    extend: {
      borderWidth: ["hover"],
      display: ["group-hover"],
    },
  },
  plugins: [require("@tailwindcss/forms")],
};
