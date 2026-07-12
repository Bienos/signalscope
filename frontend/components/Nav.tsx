'use client';
import Link from 'next/link';
import {useState} from 'react';
import {usePathname} from 'next/navigation';
import {getPlan} from '../lib/commercial';
import {dashboardNavFor} from '../lib/i18n';
import {useCommercial} from './CommercialProvider';
import {useLocale} from './LocaleProvider';
export function Nav(){
 const path=usePathname();const [open,setOpen]=useState(false);const {plan}=useCommercial();const {locale}=useLocale();const text=dashboardNavFor(locale);const p=getPlan(plan);
 const groups=[[text.daily,[['/dashboard',text.today],['/discover',text.discover],['/reports',text.reports]]],[text.research,[['/creators',text.creators],['/watchlists',text.watchlists],['/sounds',text.sounds],['/hashtags',text.hashtags]]],[text.decide,[['/ideas',text.ideas],['/review-queue',text.reviewQueue]]],[text.review,[['/data-health',text.dataHealth],['/settings',text.settings],['/pricing',text.plans]]]] as const;
 return <aside className={`nav ${open?'mobileopen':''}`}><div className="navbrandrow"><Link href="/" className="brand" aria-label="SignalScope home"><span className="signalmark" aria-hidden="true"><i/><i/><i/></span>SignalScope<small>Short-form trend intelligence</small></Link><button className="navtoggle" aria-expanded={open} aria-controls="dashboard-navigation" onClick={()=>setOpen(value=>!value)}><span aria-hidden="true">{open?'×':'☰'}</span><b>{open?'Close':'Menu'}</b></button></div><div className="demo-nav">INTERNAL DEMO · MOCKPROVIDER</div><nav id="dashboard-navigation" aria-label="Dashboard navigation">{groups.map(([name,links])=><section className="navgroup" key={name}><h2>{name}</h2>{links.map(([href,label])=><Link aria-current={path===href||path.startsWith(`${href}/`)?'page':undefined} key={href} href={href}>{label}{href==='/review-queue'&&<b className="navcount">2</b>}</Link>)}</section>)}</nav><footer className="navfooter"><span><i/> {text.demo}</span><b>{text.source}</b><small>{p.quotas.markets==null?'Custom':p.quotas.markets} market entitlement · {p.name}</small><Link className="siteback" href="/">← {text.site}</Link></footer></aside>
}
