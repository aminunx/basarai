import type { Metadata } from "next";
import localFont from "next/font/local";
import { Instrument_Serif, Hanken_Grotesk, IBM_Plex_Sans_Arabic } from "next/font/google";
import { Toaster } from "@/components/ui/toaster";
import { LocaleProvider } from "@/lib/i18n/provider";
import { getServerLocale } from "@/lib/i18n/server";
import { dirFor } from "@/lib/i18n/config";
import "./globals.css";

const display = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
  variable: "--font-display",
  display: "swap",
});

const sans = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

// Hanken Grotesk has no Arabic coverage, so Arabic text would fall back to
// whatever the OS supplies and look nothing like the rest of the interface.
const arabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-arabic",
  display: "swap",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Basar",
  description: "A brand studio for platform-ready images",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = getServerLocale();
  const dir = dirFor(locale);

  return (
    <html
      lang={locale}
      dir={dir}
      className={`${display.variable} ${sans.variable} ${arabic.variable} ${geistMono.variable}`}
    >
      <body className="font-sans antialiased">
        <LocaleProvider locale={locale}>
          {children}
          <Toaster />
        </LocaleProvider>
      </body>
    </html>
  );
}
