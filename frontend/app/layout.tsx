// FILE: frontend/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ReplyFlow — AI-Powered Customer Operations",
  description: "Autonomous, verified customer operations agent for modern businesses.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark bg-slate-950">
      <body className={`${inter.className} bg-slate-950 text-slate-100 antialiased flex h-screen overflow-hidden`}>
        <Sidebar />
        <main className="flex-1 flex flex-col overflow-y-auto bg-slate-950">
          {children}
        </main>
      </body>
    </html>
  );
}