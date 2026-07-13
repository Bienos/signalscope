import {LandingPage} from '../components/LandingPage';
import {JsonLd} from '../components/JsonLd';import {homeSchema} from '../lib/structured-data';
export const metadata={title:'TikTok toy trend intelligence for brands, retailers and agencies',description:'Evaluate toy-market momentum with repeated observations, creator spread, confidence, freshness, safety and clear Act, Monitor or Avoid decisions.',alternates:{canonical:'/'},openGraph:{title:'SignalScope toy trend intelligence',description:'Understand what is moving in toys, why it matters and what to test next.',url:'/',type:'website'}};
export default function Page(){return <><JsonLd data={homeSchema()}/><LandingPage/></>}
