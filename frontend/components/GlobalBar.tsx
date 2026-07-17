'use client';

import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {LanguageSelector} from './LocaleProvider';
import {PlanPreview} from './PlanPreview';

export function GlobalBar() {
  const path = usePathname();
  const section = path.split('/').filter(Boolean)[0] || 'today';
  return <header className="globalbar">
    <Link href="#main-content" className="skip">Skip to content</Link>
    <div className="crumb">Toy intelligence <b>/ {section}</b></div>
    <div className="globalfilters">
      <Link href="/discover" className="globalsearch" aria-label="Search toy signals">⌕ Search toy signals <kbd>/</kbd></Link>
      <span className="filterchip">GB · PL</span>
      <span className="globalfresh">MODE SHOWN BELOW</span>
      <Link href="/login" className="filterchip">Sign in</Link>
      <LanguageSelector compact/>
      <PlanPreview/>
    </div>
  </header>;
}
