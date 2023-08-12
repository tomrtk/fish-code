// ESLint Config

import js from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier";
import globals from "globals";
import jquery from "eslint-config-jquery";

const config = [
  {
    ignores: ["**/static"],
  },

  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.jquery,
        ...globals.node,
      },
    },
  },

  js.configs.recommended,

  jquery,

  eslintConfigPrettier,
];

export default config;
