import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        checkpoint: {
          cyan: "#0891b2",
          "cyan-dim": "#155e75",
        },
      },
      boxShadow: {
        panel: "0 1px 2px 0 rgba(15, 23, 42, 0.04)",
      },
      keyframes: {
        scanline: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(2400%)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
      },
      animation: {
        scanline: "scanline 2.2s linear infinite",
        pulseGlow: "pulseGlow 1.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
