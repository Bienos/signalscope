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
 audienceType:'Social and influencer agencies, multi-brand consumer companies, retail and social-commerce teams, gaming and entertainment companies, and beauty, fashion and lifestyle brands'
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
  {'@type':'Organization','@id':`${root}/#organization`,name:'SignalScope',url:`${root}/`,description:'Independent provider of evidence-led short-form social trend decision intelligence for professional teams.',logo:{'@type':'ImageObject','@id':`${root}/#logo`,url:`${root}/brand/signalscope-mark-teal.png`,contentUrl:`${root}/brand/signalscope-mark-teal.png`,width:150,height:150,caption:'SignalScope'},sameAs:['https://t.me/signalsscope']},
  {'@type':'WebSite','@id':`${root}/#website`,url:`${root}/`,name:'SignalScope',description:'Trend decision intelligence for teams that need to understand what is gaining momentum, why it matters and what to do next.',publisher:{'@id':`${root}/#organization`},inLanguage:['en','pl','es','fr']},
  {'@type':'OfferCatalog','@id':`${root}/pricing#catalog`,name:'SignalScope indicative launch plans',itemListElement:offerItems},
  {'@type':'SoftwareApplication','@id':`${root}/#software`,name:'SignalScope',url:`${root}/`,applicationCategory:'BusinessApplication',applicationSubCategory:'Short-form social trend intelligence and creative research',operatingSystem:'Web browser',description:'An evidence-led trend decision workspace for agencies, brands, retailers and creative teams. The current working demonstration is limited to toys and uses synthetic provider fixtures.',audience,featureList:['Category watchlists','Repeated metric observations','Velocity and acceleration analysis','Creator, hashtag and sound context','Confidence, freshness and safety indicators','Act, Monitor and Avoid decisions','Source-linked creative briefs','Decision-ready reporting'],offers:offerItems,publisher:{'@id':`${root}/#organization`}},
  {'@type':'Product','@id':`${root}/#product`,name:'SignalScope',url:`${root}/`,description:'A focused alternative to fragmented manual short-form social research, combining momentum evidence with confidence, freshness, safety and responsible creative guidance. The current demonstration supports toys only.',image:{'@id':`${root}/#logo`},audience,isRelatedTo:{'@id':`${root}/#software`},offers:offerItems,brand:{'@id':`${root}/#organization`}},
  {'@type':'WebPage','@id':`${root}/#webpage`,url:`${root}/`,name:'SignalScope — evidence-led trend decision intelligence',isPartOf:{'@id':`${root}/#website`},about:{'@id':`${root}/#product`},description:'Short-form social trend decision intelligence for agencies, consumer brands, retailers and creative teams.'},
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
