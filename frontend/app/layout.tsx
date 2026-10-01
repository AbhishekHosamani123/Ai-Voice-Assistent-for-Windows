import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Voice Agent",
  description: "Real-time voice agent — LiveKit + Groq + ElevenLabs",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      {/* suppressHydrationWarning: browser extensions (e.g. Bitdefender) inject
          attributes into <body> and trigger false hydration mismatches in dev */}
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
