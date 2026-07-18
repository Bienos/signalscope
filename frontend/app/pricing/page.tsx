import PricingPage from '../../components/PricingPage';
import {JsonLd} from '../../components/JsonLd';
import {pricingSchema} from '../../lib/structured-data';

export const metadata = {
  title: 'Pricing',
  description: 'Compare indicative SignalScope plans for category watchlists, research depth and team workflows.',
  alternates: {canonical: '/pricing'},
  openGraph: {
    title: 'SignalScope pricing',
    description: 'Plans for evidence-led trend research, from one category watchlist to custom enterprise requirements.',
    url: '/pricing',
    type: 'website' as const,
    images: [{url: '/brand/signalscope-wordmark-on-light.png', width: 520, height: 150, alt: 'SignalScope'}],
  },
};

export default function Page() {
  return <><JsonLd data={pricingSchema()}/><PricingPage/></>;
}
