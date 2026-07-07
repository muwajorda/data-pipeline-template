import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/Navbar'

export const metadata: Metadata = {
  title: 'Bioinformatics Project Generator',
  description: 'AI-powered tool to generate starter bioinformatics projects',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-white text-gray-900">
        <Navbar />
        <main className="min-h-screen">{children}</main>
      </body>
    </html>
  )
}
