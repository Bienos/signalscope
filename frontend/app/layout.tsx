import type {Metadata} from 'next';
import './globals.css';
import './signalscope.css';
import './pricing.css';
import './commercial.css';
import './creator-theme.css';
import './legal.css';
import './ux-improvements.css';
import './toy-platform.css';
import {AppFrame} from '../components/AppFrame';

const brandImage = {
  url: '/brand/signalscope-wordmark-on-light.png',
  width: 520,
  height: 150,
  alt: 'SignalScope',
};

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  title: {default: 'SignalScope', template: '%s · SignalScope'},
  description: 'Evidence-led short-form social trend intelligence for agencies, brands, retailers and creative teams.',
  applicationName: 'SignalScope',
  manifest: '/manifest.webmanifest',
  icons: {
    icon: [{url: '/brand/signalscope-mark-teal.png', type: 'image/png', sizes: '150x150'}],
    apple: [{url: '/brand/signalscope-mark-teal.png', type: 'image/png', sizes: '150x150'}],
  },
  openGraph: {
    title: 'SignalScope trend decision intelligence',
    description: 'See what is gaining momentum, inspect the evidence and decide what to do next.',
    siteName: 'SignalScope',
    type: 'website',
    images: [brandImage],
  },
  twitter: {
    card: 'summary',
    title: 'SignalScope trend decision intelligence',
    description: 'See what is gaining momentum, inspect the evidence and decide what to do next.',
    images: ['/brand/signalscope-wordmark-on-light.png'],
  },
};

export default function Layout({children}: {children: React.ReactNode}) {
  return <html lang="en"><body><AppFrame>{children}</AppFrame></body></html>;
}
