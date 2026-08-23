import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          primary: "#090A0C",
          secondary: "#111318",
        },
        panel: {
          DEFAULT: "#15181D",
          hover: "#1B1F25",
        },
        border: {
          DEFAULT: "#262B33",
        },
        text: {
          primary: "#F5F7FA",
          secondary: "#A5ACB8",
          muted: "#707782",
        },
        accent: {
          primary: "#E3A544",
          "primary-hover": "#F0B65B",
        },
        status: {
          critical: "#D9544D",
          warning: "#D89B3C",
          success: "#5EA876",
          info: "#5F8EC9",
        },
      },
      fontFamily: {
        sans: ["Geist", "Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;

