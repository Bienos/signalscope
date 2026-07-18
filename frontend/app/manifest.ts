import type {MetadataRoute} from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'SignalScope',
    short_name: 'SignalScope',
    description: 'Evidence-led short-form social trend decision intelligence for agencies, brands, retailers and creative teams.',
    start_url: '/dashboard',
    display: 'standalone',
    background_color: '#F7F8FA',
    theme_color: '#0B1220',
    icons: [
      {
        src: '/brand/signalscope-mark-teal.png',
        sizes: '150x150',
        type: 'image/png',
        purpose: 'any',
      },
    ],
  };
}
