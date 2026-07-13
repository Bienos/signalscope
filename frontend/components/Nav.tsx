'use client';

import Image from 'next/image';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {useState} from 'react';

const links = [
  ['/dashboard', 'Today', 'Daily toy trend brief'],
  ['/discover', 'Discover', 'Search and evaluate toy signals'],
  ['/track', 'Track', 'Watchlists and research entities'],
  ['/opportunities', 'Opportunities', 'Act, monitor, avoid and brief'],
  ['/reports', 'Reports', 'Decision-led exports'],
  ['/workspace', 'Workspace', 'Data health and methodology'],
] as const;

export function Nav() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  return <aside className={`nav ${open ? 'mobileopen' : ''}`}>
    <div className="navbrandrow">
      <Link href="/" className="brand" aria-label="SignalScope home">
        <Image src="/brand/signalscope-horizontal-dark.png" width={208} height={60} alt="SignalScope" priority/>
      </Link>
      <button className="navtoggle" aria-expanded={open} aria-controls="dashboard-navigation" onClick={() => setOpen((value) => !value)}><span aria-hidden="true">{open ? '×' : '☰'}</span><b>{open ? 'Close' : 'Menu'}</b></button>
    </div>
    <div className="demo-nav">TOY MARKET INTELLIGENCE</div>
    <nav id="dashboard-navigation" aria-label="Primary product navigation">
      {links.map(([href, label, description]) => <Link aria-current={path === href || path.startsWith(`${href}/`) ? 'page' : undefined} key={href} href={href} onClick={() => setOpen(false)}><b>{label}</b><small>{description}</small></Link>)}
    </nav>
    <footer className="navfooter"><span><i/> Source state shown on each page</span><b>Toy intelligence · GB + PL</b><small>Coverage is a configured monitored sample.</small><Link className="siteback" href="/">← Product site</Link></footer>
  </aside>;
}
