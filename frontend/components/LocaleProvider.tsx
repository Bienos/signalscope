'use client';
import {createContext,useContext,useEffect,useState} from 'react';
import {locales,messagesFor,Messages,selectableLocales} from '../lib/i18n';

type LocaleContextValue={locale:string;messages:Messages;setLocale:(locale:string)=>void};
const LocaleContext=createContext<LocaleContextValue|null>(null);

export function LocaleProvider({children}:{children:React.ReactNode}){const [locale,setLocaleState]=useState('en');useEffect(()=>{const saved=localStorage.getItem('signalscope-locale');if(saved&&selectableLocales.some(item=>item.code===saved))setTimeout(()=>setLocaleState(saved),0)},[]);useEffect(()=>{document.documentElement.lang=locale},[locale]);const setLocale=(next:string)=>{if(!selectableLocales.some(item=>item.code===next))return;setLocaleState(next);localStorage.setItem('signalscope-locale',next);document.documentElement.lang=next};return <LocaleContext.Provider value={{locale,messages:messagesFor(locale),setLocale}}>{children}</LocaleContext.Provider>}
export function useLocale(){const value=useContext(LocaleContext);if(!value)throw new Error('LocaleProvider missing');return value}

export function LanguageSelector({compact=false}:{compact?:boolean}){const {locale,messages,setLocale}=useLocale();const complete=locales.filter(item=>item.status==='complete');const beta=locales.filter(item=>item.status==='beta');const planned=locales.filter(item=>item.status==='planned');return <label className={`languagepicker ${compact?'compact':''}`}><span>{messages.language}</span><select aria-label={messages.language} value={locale} onChange={event=>setLocale(event.target.value)}><optgroup label={messages.available}>{complete.map(item=><option value={item.code} key={item.code}>{item.nativeName}</option>)}</optgroup><optgroup label={messages.beta}>{beta.map(item=><option value={item.code} key={item.code}>{item.nativeName} · Beta</option>)}</optgroup><optgroup label={messages.planned}>{planned.map(item=><option disabled value={item.code} key={item.code}>{item.nativeName} · {messages.comingSoon}</option>)}</optgroup></select></label>}

export function LocaleStatusNotice(){const {locale,messages}=useLocale();if(locale==='en')return null;return <div className="localenotice" role="status"><b>{messages.betaNotice}</b><span>{messages.englishReference}</span></div>}
