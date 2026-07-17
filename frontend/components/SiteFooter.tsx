'use client';
import Link from 'next/link';
import {EFFECTIVE_DATE} from '../lib/legal';
import type {Messages} from '../lib/i18n';
import {BrandLogo} from './BrandLogo';
import {LanguageSelector,useLocale} from './LocaleProvider';

const groups:Array<{title:keyof Messages;links:Array<{label:keyof Messages;href:string}>}>=[
 {title:'product',links:[{label:'overview',href:'/'},{label:'dashboard',href:'/dashboard'},{label:'pricing',href:'/pricing'}]},
 {title:'company',links:[{label:'about',href:'/#problem'},{label:'contact',href:'/legal/contact'}]},
 {title:'trust',links:[{label:'methodology',href:'/legal/methodology'},{label:'ai',href:'/legal/ai-disclosure'},{label:'security',href:'/legal/security'},{label:'responsible',href:'/legal/security'},{label:'accessibility',href:'/legal/accessibility'}]},
 {title:'legal',links:[{label:'terms',href:'/legal/terms'},{label:'privacy',href:'/legal/privacy'},{label:'cookies',href:'/legal/cookies'},{label:'acceptable',href:'/legal/acceptable-use'},{label:'copyright',href:'/legal/copyright'},{label:'billing',href:'/legal/billing'}]},
];

const socials=[
 {name:'X',url:'[X PROFILE URL — REQUIRED BEFORE PUBLICATION]',icon:'x'},
 {name:'LinkedIn',url:'[LINKEDIN PROFILE URL — REQUIRED BEFORE PUBLICATION]',icon:'linkedin'},
 {name:'Telegram',url:'https://t.me/signalsscope',icon:'telegram'},
] as const;

function SocialIcon({name}:{name:string}){if(name==='linkedin')return <svg aria-hidden="true" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 10v7M8 7v.2M12 17v-4a3 3 0 0 1 6 0v4M12 10v7"/></svg>;if(name==='telegram')return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M3 11.5 20.5 4 17 20l-5-4-3 2 .5-4.5L17 7 7.5 12.5z"/></svg>;return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 4l14 16M19 4 5 20"/></svg>}

function SocialLinks(){const {messages}=useLocale();return <section className="socialgroup"><h2>{messages.follow}</h2>{socials.map(item=>item.url.startsWith('https://')?<a key={item.name} className="sociallink" href={item.url} target="_blank" rel="noopener noreferrer" aria-label={`${messages.follow}: ${item.name}`}><SocialIcon name={item.icon}/><span>{item.name}</span><b aria-hidden="true">↗</b></a>:<span key={item.name} className="sociallink socialdisabled" aria-disabled="true" title={item.url}><SocialIcon name={item.icon}/><span>{item.name}</span><small>{messages.comingSoon}</small></span>)}</section>}

export function SiteFooter(){const {messages}=useLocale();return <footer className="sitefooter"><div className="footerbrand"><Link href="/" className="footerlogo" aria-label="SignalScope home"><BrandLogo variant="on-dark" sizes="210px"/></Link><p>Short-form social trend decision intelligence for agencies, brands, retailers and creative teams.</p><LanguageSelector/><div className="footertrust"><b>{messages.independent}</b><span>{messages.coverage}</span><span>CURRENT DEMO: TOYS · Synthetic provider fixtures</span></div></div><div className="footerlinks">{groups.map(group=><section key={group.title}><h2>{messages[group.title]}</h2>{group.links.map(item=><Link key={item.label} href={item.href}>{messages[item.label]}</Link>)}</section>)}<SocialLinks/></div><div className="footerbase"><span>© 2026 [COMPANY LEGAL NAME — REQUIRED BEFORE PUBLICATION]</span><span>{messages.draft} {EFFECTIVE_DATE}</span><Link href="/legal">{messages.legalOverview}</Link><span>{messages.noTracking}</span></div></footer>}

export function CompactLegalFooter(){return <footer className="compactlegal"><span>DEMO TOY DATA · configured sample, not exhaustive</span><nav aria-label="Legal links"><Link href="/legal/terms">Terms</Link><Link href="/legal/privacy">Privacy</Link><Link href="/workspace?tab=methodology">Methodology</Link><Link href="/legal/security">Security</Link></nav></footer>}
