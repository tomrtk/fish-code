module.exports = {
  purge: [],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {},
  },
  variants: {
    extend: {
      borderWidth: ["hover"],
      display: ["group-hover"],
    },
  },
  plugins: [require("@tailwindcss/forms")],
};
