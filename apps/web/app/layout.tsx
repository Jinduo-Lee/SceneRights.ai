import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SceneRights AI — Production Control Room",
  description: "Agentic Cinema Hackathon: ClickHouse Track",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background-primary text-text-primary antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}

