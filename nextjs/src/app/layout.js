import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Providers from './providers'
// import { getLocale, getMessages } from 'next-intl/server';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Bitcoin LN Statistics",
  description: "Bitcoin LN Statistics",
};

export default async function RootLayout({ children }) {
  const excludedPaths = ['/login'];

  const messages = "";//await getMessages();
  const locale = "";//await getLocale();
  
  return (
    <html lang="lt" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`} suppressHydrationWarning>
        <Providers messages={messages} locale={locale} excludedPaths={excludedPaths}>
          {children}
        </Providers>
      </body>
    </html>
  )
}