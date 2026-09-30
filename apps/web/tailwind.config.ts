import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        onko: {
          teal: "#0F5F5C",
          tealdark: "#0A4543",
          mint: "#E8F4F1",
          line: "#CFE3DE",
          ink: "#17302E",
          sos: "#C8322D",
          amber: "#B7791F",
        },
      },
      fontFamily: { sans: ["var(--font-body)", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
} satisfies Config;
