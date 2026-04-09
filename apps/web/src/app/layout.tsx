import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

import { ReportProvider } from "@/context/ReportContext";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Whoop Lens — visualize your Whoop data export",
  description:
    "Open-source report generator for Whoop data exports. Not affiliated with WHOOP, Inc.",
};

export const viewport: Viewport = {
  themeColor: "#101518",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} antialiased`}
    >
      <body className="min-h-screen flex flex-col">
        <ReportProvider>
          {children}
        </ReportProvider>
        <SpeedInsights />
        <Analytics />
      </body>
    </html>
  );
}
