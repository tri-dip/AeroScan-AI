import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Sentry Gate | Document Screening",
  description: "AI-based fake identity and document screening system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <div className="flex h-screen w-full overflow-hidden bg-slate-50">
          <Sidebar />
          <main className="flex h-screen flex-1 flex-col overflow-y-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
