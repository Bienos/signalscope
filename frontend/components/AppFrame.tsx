'use client';
import {usePathname} from 'next/navigation';
import {Nav} from './Nav';
import {GlobalBar} from './GlobalBar';
import {CommercialProvider} from './CommercialProvider';
import {PublicHeader} from './PublicHeader';
import {CompactLegalFooter,SiteFooter} from './SiteFooter';
import {LocaleProvider,LocaleStatusNotice} from './LocaleProvider';
export function AppFrame({children}:{children:React.ReactNode}){const path=usePathname();const publicRoute=path==='/'||path==='/pricing'||path==='/login'||path.startsWith('/legal');return <LocaleProvider><CommercialProvider>{publicRoute?<>{path!=='/'&&<PublicHeader/>}<LocaleStatusNotice/>{children}<SiteFooter/></>:<div className="shell"><Nav/><div className="workspace"><GlobalBar/><main className="main" id="main-content"><LocaleStatusNotice/>{children}</main><CompactLegalFooter/></div></div>}</CommercialProvider></LocaleProvider>}
