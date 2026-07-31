/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "#050505",
        ink: "#0a0a0a",
        chalk: "#f5f5f5",
        snow: "#ffffff",
        ash: {
          100: "#e5e5e5",
          200: "#d4d4d4",
          400: "#a3a3a3",
          500: "#737373",
          600: "#525252",
          700: "#404040",
          800: "#262626",
          900: "#171717",
        },
      },
      fontFamily: {
        display: ["Syne", "system-ui", "sans-serif"],
        sans: ["Figtree", "system-ui", "sans-serif"],
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        blink: {
          "0%, 100%": { opacity: "0.25" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "fade-up": "fadeUp 0.5s ease-out both",
        "fade-up-delay": "fadeUp 0.5s ease-out 0.1s both",
        "fade-up-delay-2": "fadeUp 0.5s ease-out 0.18s both",
        blink: "blink 1.2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
