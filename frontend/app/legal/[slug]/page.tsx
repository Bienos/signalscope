import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {LegalPage} from '../../../components/LegalPage';
import {JsonLd} from '../../../components/JsonLd';
import {policies,policyBySlug} from '../../../lib/legal';
import {legalSchema} from '../../../lib/structured-data';
export function generateStaticParams(){return policies.map(policy=>({slug:policy.slug}))}
export async function generateMetadata({params}:{params:Promise<{slug:string}>}):Promise<Metadata>{const {slug}=await params;const policy=policyBySlug[slug];return policy?{title:policy.title,description:policy.summary,alternates:{canonical:`/legal/${slug}`}}:{title:'Legal document not found'}}
export default async function Page({params}:{params:Promise<{slug:string}>}){const {slug}=await params;const policy=policyBySlug[slug];if(!policy)notFound();return <><JsonLd data={legalSchema(policy.title,policy.summary,`/legal/${slug}`)}/><LegalPage policy={policy}/></>}
