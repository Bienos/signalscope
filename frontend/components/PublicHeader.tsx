'use client';

import Link from 'next/link';
import {BrandLogo} from './BrandLogo';
import {LanguageSelector} from './LocaleProvider';

export function PublicHeader() {
  return <header className="publicheader">
    <Link href="/" className="publicheaderbrand" aria-label="SignalScope home">
      <BrandLogo variant="on-light" priority sizes="(max-width: 700px) 165px, 190px"/>
    </Link>
    <nav className="publicheadernav" aria-label="Public navigation">
      <Link href="/">Product</Link>
      <Link href="/pricing">Pricing</Link>
      <Link href="/legal">Trust</Link>
    </nav>
    <div className="publicheaderactions">
      <LanguageSelector compact/>
      <Link href="/dashboard" className="publicdashboardlink">Open dashboard</Link>
    </div>
  </header>;
}
