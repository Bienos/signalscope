import {LandingPage} from '../components/LandingPage';
import {JsonLd} from '../components/JsonLd';import {homeSchema} from '../lib/structured-data';
export const metadata={title:'Social trend intelligence for professional teams',description:'Evaluate emerging social signals with velocity, acceleration, confidence and freshness. Built for agencies, brands, insights, influencer and commerce teams.',alternates:{canonical:'/'},openGraph:{title:'SignalScope social trend intelligence',description:'Understand what is accelerating, why it matters and where to act next.',url:'/',type:'website'}};
export default function Page(){return <><JsonLd data={homeSchema()}/><LandingPage/></>}
