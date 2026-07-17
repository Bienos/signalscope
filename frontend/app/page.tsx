import {LandingPage} from '../components/LandingPage';
import {JsonLd} from '../components/JsonLd';
import {homeSchema} from '../lib/structured-data';

export const metadata = {
  title: 'Short-form social trend intelligence for agencies and brand teams',
  description: 'Turn fragmented short-form social observations into evidence-backed Act, Monitor or Avoid decisions, original opportunities and stakeholder-ready reports.',
  alternates: {canonical: '/'},
  openGraph: {
    title: 'SignalScope trend decision intelligence',
    description: 'Understand what is gaining momentum, why it matters and what your team should do next.',
    url: '/',
    type: 'website' as const,
    images: [{url: '/brand/signalscope-wordmark-on-light.png', width: 520, height: 150, alt: 'SignalScope'}],
  },
};

export default function Page() {
  return <><JsonLd data={homeSchema()}/><LandingPage/></>;
}
