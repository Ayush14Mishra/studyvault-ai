import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";

export default [
  { ignores: ["dist"] },
  { files: ["**/*.{js,jsx}"], languageOptions: { globals: globals.browser, parserOptions: { ecmaVersion: "latest", sourceType: "module", ecmaFeatures: { jsx: true } } }, plugins: { "react-hooks": reactHooks }, rules: { ...js.configs.recommended.rules, ...reactHooks.configs.recommended.rules, "no-unused-vars": ["error", { argsIgnorePattern: "^[A-Z_]" }] } },
];
