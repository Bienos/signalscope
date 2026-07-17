import {LandingPage} from '../components/LandingPage';
import {JsonLd} from '../components/JsonLd';
import {homeSchema} from '../lib/structured-data';
import type {Metadata} from 'next';

export const metadata: Metadata = {
  title: 'Short-form trend intelligence for agencies and consumer teams',
  description: 'Detect emerging short-form momentum, understand the evidence and turn the strongest opportunities into watchlists, creative briefs and client-ready reports.',
  alternates: {canonical: '/'},
  openGraph: {
    title: 'Short-form trend intelligence for agencies and consumer teams',
    description: 'Detect emerging short-form momentum, understand the evidence and turn the strongest opportunities into watchlists, creative briefs and client-ready reports.',
    url: '/',
    type: 'website' as const,
    images: [{url: '/brand/signalscope-wordmark-on-light.png', width: 520, height: 150, alt: 'SignalScope'}],
  },
  twitter: {
    card: 'summary',
    title: 'Short-form trend intelligence for agencies and consumer teams',
    description: 'Turn emerging short-form signals into client-ready decisions with evidence, freshness and confidence attached.',
    images: ['/brand/signalscope-wordmark-on-light.png'],
  },
};

export default function Page() {
  return <><JsonLd data={homeSchema()}/><LandingPage/></>;
}
