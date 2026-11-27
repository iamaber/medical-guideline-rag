import type { Metadata } from "next";
import { Geist, Source_Serif_4 } from "next/font/google";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const sourceSerif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Medical Guideline RAG",
  description:
    "Medication advice for a patient's medications, schedules and conditions, with the PubMed articles and MedEx monographs it cited.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${sourceSerif.variable} flex min-h-screen flex-col font-sans antialiased`}
      >
        <SiteHeader />
        <main className="flex-1">{children}</main>
        <footer className="border-t">
          <div className="mx-auto flex max-w-6xl flex-wrap justify-between gap-x-8 gap-y-2 px-6 py-6 text-sm text-muted-foreground">
            <p>For education only. This is not medical advice.</p>
            <p>
              Evidence from PubMed and WHO guidelines. Drug data from MedEx.{" "}
              <a
                href="https://github.com/iamaber/medical-guideline-rag"
                className="underline underline-offset-2 hover:text-foreground"
              >
                Source code
              </a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
