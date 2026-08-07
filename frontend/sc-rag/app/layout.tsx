import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SCRAG AI | Secure Cloud Retrieval Augmented Generation",
  description: "Secure AI assistant for cloud documents"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  );
}
