import {plans} from './commercial';
import {pricingFaqs,publicFaqs} from './seo-content';

type JsonLd=Record<string,unknown>;
const configured=process.env.NEXT_PUBLIC_SITE_URL;
export function siteUrl(){
 if(!configured)return null;
 try{const url=new URL(configured);if(url.hostname==='localhost'||url.hostname==='127.0.0.1'||url.protocol!=='https:')return null;return url.origin}catch{return null}
}
export const absoluteUrl=(path='/')=>{const root=siteUrl();return root?new URL(path,`${root}/`).toString():null};

const audience={
 '@type':'Audience',
 audienceType:'Social and influencer agencies, multi-brand consumer companies, retail and social-commerce companies, gaming, entertainment, media, beauty, fashion and lifestyle brands'
};
function offers(root:string){return plans.map(plan=>({
 '@type':'Offer',
 '@id':`${root}/pricing#offer-${plan.id}`,
 name:plan.name,
 url:`${root}/pricing#${plan.id}`,
 priceCurrency:'EUR',
 ...(plan.monthly===null?{description:`Custom pricing · ${plan.limits.monitors}`}:{price:String(plan.monthly),description:`Indicative launch pricing · ${plan.limits.monitors}`}),
 category:'SaaS subscription concept'
}))}
export function homeSchema():JsonLd|null{
 const root=siteUrl();if(!root)return null;
 const offerItems=offers(root);
 return {'@context':'https://schema.org','@graph':[
  {'@type':'Organization','@id':`${root}/#organization`,name:'SignalScope',url:`${root}/`,description:'Independent provider of evidence-led short-form social trend intelligence for professional teams.',sameAs:['https://t.me/signalsscope']},
  {'@type':'WebSite','@id':`${root}/#website`,url:`${root}/`,name:'SignalScope',description:'Evidence-led trend intelligence for teams that need to understand what is accelerating, why it matters and where to act next.',publisher:{'@id':`${root}/#organization`},inLanguage:['en','pl','es','fr']},
  {'@type':'OfferCatalog','@id':`${root}/pricing#catalog`,name:'SignalScope indicative launch plans',itemListElement:offerItems},
  {'@type':'SoftwareApplication','@id':`${root}/#software`,name:'SignalScope',url:`${root}/`,applicationCategory:'BusinessApplication',applicationSubCategory:'Social trend intelligence and creative research',operatingSystem:'Web browser',description:'An evidence-led trend intelligence workspace for professional social, creative, insights, influencer and commerce teams. The current public demonstration uses simulated provider data.',audience,featureList:['Category watchlists','Trend velocity and acceleration analysis','Creator context','Confidence and data-freshness indicators','Act, Monitor and Avoid decisions','Decision-ready reporting'],offers:offerItems,publisher:{'@id':`${root}/#organization`}},
  {'@type':'Product','@id':`${root}/#product`,name:'SignalScope',url:`${root}/`,description:'A focused alternative to fragmented manual social trend research, combining momentum analysis with confidence, freshness and responsible creative guidance.',audience,isRelatedTo:{'@id':`${root}/#software`},offers:offerItems,brand:{'@id':`${root}/#organization`}},
  {'@type':'WebPage','@id':`${root}/#webpage`,url:`${root}/`,name:'SignalScope — evidence-led social trend intelligence',isPartOf:{'@id':`${root}/#website`},about:{'@id':`${root}/#product`},description:'Trend intelligence for agencies, brands, insights teams, influencer teams and social-commerce leaders.'},
  faqSchema(publicFaqs,`${root}/#faq`)
 ]};
}
function faqSchema(faqs:ReadonlyArray<{question:string;answer:string}>,id:string):JsonLd{return {'@type':'FAQPage','@id':id,mainEntity:faqs.map(item=>({'@type':'Question',name:item.question,acceptedAnswer:{'@type':'Answer',text:item.answer}}))}}
export function pricingSchema():JsonLd|null{const root=siteUrl();if(!root)return null;return {'@context':'https://schema.org','@graph':[
 {'@type':'WebPage','@id':`${root}/pricing#webpage`,url:`${root}/pricing`,name:'SignalScope pricing',description:'Indicative plans for category watchlists, research depth and team workflows.',isPartOf:{'@id':`${root}/#website`},breadcrumb:{'@id':`${root}/pricing#breadcrumb`}},
 {'@type':'BreadcrumbList','@id':`${root}/pricing#breadcrumb`,itemListElement:[{'@type':'ListItem',position:1,name:'Home',item:`${root}/`},{'@type':'ListItem',position:2,name:'Pricing',item:`${root}/pricing`}]},
 {'@type':'OfferCatalog','@id':`${root}/pricing#catalog`,name:'SignalScope indicative launch plans',itemListElement:offers(root)},faqSchema(pricingFaqs,`${root}/pricing#faq`)
]}}
export function legalSchema(title:string,description:string,path:string,type:'CollectionPage'|'WebPage'='WebPage'):JsonLd|null{const root=siteUrl();if(!root)return null;const url=`${root}${path}`;return {'@context':'https://schema.org','@graph':[
 {'@type':type,'@id':`${url}#webpage`,url,name:title,description,isPartOf:{'@id':`${root}/#website`},breadcrumb:{'@id':`${url}#breadcrumb`}},
 {'@type':'BreadcrumbList','@id':`${url}#breadcrumb`,itemListElement:[{'@type':'ListItem',position:1,name:'Home',item:`${root}/`},{'@type':'ListItem',position:2,name:path==='/legal'?'Legal and trust centre':'Legal',item:`${root}/legal`},...(path==='/legal'?[]:[{'@type':'ListItem',position:3,name:title,item:url}])]}
]}}
